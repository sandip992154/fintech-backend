import React from "react";
import { useNavigate } from "react-router-dom";
import { ImMobile } from "react-icons/im";
import { AiOutlineLaptop } from "react-icons/ai";
import { IoHeadset } from "react-icons/io5";
import {
  Amazon,
  Flipkart,
  Croma,
  VS,
  SamsungLogo,
  moreImg,
} from "../../assets/ImportImages";
import SearchBar from "./SearchBar";

const ComparePrices = () => {
  const navigate = useNavigate();

  const categories = [
    { icon: <ImMobile />, label: "Mobiles", route: "mobiles" },
    { icon: <AiOutlineLaptop />, label: "Laptops", route: "laptops" },
    { icon: <IoHeadset />, label: "Accessories", route: "accessories" },
  ];

  const brands = [
    { src: Amazon, label: "Amazon" },
    { src: Flipkart, label: "Flipkart" },
    { src: Croma, label: "Croma" },
    { src: VS, label: "Vijay Sales" },
    { src: SamsungLogo, label: "Samsung" },
    { src: moreImg, label: "More" },
  ];

  return (
    <div className="maxscreen screen-margin overflow-hidden text-center flex flex-col justify-center w-full py-20">
      {/* Heading */}
      <p className="text-2xl sm:text-4xl md:text-3xl lg:text-5xl 2xl:text-7xl text-black font-semibold">
        Compare Prices. Save Big.
      </p>

      <p className="mt-4 md:mt-6 text-sm sm:text-md md:text-lg lg:text-xl font-semibold text-gray-500">
        Find best deals on mobiles, laptops & headphones
        <br className="hidden md:block" />
        from top online stores.
      </p>

      {/* Search Component */}
      <div className="flex justify-center mt-6 md:mt-8 w-full px-4 relative">
        <SearchBar />
      </div>

      {/* Categories */}
      <div className="flex flex-wrap justify-center items-center mt-10 gap-8 sm:gap-12 md:gap-20">
        {categories.map(({ icon, label, route }, idx) => (
          <div
            key={idx}
            onClick={() =>
              navigate("/products", { state: { category: route } })
            }
            className="flex flex-col items-center rounded-2xl bg-primary p-4 cursor-pointer hover:scale-105 transition-transform"
          >
            {React.cloneElement(icon, {
              className:
                "text-black w-20 h-20 sm:w-28 sm:h-28 md:w-36 md:h-36 p-3",
            })}
            <p className="text-sm sm:text-base md:text-lg pt-2">{label}</p>
          </div>
        ))}
      </div>

      {/* Brand Logos */}
      <div className="w-full border-t border-b border-gray-200 py-4 my-8">
        <div className="flex flex-wrap justify-center items-center gap-x-6 gap-y-4 px-4">
          {brands.map(({ src, label }, index) => (
            <div
              key={index}
              className="flex items-center gap-2 w-max whitespace-nowrap"
            >
              <img src={src} alt={label} className="h-6 w-6 object-contain" />
              <span className="text-sm font-medium text-black">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ComparePrices;
