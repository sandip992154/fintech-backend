import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { FaStar, FaStarHalfAlt, FaRegStar } from "react-icons/fa";
import { apiEndpoints } from "../../services/api";
import { toast } from "react-toastify";
import { ClipLoader } from "react-spinners";
import Info from "./Info";
import Prices from "./Prices";
import Specs from "./Specs";

const formatPrice = (p) => (p ? `₹${Number(p).toLocaleString("en-IN")}` : "");

const renderStars = (r) => {
  if (!r || r < 0) return null;
  const full = Math.floor(r);
  const half = r % 1 >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);
  return (
    <div className="flex text-yellow-500 text-xs sm:text-sm">
      {Array(full)
        .fill()
        .map((_, i) => (
          <FaStar key={`f${i}`} />
        ))}
      {half && <FaStarHalfAlt />}
      {Array(empty)
        .fill()
        .map((_, i) => (
          <FaRegStar key={`e${i}`} />
        ))}
    </div>
  );
};

const ProductDetails = () => {
  const { id } = useParams();
  const [product, setProduct] = useState({});
  const [tab, setTab] = useState("info");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiEndpoints.getProductDetail(id);
        setProduct(response.data || {});
      } catch (error) {
        console.error("Error fetching product:", error);
        setError("Failed to load product details");
        toast.error("Failed to load product details");
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchProduct();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <ClipLoader color="#dcfe50" size={50} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <p className="text-red-500 mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-2 bg-primary text-black font-semibold rounded-lg hover:bg-primary/80"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-8 md:p-16 rounded bg-gray-200 py-19">
      {/* Tabs */}
      <div className="flex gap-2 sm:gap-6 text-sm sm:text-lg font-semibold bg-gray-300 rounded overflow-x-auto">
        {["info", "prices", "specs"].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 sm:px-8 py-2 capitalize whitespace-nowrap transition ${
              tab === t
                ? "border-b-2 bg-white border-orange-500 text-orange-600"
                : "text-gray-600"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mt-4 sm:mt-6">
        {tab === "info" && (
          <Info
            product={product}
            renderStars={renderStars}
            formatPrice={formatPrice}
          />
        )}

        {tab === "prices" && (
          <Prices
            product={product}
            renderStars={renderStars}
            formatPrice={formatPrice}
          />
        )}

        {tab === "specs" && (
          <Specs
            product={product}
            renderStars={renderStars}
            formatPrice={formatPrice}
          />
        )}
      </div>
    </div>
  );
};

export default ProductDetails;
