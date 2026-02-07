import React, { useState } from "react";
import { ClipLoader } from "react-spinners";
import axios from "axios";
import ProductCompareShowCard from "./CompareProductShowCard";

const CATEGORY_MAP = {
  SmartPhone: "smartphone",
  Laptop: "laptop",
  Accessories: "accessories",
};

const CompareModal = ({ activeTab, onClose, onSelect }) => {
  const [query, setQuery] = useState("");
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const category = activeTab; // Use directly
      const { data } = await axios.get("/productlisting", {
        params: { category, query, page: 1, limit: 12 },
      });
      setProducts(data?.products || []);
    } catch (err) {
      console.error("Error fetching products:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl p-6 relative overflow-hidden">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-gray-500 hover:text-black text-lg sm:text-xl"
        >
          ✕
        </button>

        {/* Search */}
        <div className="flex flex-col sm:flex-row gap-2 mb-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search product..."
            className="flex-grow px-3 py-2 border border-gray-300 rounded-md text-sm w-full"
          />
          <button
            onClick={fetchProducts}
            className="bg-black text-white px-4 py-2 rounded w-full sm:w-auto"
          >
            Search
          </button>
        </div>

        {/* Results */}
        {loading ? (
          <div className="flex justify-center py-6">
            <ClipLoader size={25} />
          </div>
        ) : products.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
            {products.map((p) => (
              <ProductCompareShowCard
                key={p._id}
                product={p}
                onSelect={() => onSelect(p)}
              />
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center">No products found</p>
        )}
      </div>
    </div>
  );
};

export default CompareModal;
