import React, { useState, useEffect, useMemo } from "react";
import { FiChevronDown, FiChevronUp, FiRotateCw } from "react-icons/fi";
import PriceRangeSelector from "./PriceRangeSelector.jsx";
import FeaturedProductBaner from "./FeaturedProductsBaner.jsx";
import axios from "axios";
import { debounce } from "lodash";
import { BeatLoader } from "react-spinners"; // Import spinner

const categories = [
  "All",
  "Electronics Devices",
  "Computer & Laptop",
  "Laptop Accessories",
  "SmartPhone",
  "Headphone",
  "Mobile Accessories",
  "Gaming Console",
  "Camera & Photo",
  "TV & Homes Appliances",
  "Watches & Accessories",
  "GPS & Navigation",
  "Warable Technology",
];

const prices = [
  "All Price",
  "Under Rs. 20",
  "Rs. 25 to Rs. 100",
  "Rs. 100 to Rs. 300",
  "Rs. 300 to Rs. 500",
  "Rs. 500 to Rs. 1,000",
  "Rs. 1,000 to Rs. 10,000",
];

const brands = [
  "Apple",
  "Google",
  "Microsoft",
  "Samsung",
  "Dell",
  "HP",
  "Symphony",
  "Xiaomi",
  "Sony",
  "Panasonic",
  "LG",
  "Intel",
  "One Plus",
];

const features = {
  Display: [
    "6.1 inches",
    "6.2 inches",
    "6.3 inches",
    "6.4 inches",
    "6.5 inches",
    "6.6 inches",
  ],
  "Processor & Performance": [
    "Intel",
    "Silicon",
    "Apple M1",
    "Apple M2",
    "Apple M3",
    "Apple M4",
  ],
  Storage: ["128 SSD", "256 SSD", "512 SSD", "1 TB SSD"],
  Camera: ["50 MP", "200 MP", "200 + 200 MP", "50 + 50 MP"],
  Battery: ["2580 MAh", "4000 MAh", "5000 MAh", "8000 MAh"],
};

const defaultFilters = {
  category: "",
  price: "All Price",
  minPrice: 199,
  maxPrice: 199900,
  brands: [],
  features: {},
  rating: 0,
};

const FilterSection = ({ title, isOpen, toggleOpen, children }) => (
  <div className="mb-2 rounded-sm">
    <button
      onClick={toggleOpen}
      className="w-full bg-primary px-4 py-2 font-semibold uppercase text-sm text-black flex justify-between items-center cursor-pointer"
    >
      {title}
      {isOpen ? <FiChevronUp /> : <FiChevronDown />}
    </button>
    {isOpen && <div className="mt-4 px-2 space-y-2">{children}</div>}
  </div>
);

const SidebarFilters = ({ onFiltersChange }) => {
  const [filters, setFilters] = useState({});
  const [loadingFilters, setLoadingFilters] = useState(true);

  const [openSections, setOpenSections] = useState({
    category: false,
    price: false,
    brand: false,
    features: false,
  });

  useEffect(() => {
    const fetchDynamicFilters = async () => {
      setLoadingFilters(true);
      try {
        const [categoriesRes, brandsRes] = await Promise.all([
          apiEndpoints.getCategories(),
          apiEndpoints.getBrands()
        ]);
        
        setFilters({
          categories: ['All', ...(categoriesRes.data.categories || [])],
          brand: brandsRes.data.brands || [],
          pricerange: { min: 0, max: 200000 },
          specificfilters: {},
          features: {},
        });
      } catch (error) {
        console.error("Error fetching filters:", error);
        toast.error("Failed to load filters");
        // Fallback to basic structure
        setFilters({
          categories: ['All'],
          brand: [],
          pricerange: { min: 0, max: 200000 },
          specificfilters: {},
          features: {},
        });
      } finally {
        setLoadingFilters(false);
      }
    };
    
    fetchDynamicFilters();
  }, []);

  const [selectedFilters, setSelectedFilters] = useState(defaultFilters);

  const toggleSection = (section) => {
    setOpenSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const handleCategoryChange = (value) => {
    setSelectedFilters((prev) => ({ ...prev, category: value }));
  };

  const handleBrandToggle = (brand) => {
    setSelectedFilters((prev) => {
      const current = new Set(prev.brands);

      current.has(brand.toLowerCase())
        ? current.delete(brand.toLowerCase())
        : current.add(brand.toLowerCase());

      return { ...prev, brands: Array.from(current) };
    });
  };

  const handleFeatureToggle = (featureGroup, value) => {
    setSelectedFilters((prev) => {
      const group = new Set(prev.features[featureGroup] || []);
      group.has(value) ? group.delete(value) : group.add(value);
      return {
        ...prev,
        features: {
          ...prev.features,
          [featureGroup]: Array.from(group),
        },
      };
    });
  };

  const handlePriceChange = (selected) => {
    const priceMap = {
      "Under ₹5,000": [0, 5000],
      "₹5,000 to ₹10,000": [5000, 10000],
      "₹10,000 to ₹20,000": [10000, 20000],
      "₹20,000 to ₹50,000": [20000, 50000],
      "₹50,000 to ₹1,00,000": [50000, 100000],
      "Above ₹1,00,000": [100000, 500000],
    };
    
    const [min, max] = priceMap[selected] || [0, 500000];

    setSelectedFilters({
      ...selectedFilters,
      price: selected,
      minPrice: min,
      maxPrice: max,
    });
  };

  // Category Based Brands
  const categoryBasedBrands = useMemo(() => {
    // console.log(filters);
    // console.log(filters.specificfilters?.[selectedFilters.category]?.brand);
    return selectedFilters.category === ""
      ? filters.brand ?? []
      : filters.specificfilters?.[selectedFilters.category]?.brand ?? [];
  }, [selectedFilters.category, filters]);

  // Category based Features - fetch dynamically based on selected category
  const categoryBasedFeatures = useMemo(() => {
    // For now, return empty array as features will be product-specific
    // You can extend this to fetch category-specific attributes from the backend
    const specific = filters?.specificfilters?.[selectedFilters.category];
    if (!specific) return [];

    // Filter out 'brand' and return entries
    return Object.entries(specific).filter(([key]) => key !== "brand");
  }, [selectedFilters.category, filters]);

  const handleResetFilters = () => {
    setSelectedFilters(defaultFilters);
  };

  const debouncedFilterUpdate = useMemo(
    () =>
      debounce((filters) => {
        onFiltersChange(filters);
      }, 600), // adjust delay as needed
    [onFiltersChange]
  );

  useEffect(() => {
    debouncedFilterUpdate(selectedFilters);
  }, [selectedFilters, debouncedFilterUpdate]);

  return (
    <aside className="w-full  pb-8">
      {/* 🔄 Reset Button */}
      <div className="flex justify-end mb-2 pr-2">
        <button
          onClick={handleResetFilters}
          title="Reset Filters"
          className="cursor-pointer flex items-center gap-1 text-sm text-gray-600 hover:text-black transition"
        >
          <FiRotateCw className="w-4 h-4" />
          <span className="text-xs">Reset</span>
        </button>
      </div>

      {/* Category */}
      <FilterSection
        title="Category"
        isOpen={openSections.category}
        toggleOpen={() => toggleSection("category")}
      >
        {loadingFilters ? (
          <div className="flex justify-center py-4">
            <BeatLoader size={10} color="gray" />
          </div>
        ) : (
          <>
            {/* All Category */}
            <label className="cursor-pointer flex items-center gap-2 text-sm text-gray-800">
              <input
                type="radio"
                name="category"
                checked={selectedFilters.category === ""}
                onChange={() => handleCategoryChange("")}
                className="radio-custom cursor-pointer"
              />
              All
            </label>
            {/* Other Categories realted to the Electronic Devices */}
            {filters.categories?.map((item) => (
              <label
                key={item}
                className="cursor-pointer flex items-center gap-2 text-sm text-gray-800"
              >
                <input
                  type="radio"
                  name="category"
                  checked={selectedFilters.category === item}
                  onChange={() => handleCategoryChange(item)}
                  className="radio-custom cursor-pointer"
                />
                {item}
              </label>
            ))}
          </>
        )}
      </FilterSection>

      <FilterSection
        title="Price"
        isOpen={openSections.price}
        toggleOpen={() => toggleSection("price")}
      >
        {/* Displayed Range Knobs with custom style */}

        <PriceRangeSelector
          minPrice={selectedFilters.minPrice}
          maxPrice={selectedFilters.maxPrice}
          min={filters.pricerange?.min || 0}
          max={filters.pricerange?.max || 200000}
          onChange={({ minPrice, maxPrice }) =>
            setSelectedFilters((prev) => ({
              ...prev,
              minPrice,
              maxPrice,
              price: "All Price",
            }))
          }
        />

        {/* Predefined Ranges */}
        <div className="mt-4 space-y-1">
          {prices.map((item) => (
            <label
              key={item}
              className="cursor-pointer flex items-center gap-2 text-sm"
            >
              <input
                type="radio"
                name="price"
                checked={selectedFilters.price === item}
                onChange={() => handlePriceChange(item)}
                className="radio-custom cursor-pointer"
              />
              {item}
            </label>
          ))}
        </div>
      </FilterSection>

      {/* Brands */}
      <FilterSection
        title="Brand"
        isOpen={openSections.brand}
        toggleOpen={() => toggleSection("brand")}
      >
        {loadingFilters ? (
          <div className="flex justify-center py-4">
            <BeatLoader size={10} color="gray" />
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2">
            {(categoryBasedBrands || []).map((item) => (
              <label
                key={item}
                className="cursor-pointer flex items-center gap-2 text-sm"
              >
                <input
                  type="checkbox"
                  checked={selectedFilters?.brands?.includes(
                    item.toLowerCase()
                  )}
                  onChange={() => handleBrandToggle(item)}
                  className="accent-black cursor-pointer"
                />
                {item}
              </label>
            ))}
          </div>
        )}
      </FilterSection>

      {/* Features */}
      <FilterSection
        title="Features"
        isOpen={openSections.features}
        toggleOpen={() => toggleSection("features")}
      >
        {loadingFilters ? (
          <div className="flex justify-center py-4">
            <BeatLoader size={10} color="gray" />
          </div>
        ) : (
          categoryBasedFeatures?.map(([feature, values]) => (
            <div key={feature} className="mb-4">
              <h4 className="font-semibold text-sm mb-2 capitalize">
                {feature}
              </h4>
              <div className="grid grid-cols-2 gap-2">
                {values.map((item) => (
                  <label
                    key={item}
                    className="cursor-pointer flex items-center gap-2 text-sm"
                  >
                    <input
                      type="checkbox"
                      checked={
                        selectedFilters.features[feature]?.includes(item) ||
                        false
                      }
                      onChange={() => handleFeatureToggle(feature, item)}
                      className="accent-black cursor-pointer"
                    />
                    {item}
                  </label>
                ))}
              </div>
              <hr className="my-2 border-gray-300" />
            </div>
          ))
        )}
      </FilterSection>

      <div className="hidden sm:block">
        <FeaturedProductBaner />
      </div>
    </aside>
  );
};

export default SidebarFilters;
