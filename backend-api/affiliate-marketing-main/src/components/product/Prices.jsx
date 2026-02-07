import React from "react";
import { FaStar } from "react-icons/fa";
import { Amazon, Flipkart, Croma, VS } from "../../assets/ImportImages";

const vendorLogos = {
  amazon: Amazon,
  flipkart: Flipkart,
  croma: Croma,
  vijaysales: VS,
  jiomart:
    "data:image/png;base64,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",
};

// Helper: Remove commas and convert to number
const parsePrice = (price) => {
  if (!price) return 0;
  if (typeof price === "string") {
    return Number(price.replace(/,/g, ""));
  }
  return price;
};

const formatPrice = (price) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
  }).format(price);

const Prices = ({ product }) => {
  const vendors = Object.entries(product.vendors || {});
  const { ram, rom } = product.features?.details?.storage || {};

  return (
    <div className="space-y-5 mt-4">
      {vendors.map(([vendor, data], idx) => {
        const {
          discountprice,
          price,
          rating,
          affiliatelink,
          offers = [],
        } = data;

        // Convert prices to numbers after removing commas
        const numericPrice = parsePrice(price);
        const numericDiscount = parsePrice(discountprice);

        const discountPercent = numericPrice
          ? Math.round(((numericPrice - numericDiscount) / numericPrice) * 100)
          : null;

        return (
          <div
            key={idx}
            className="flex flex-col sm:flex-row justify-between items-start sm:items-center border rounded-xl p-4 bg-white shadow-sm"
          >
            {/* Left side: Vendor + config + logo */}
            <div className="flex flex-col items-start gap-4 w-full sm:w-auto">
              <div>
                <div className="font-semibold text-lg text-gray-800">
                  {ram} + {rom}
                </div>
                <div className="flex gap-2 items-center justify-center text-xl font-bold text-gray-600 mt-1">
                  <img
                    src={vendorLogos[vendor]}
                    alt={vendor}
                    className="w-8 h-8 object-contain"
                  />{" "}
                  {vendor}
                </div>

                {rating != null && (
                  <div className="flex items-center gap-1 text-yellow-500 mt-1">
                    {[...Array(Math.floor(Number(rating) || 0))].map((_, i) => (
                      <FaStar key={i} className="w-4 h-4" />
                    ))}
                    <span className="text-sm text-gray-700 ml-1">
                      ({Number(rating) || 0})
                    </span>
                  </div>
                )}
              </div>
              {offers.length > 0 && (
                <ul className="text-xs text-gray-600 mt-3 text-left list-disc ml-4 space-y-1 max-w-[280px]">
                  {offers.slice(0, 3).map((offer, i) => (
                    <li key={i}>{offer}</li>
                  ))}
                </ul>
              )}
            </div>

            {/* Right side: Price + CTA + Offers */}
            <div className="text-right mt-4 sm:mt-0 w-full sm:w-auto">
              <div className="text-xl font-bold text-black">
                {formatPrice(numericDiscount)}
              </div>
              {numericPrice && numericPrice !== numericDiscount && (
                <div className="text-sm text-gray-500 line-through">
                  {formatPrice(numericPrice)}
                </div>
              )}
              {discountPercent && (
                <div className="text-sm text-green-600 font-medium">
                  Save {discountPercent}% Off
                </div>
              )}
              <a
                href={affiliatelink}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block mt-2 bg-orange-600 hover:bg-orange-700 text-white text-sm font-semibold py-1.5 px-4 rounded shadow"
              >
                Go To Store
              </a>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Prices;
