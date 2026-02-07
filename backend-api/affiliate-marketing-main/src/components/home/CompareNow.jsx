import React, { useEffect, useState } from "react";
import { RxCross2 } from "react-icons/rx";
import { z } from "zod";
import { toast } from "react-toastify";
import CompareBox from "./compare/CompareBox";
import CompareModal from "./compare/CompareModal";
import { useNavigate } from "react-router-dom";

const TABS = ["SmartPhone", "Laptop", "Accessories"];

const schema = z
  .array(
    z
      .object({
        _id: z.string(),
        name: z.string(),
        price: z.string(),
        image: z.string().url(),
      })
      .nullable()
  )
  .refine((arr) => arr.filter(Boolean).length >= 2, {
    message: "Select at least 2 products to compare",
  });

const CompareNow = () => {
  const [activeTab, setActiveTab] = useState("SmartPhone");
  const [comparisons, setComparisons] = useState([null, null, null, null]);
  const [modalIndex, setModalIndex] = useState(null);
  const navigate = useNavigate();

  const handleSelectProduct = (product) => {
    console.log("product", product);
    try {
      if (modalIndex !== null) {
        const updated = [...comparisons];
        updated[modalIndex] = {
          _id: product._id,
          name: product.title,
          price: product?.vendors?.flipkart?.discountprice
            ? `Rs. ${product.vendors.flipkart.discountprice}/-`
            : product?.vendors?.amazon?.discountprice
            ? `Rs. ${product.vendors.amazon.discountprice}/-`
            : "Price not available",
          image: product.image?.thumbnail,
        };
        setComparisons(updated);
        setModalIndex(null);
      }
    } catch (err) {
      console.log("Error selecting product:", err);
    }
  };

  const handleRemove = (index) => {
    const updated = [...comparisons];
    updated[index] = null;
    setComparisons(updated);
  };

  const handleCompare = () => {
    try {
      schema.parse(comparisons);
      toast.success("Comparison started 🚀");
      // Navigate to compare page or API call
      navigate("/compare", { state: comparisons });
    } catch (err) {
      toast.error(err.errors[0].message);
    }
  };

  useEffect(() => {
    setModalIndex(null);
    setComparisons([null, null, null, null]);
  }, [activeTab]);

  return (
    <div className="flex flex-col items-center w-full px-4 pt-16">
      {/* Tabs */}
      <div className="flex justify-center gap-2 w-full max-w-2xl sm:max-w-4xl mb-8">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`relative px-3 xs:px-6 py-2 text-sm sm:text-2xl font-semibold transition-all 
              ${
                activeTab === tab
                  ? "bg-primary text-black rounded-t-md shadow-md border-b-[2px] border-gray-400"
                  : "text-gray-400 hover:text-black border-b-[2px] border-gray-400"
              }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Title */}
      <div className="text-center text-xl sm:text-2xl md:text-3xl font-semibold text-black mb-8">
        Compare {activeTab.toLowerCase()}, <br className="hidden sm:block" />
        save instantly
      </div>

      {/* Comparison Grid */}
      <div className="flex flex-wrap justify-center items-center gap-4 md:gap-6 w-full max-w-7xl">
        {comparisons.map((item, index) => (
          <React.Fragment key={index}>
            <CompareBox
              item={item}
              index={index}
              onAdd={() => setModalIndex(index)}
              onRemove={() => handleRemove(index)}
            />
            {index < comparisons.length - 1 && (
              <div className="text-xs font-bold bg-black text-white rounded-full w-6 h-6 flex items-center justify-center">
                VS
              </div>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Compare Now Button */}
      <div className="mt-10 sm:mt-16">
        <button
          onClick={handleCompare}
          className="bg-[#DCFE50] px-6 py-2 rounded font-semibold text-black text-sm sm:text-base hover:bg-lime-300 transition"
        >
          COMPARE NOW
        </button>
      </div>

      {/* Modal */}
      {modalIndex !== null && (
        <CompareModal
          activeTab={activeTab}
          onClose={() => setModalIndex(null)}
          onSelect={handleSelectProduct}
        />
      )}
    </div>
  );
};

export default CompareNow;
