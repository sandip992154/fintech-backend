import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";

import { z } from "zod";
import CompareModal from "../components/home/compare/CompareModal";
import CompareBox from "../components/home/compare/CompareBox";

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

const CompareNowSingle = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const selectedCategory = location.state?.category || "";
  const activeTab = selectedCategory; // Removed unused setActiveTab

  const [comparisons, setComparisons] = useState([null, null, null, null]);
  const [modalIndex, setModalIndex] = useState(null);

  // useEffect(() => {
  //   // Pre-fill first box with clicked product if passed
  //   if (location.state && location.state.product) {
  //     setComparisons((prev) => {
  //       const updated = [...prev];
  //       updated[0] = location.state.product;
  //       return updated;
  //     });
  //   }
  // }, [location.state]);

  const handleSelectProduct = (product) => {
    if (modalIndex !== null) {
      const updated = [...comparisons];
      updated[modalIndex] = {
        _id: product._id,
        name: product.title,
        price: `Rs. ${product.vendors.flipkart.discountprice}/-`,
        image: product.image?.thumbnail,
      };
      setComparisons(updated);
      setModalIndex(null);
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
      toast.success("Comparison started ");
      navigate("/compare", { state: comparisons });
    } catch (err) {
      toast.error(err.errors[0].message);
    }
  };

  return (
    <div className="flex flex-col items-center w-full px-4 pt-16">
      {/* Tabs */}
      <div className="flex flex-col items-center w-full px-4 pt-16">
        {/* Show only the selected category */}
        <h2 className="text-2xl font-semibold bg-[#DCFE50] px-6 py-2 mb-5 rounded">
          {activeTab}
        </h2>
      </div>

      {/* Comparison Grid */}
      <div className="flex flex-wrap justify-center items-center gap-4 md:gap-6 w-full max-w-7xl">
        {comparisons.map((item, index) => (
          <React.Fragment key={index}>
            <CompareBox
              item={item}
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
          className="bg-[#DCFE50] px-6 py-2 mb-5 rounded font-semibold text-black text-sm sm:text-base hover:bg-lime-300 transition"
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

export default CompareNowSingle;
