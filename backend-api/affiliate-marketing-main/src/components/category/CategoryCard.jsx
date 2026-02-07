import React from "react";
import { useNavigate } from "react-router-dom";

const CategoryCard = ({ product }) => {
  const navigate = useNavigate();

  const handleCompare = () => {
    navigate("/CompareNowSingle", {
      state: { product, category: product.category },
    });
  };
  return (
    <div className="bg-lightBg p-6 rounded-lg flex flex-col items-center text-center transition-all duration-200 hover:shadow-xl hover:scale-[1.02] cursor-pointer">
      <img
        src={product?.image}
        alt={product?.name}
        className="w-16 h-16 object-contain mb-4"
      />
      <div className="font-bold text-darkHover">{product?.name}</div>
      <div className="text-small text-gray-600">{product?.price}</div>
      <button className="mt-4 btn-compare" onClick={handleCompare}>
        Compare
      </button>
    </div>
  );
};

export default CategoryCard;
