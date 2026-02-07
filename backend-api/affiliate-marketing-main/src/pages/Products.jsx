import { useState, useMemo } from "react";
import SearchSortBar from "../components/products/SearchSortBar";
import ProductGrid from "../components/products/ProductGrid";
import ResponsiveSidebarWrapper from "../components/products/ResponsiveSideBar";
import { useLocation } from "react-router-dom";
export const Products = () => {



const location = useLocation();
const initialCategory = location.state?.category || "";

const [filters, setFilters] = useState({
  category: initialCategory,
  price: "All Price",
  minPrice: "",
  maxPrice: "",
  brands: [],
  features: {},
});


  // const [filters, setFilters] = useState({
  //   category: "",
  //   price: "All Price",
  //   minPrice: "",
  //   maxPrice: "",
  //   brands: [],
  //   features: {},
  // });
  const [searchQuery, setSearchQuery] = useState("");
  const [sortOption, setSortOption] = useState("-1");

  const sortOptions = [
    { label: "Price: Low to High", value: "1" },
    { label: "Price: High to Low", value: "-1" },
  ];

  // Utility function to clean filters
  const cleanFilters = (filters) => {
    const cleaned = { ...filters };

    // Remove empty arrays from features
    if (cleaned.features) {
      const cleanedFeatures = {};
      for (const [key, value] of Object.entries(cleaned.features)) {
        if (Array.isArray(value) && value.length > 0) {
          cleanedFeatures[key] = value;
        }
      }
      cleaned.features = cleanedFeatures;
    }

    if (Array.isArray(cleaned.brands) && cleaned.brands.length === 0) {
      delete cleaned.brands;
    }
    if (!cleaned.category) delete cleaned.category;
    if (!cleaned.minPrice) delete cleaned.minPrice;
    if (!cleaned.maxPrice) delete cleaned.maxPrice;

    return cleaned;
  };

  // ✅ Memoize cleaned filters
  const cleanedFilters = useMemo(() => cleanFilters(filters), [filters]);

  return (
    <section className="relative maxscreen screen-margin overflow-hidden py-20">
      <div className="flex py-8 gap-4 w-full ">
        <ResponsiveSidebarWrapper onFiltersChange={setFilters} />
        <section className="min-h-screen w-full ">
          <SearchSortBar
            searchPlaceholder="Search for anything..."
            sortLabel="Sort by:"
            sortOptions={sortOptions}
            selectedSort={sortOption}
            onSearchChange={setSearchQuery}
            onSortChange={setSortOption}
          />
          <ProductGrid
            filters={cleanedFilters}
            query={searchQuery}
            sortby={sortOption}
          />
        </section>
      </div>
    </section>
  );
};
