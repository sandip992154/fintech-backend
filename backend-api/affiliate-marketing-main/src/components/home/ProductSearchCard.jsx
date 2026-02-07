import React from "react";
import { useNavigate } from "react-router-dom";

const ProductSearchCard = ({ product }) => {
  const navigate = useNavigate();
  if (!product) return null;

  // Get image
  const thumbnail = product.image?.thumbnail;

  // Get title
  const title = product.title || "No title";

  // Get minimum price among vendors
  const vendors = product.vendors ? Object.values(product.vendors) : [];
  const minPrice = vendors.length
    ? Math.min(...vendors.map((v) => v.discountprice || v.price || Infinity))
    : null;

  // Availability check
  const isAvailable = vendors.length > 0;

  const handleProductClick = () => {
    if (product._id) {
      navigate(`/product/${product._id}`);
    }
  };

  return (
    <div
      onClick={handleProductClick}
      className="flex items-center  gap-3 px-3 py-2 hover:bg-gray-50 cursor-pointer"
    >
      {/* Product Image */}
      {thumbnail && (
        <img
          src={thumbnail}
          alt={title}
          className="w-12 h-12 object-contain rounded"
        />
      )}

      {/* Product Info */}
      <div className="flex-1 text-start">
        <p className="font-medium text-black line-clamp-1">{title}</p>
        {minPrice ? (
          <p className="text-sm text-gray-600">
            From{" "}
            <span className="text-orange-600 font-semibold">
              ₹{minPrice.toLocaleString("en-IN")}
            </span>{" "}
            - {isAvailable ? "Available" : "Out of stock"}
          </p>
        ) : (
          <p className="text-sm text-gray-500">Price not available</p>
        )}
      </div>
    </div>
  );
};

export default ProductSearchCard;
