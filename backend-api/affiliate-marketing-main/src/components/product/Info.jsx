import React, { useState } from "react";
import { FaStar } from "react-icons/fa";
import { MdSpeed, MdDisplaySettings } from "react-icons/md";

const getDefaultVendorWithRating = (vendors) => {
  if (!vendors || typeof vendors !== "object")
    return { name: null, data: null };

  const vendorsArray = Object.entries(vendors);
  if (vendorsArray.length === 0) return { name: null, data: null };

  const vendorsWithRating = vendorsArray.filter(
    ([, data]) => typeof data?.rating === "number"
  );

  const bestVendor = vendorsWithRating.sort(
    (a, b) => b[1].rating - a[1].rating
  )[0] ||
    vendorsArray[0] || [null, null];

  const [bestVendorName, bestVendorData] = bestVendor;

  return { name: bestVendorName, data: bestVendorData };
};

const Info = ({ product = {}, formatPrice }) => {
  const [displayIMG, setDisplayIMG] = useState(
    product?.image?.thumbnail || product?.image?.urls?.[0] || ""
  );

  const { name: defaultVendorName, data: defaultVendorData } =
    getDefaultVendorWithRating(product?.vendors);

  const { features = {}, title = "" } = product;

  const details = features?.details || {};
  const display = details?.display || {};
  const performance = details?.performance || {};
  const design = details?.design || {};
  const audio = details?.audio || {};

  // ✅ safe image array
  const images = Array.isArray(product?.image?.urls) ? product.image.urls : [];

  return (
    <div className="p-4 md:p-8 bg-white">
      {/* Title */}
      <h1 className="text-2xl font-bold text-gray-900">
        {title || "No Title"}
      </h1>

      {/* Rating */}
      <div className="flex items-center gap-4 text-sm text-gray-600 mt-2">
       {defaultVendorData?.rating != null && (
  <div className="flex items-center gap-1">
    <FaStar className="text-yellow-500" />
    <span>
      {(Number(defaultVendorData.rating) || 0).toFixed(1)}/5 ({defaultVendorName || "N/A"} Ratings)
    </span>
  </div>
)}

      </div>

      {/* Grid Layout */}
      <div className="mt-6 grid md:grid-cols-2 gap-6">
        {/* Left: Image & thumbnails */}
        <div className="space-y-4">
          {displayIMG || product?.image?.thumbnail ? (
            <img
              src={displayIMG || product?.image?.thumbnail}
              alt={title || "product"}
              className="w-full h-auto bg-gray-100 rounded-lg"
            />
          ) : (
            <div className="w-full h-64 flex items-center justify-center bg-gray-100 rounded-lg text-gray-500">
              No Image Available
            </div>
          )}

          <div className="flex gap-2 overflow-x-auto">
            {images.map((url, i) =>
              url ? (
                <img
                  key={i}
                  src={url}
                  alt={`img-${i}`}
                  className="w-16 h-16 object-cover border rounded cursor-pointer"
                  onClick={() => setDisplayIMG(url)}
                />
              ) : (
                <div
                  key={i}
                  className="w-16 h-16 flex items-center justify-center bg-gray-100 border rounded text-gray-400"
                >
                  No Img
                </div>
              )
            )}
          </div>
        </div>

        {/* Right: Specs & Price */}
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-800">Key Specs</h2>

          {/* Display */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <MdDisplaySettings /> Display
            </h3>
            <ul className="text-sm text-gray-600 list-disc pl-5 space-y-1 mt-1">
              <li>Size: {display?.screen_size || "N/A"}</li>
              <li>Resolution: {display?.resolution || "N/A"}</li>
              <li>Brightness: {display?.brightness || "N/A"}</li>
              <li>Touchscreen: {display?.touchscreen ? "Yes" : "No"}</li>
            </ul>
          </div>

          {/* Performance */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <MdSpeed /> Performance
            </h3>
            <ul className="text-sm text-gray-600 list-disc pl-5 space-y-1 mt-1">
              <li>Processor: {performance?.processor || "N/A"}</li>
              <li>Cores: {performance?.cores || "N/A"}</li>
              <li>OS: {performance?.operating_system || "N/A"}</li>
              <li>Model No: {performance?.model_number || "N/A"}</li>
            </ul>
          </div>

          {/* Design */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700">Design</h3>
            <ul className="text-sm text-gray-600 list-disc pl-5 space-y-1 mt-1">
              <li>Dimensions: {design?.dimensions || "N/A"}</li>
              <li>Weight: {design?.weight || "N/A"}</li>
              <li>Color: {design?.color || "N/A"}</li>
            </ul>
          </div>

          {/* Audio */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700">Audio</h3>
            <ul className="text-sm text-gray-600 list-disc pl-5 space-y-1 mt-1">
              <li>Speakers: {audio?.speaker || "N/A"}</li>
              <li>Mic: {audio?.microphone || "N/A"}</li>
            </ul>
          </div>

          {/* Pricing Box */}
          {defaultVendorData && (
            <div className="mt-6 border p-4 rounded bg-gray-50 space-y-2">
              <div className="text-xs text-gray-500">Special Price</div>
              <div className="text-2xl font-bold text-red-600">
                {formatPrice
                  ? formatPrice(defaultVendorData?.discountprice)
                  : defaultVendorData?.discountprice || "N/A"}
              </div>
              {defaultVendorData?.price && (
                <div className="text-sm text-gray-500 line-through">
                  {formatPrice
                    ? formatPrice(defaultVendorData?.price)
                    : defaultVendorData?.price}
                </div>
              )}
              {defaultVendorData?.affiliatelink && (
                <a
                  href={defaultVendorData.affiliatelink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block mt-3 px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600"
                >
                  Go To Store
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Info;
