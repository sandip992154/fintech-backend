import React from "react";
import RatingStars from "./RatingStars";
import { Link } from "react-router-dom";

const ProductCard = ({ product }) => {
  // Get the best price from all vendors
  const getBestPrice = () => {
    if (!product?.vendors) return { price: 0, discountprice: 0, rating: 0 };
    
    const vendorData = Object.values(product.vendors).filter(
      v => v.discountprice > 0 || v.price > 0
    );
    
    if (vendorData.length === 0) return { price: 0, discountprice: 0, rating: 0 };
    
    // Find vendor with lowest discount price
    const bestVendor = vendorData.reduce((best, current) => {
      const currentPrice = current.discountprice || current.price;
      const bestPrice = best.discountprice || best.price;
      return currentPrice < bestPrice ? current : best;
    });
    
    return bestVendor;
  };

  const { price, discountprice, rating } = getBestPrice();

  const discountPercent =
    price && discountprice && price > discountprice
      ? Math.floor(((price - discountprice) / price) * 100)
      : 0;

  return (
    <div className="max-w-[14rem] border border-gray-200 rounded p-4 flex-shrink-0 bg-white hover:shadow-md transition">
      <div className="relative mb-3">
        {product.label && (
          <span
            className={`absolute top-2 left-2 text-[10px] px-2 py-1 rounded text-white font-semibold uppercase ${
              product?.label === "HOT"
                ? "bg-red-500"
                : product?.label === "BEST DEALS"
                ? "bg-blue-500"
                : "bg-gray-500"
            }`}
          >
            {product.label}
          </span>
        )}
        <img
          src={product.image?.thumbnail || product.image?.urls?.[0]}
          alt={product.title}
          className="w-full h-40 object-contain blend-soft"
        />
      </div>

      <RatingStars rating={rating || product.rating || 0} reviews={product.reviews || 0} />
      <Link to={`/product/${product._id || product.id}`}>
        <h3 className="text-sm font-medium mt-1 line-clamp-2">
          {product.title}
        </h3>
      </Link>
      <div className="mt-1 text-sm">
        <span className="text-blue-600 font-bold mr-2">
          {discountprice > 0 ? `₹${discountprice.toLocaleString('en-IN')}` : 'N/A'}
        </span>

        <p>
          {price > 0 && price !== discountprice && (
            <span className="text-red-600 line-through mr-2">
              ₹{price.toLocaleString('en-IN')}
            </span>
          )}
          {discountPercent > 0 && (
            <span className="text-green-600 font-semibold">
              ({discountPercent}% OFF)
            </span>
          )}
        </p>
      </div>
    </div>
  );
};

export default ProductCard;
