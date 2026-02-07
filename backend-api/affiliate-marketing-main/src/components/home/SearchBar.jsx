import React, { useState, useEffect, useRef, useCallback } from "react";
import { apiEndpoints } from "../../services/api";
import { ClipLoader } from "react-spinners";
import ProductSearchCard from "./ProductSearchCard";

const SearchBar = () => {
  const [localQuery, setLocalQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [category, setCategory] = useState("");
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);

  const searchCache = useRef(new Map()); // memoization cache
  const wrapperRef = useRef(null); // for click outside

  // Fetch categories on mount
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await apiEndpoints.getCategories();
        setCategories(response.data.categories || []);
      } catch (error) {
        console.error("Error fetching categories:", error);
      }
    };
    loadCategories();
  }, []);

  // Fetch products with memoization
  const fetchProducts = useCallback(
    async (query) => {
      const cacheKey = `${category || "all"}-${query}`;

      // ✅ Return cached results if available
      if (searchCache.current.has(cacheKey)) {
        setProducts(searchCache.current.get(cacheKey));
        setShowDropdown(true);
        return;
      }

      try {
        setLoading(true);
        const params = {
          category: category || undefined,
          query: query || undefined,
          page: 1,
          limit: 12,
          sort_by: "-1",
        };

        const response = await apiEndpoints.searchProducts(params);
        const results = response.data?.products || [];
        setProducts(results);
        setShowDropdown(true);

        // ✅ Cache results
        searchCache.current.set(cacheKey, results);
      } catch (error) {
        console.error("Error fetching products:", error);
        setProducts([]);
      } finally {
        setLoading(false);
      }
    },
    [category]
  );

  const handleSearch = () => {
    if (localQuery.trim()) {
      fetchProducts(localQuery.trim());
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  // Hide dropdown when input cleared
  useEffect(() => {
    if (!localQuery.trim()) {
      setShowDropdown(false);
    }
  }, [localQuery]);

  // ✅ Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div
      ref={wrapperRef}
      className="relative w-full max-w-4xl flex flex-col sm:flex-row sm:items-center border border-gray-300 rounded-lg shadow-sm p-2"
    >
      {/* Category Select */}
      <select
        name="categories"
        value={category}
        onChange={(e) => setCategory(e.target.value)}
        className="bg-white text-sm md:text-base px-4 py-3 text-black w-full sm:w-42 border-b sm:border-b-0 sm:border-r border-gray-300 focus:outline-none mb-2 sm:mb-0"
      >
        <option value="">All Categories</option>
        {categories.map((cat) => (
          <option key={cat} value={cat}>
            {cat}
          </option>
        ))}
      </select>

      {/* Input + Button */}
      <div className="flex flex-col sm:flex-row sm:flex-grow w-full sm:w-auto gap-2 sm:gap-0 relative">
        <input
          type="text"
          value={localQuery}
          onChange={(e) => setLocalQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Search for a product"
          className="px-4 py-3 text-sm md:text-base text-gray-600 placeholder-gray-400 focus:outline-none w-full border border-gray-300 sm:border-0 sm:border-r sm:flex-grow rounded sm:rounded-none"
        />

        <button
          onClick={handleSearch}
          disabled={loading}
          className="bg-black text-lime-300 font-semibold px-6 py-3 text-sm md:text-base hover:bg-gray-900 transition rounded sm:rounded-none sm:rounded-r w-full sm:w-auto flex items-center justify-center"
        >
          {loading && <ClipLoader color="#A3E635" size={20} />}
         Search
        </button>
      </div>

      {/* Dropdown of products */}
      {showDropdown && (
        <ul className="absolute top-full left-0 mt-2 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto z-50">
          {loading ? (
            <li className="flex justify-center py-4">
              <ClipLoader color="#000" size={25} />
            </li>
          ) : products.length > 0 ? (
            products.map((p, idx) => (
              <ProductSearchCard product={p} key={idx} />
            ))
          ) : (
            <li className="px-4 py-2 text-sm text-gray-500">
              No products found
            </li>
          )}
        </ul>
      )}
    </div>
  );
};

export default SearchBar;
