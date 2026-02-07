import React, { useRef } from "react";

const formatKey = (key) =>
  key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/\s+([A-Z])/g, " $1");

const Specs = ({ product }) => {
  const sections = product?.features?.details || {};

  const filteredSections = Object.entries(sections).filter(
    ([, specs]) =>
      specs && Object.values(specs).some((val) => val !== null && val !== "")
  );

  const sectionRefs = useRef({});

  const handleScrollTo = (key) => {
    const ref = sectionRefs.current[key];
    if (ref) {
      ref.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  if (!filteredSections.length) return null;

  return (
    <div className="bg-white">
      {/* Sticky Tab Navigation */}
      <div className="sticky top-0 z-10 bg-white py-3 px-2 shadow-sm overflow-x-auto scrollbar-hide">
        <div className="flex gap-3 text-sm font-medium min-w-max">
          {filteredSections.map(([key]) => (
            <button
              key={key}
              onClick={() => handleScrollTo(key)}
              className="px-4 py-2 bg-orange-500 cursor-pointer text-white rounded-full 
                         border border-primary hover:bg-gray-600 
                         whitespace-nowrap transition text-xs sm:text-sm"
            >
              {formatKey(key)}
            </button>
          ))}
        </div>
      </div>

      {/* Section Details */}
      <div className="">
        {filteredSections.map(([sectionKey, specs]) => (
          <div
            key={sectionKey}
            ref={(el) => (sectionRefs.current[sectionKey] = el)}
            className="p-4 sm:p-6"
          >
            <h3 className="border-l-2 border-l-orange-500 pl-3 text-lg sm:text-xl font-semibold text-gray-800">
              {formatKey(sectionKey)}
            </h3>
            <div className="text-sm border border-gray-400 rounded m-3 sm:m-4 p-3 sm:p-4">
              {Object.entries(specs).map(
                ([specKey, value]) =>
                  value && (
                    <div
                      key={specKey}
                      className="flex flex-col sm:flex-row justify-between gap-2 py-2"
                    >
                      <span className="text-gray-500 font-medium text-sm sm:text-base">
                        {formatKey(specKey)}
                      </span>
                      <span className="text-gray-900 text-sm sm:text-base break-words sm:max-w-[60%]">
                        {value}
                      </span>
                    </div>
                  )
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Specs;
