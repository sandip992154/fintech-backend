import React, { useEffect, useState, useCallback } from "react";
import { useLocation } from "react-router-dom";
import { ClipLoader } from "react-spinners";
import { toast } from "react-hot-toast";

import DeviceComparisonHeader from "../components/compare/DeviceComparisonHeader";
import DeviceCards from "../components/compare/DeviceCards";
import { fallbackDevices } from "../constants/deviceConstants";
import DesignSection from "../components/compare/DesignSection";
import DisplaySection from "../components/compare/DisplaySection";
import NetworkSection from "../components/compare/NetworkSection";
import PriceSection from "../components/compare/PriceSection";
import { apiService } from "../services/api";

export const Compare = () => {
  const location = useLocation();
  const comparisons = location.state;

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);

  const [hiddenIds, setHiddenIds] = useState(
    () => JSON.parse(localStorage.getItem("hiddenIds")) || []
  );

  const handleRemoveProduct = (selectedProduct) => {
    if (!selectedProduct) return; // ✅ safeguard
    const newHidden = [...hiddenIds, selectedProduct._id || selectedProduct.id];
    setHiddenIds(newHidden);
    localStorage.setItem("hiddenIds", JSON.stringify(newHidden));
    setProducts(
      products.filter((p) => p && !newHidden.includes(p._id || p.id))
    );
  };

  const fetchProducts = useCallback(
    async (ids) => {
      try {
        setLoading(true);
        const uniqueIds = [...new Set(ids.filter(Boolean))]; // filter out null/undefined ids

        // Use single batch API call for optimization
        const responses = await Promise.allSettled(
          uniqueIds.map(async (id) => {
            try {
              return await apiService.getProductById(id);
            } catch (error) {
              console.warn(`Failed to fetch product ${id}:`, error);
              return null;
            }
          })
        );

        const fetchedProducts = responses
          .map((res) => (res.status === "fulfilled" ? res.value : null))
          .filter(Boolean)
          .map((p) => ({ ...p, _id: p._id || p.id }));

        // Validate products have vendor data for comparison
        const validProducts = fetchedProducts.filter(
          (p) => p && p.vendors && Object.keys(p.vendors).length > 0 && !hiddenIds.includes(p._id)
        );

        setProducts(validProducts);
        
        if (validProducts.length === 0 && uniqueIds.length > 0) {
          toast.error('No products with pricing data found for comparison');
        }
      } catch (err) {
        console.error("Error fetching products:", err);
        toast.error('Failed to load products for comparison');
      } finally {
        setLoading(false);
      }
    },
    [hiddenIds]
  );

  useEffect(() => {
    if (comparisons?.length) {
      const ids = comparisons
        .filter(Boolean) // ✅ filter null comparisons
        .map((p) => p._id || p.id)
        .filter(Boolean); // ✅ remove empty ids
      if (ids.length) {
        fetchProducts(ids);
      }
    }
  }, [comparisons, fetchProducts]);

  // Always ensure at least 4 cards
  let visibleProducts = products.filter(
    (p) => p && !hiddenIds.includes(p._id || p.id)
  ); // ✅ skip nulls safely
  const totalCards = 4;
  if (visibleProducts.length < totalCards) {
    const fallbackCount = totalCards - visibleProducts.length;
    const fallbackSlice = fallbackDevices
      .slice(0, fallbackCount)
      .map((d) => ({ ...d, isFallback: true }));
    visibleProducts = [...visibleProducts, ...fallbackSlice];
  }

  return (
    <div className="py-8 maxscreen screen-margin overflow-hidden">
      {loading ? (
        <div className="min-h-screen w-full flex items-center justify-center">
          <ClipLoader size={25} />
          <span className="ml-2">Loading...</span>
        </div>
      ) : (
        <>
          <DeviceComparisonHeader products={visibleProducts} />
          <DeviceCards
            products={visibleProducts}
            onRemove={handleRemoveProduct}
          />
          <DesignSection products={visibleProducts} />
          <DisplaySection products={visibleProducts} />
          <NetworkSection products={visibleProducts} />
          <PriceSection products={visibleProducts} />
        </>
      )}
    </div>
  );
};
