import React, { useState } from "react";

const Section = ({ title, labels, products = [], sectionKey }) => {
  // sectionKey = "design" | "display" | "network&connectivity" etc.
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="mb-6 bg-white rounded-md shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-dotted border-gray-300">
        <h3 className="font-semibold text-lg text-gray-800">{title}</h3>
        <label className="inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            className="sr-only peer"
            checked={isOpen}
            onChange={() => setIsOpen(!isOpen)}
          />
          <div className="relative w-9 h-5 bg-[#DCFE50] 
           rounded-full peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px]
           after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#DCFE50]"></div>
        </label>
      </div>

      {/* Table */}
      {isOpen && (
        <div className="overflow-x-auto transition-all duration-300 ease-in-out">
          <table className="w-full text-sm">
            <tbody>
              {labels.map((label, idx) => (
                <tr
                  key={idx}
                  className={idx % 2 === 0 ? "bg-white" : "bg-gray-200"}
                >
                  <td className="font-medium text-black p-3 whitespace-nowrap w-1/5">
                    {label}
                  </td>

                  {products.map((product, i) => {
                    // Access nested features.details
                    const value =
                      product.features?.details?.[sectionKey]?.[
                        label.toLowerCase()
                      ] || "-";
                    return (
                      <td key={i} className="text-gray-700 p-3 text-center">
                        {value}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Section;
