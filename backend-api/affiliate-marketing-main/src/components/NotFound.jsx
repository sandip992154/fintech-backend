import React from "react";
import { Link, useNavigate } from "react-router-dom";
// import { ArrowLeft, Home } from "lucide-react";
import { FaArrowLeft, FaHome } from "react-icons/fa";
import { ErrorImg } from "../assets/ImportImages";

const NotFound = () => {
  const navigate = useNavigate();

  const commonBtnStyles =
    "flex items-center justify-center gap-2 font-semibold px-5 py-2 rounded w-full sm:w-auto";

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white text-center px-4 py-10 sm:py-16">
      <img
        src={ErrorImg}
        alt="404 Illustration"
        className="w-80 max-w-full md:max-w-md mb-6"
      />

      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
        404, Page not found
      </h1>

      <p className="text-gray-600 max-w-md text-sm sm:text-base mb-6 px-2 sm:px-0">
        Something went wrong. The page you’re looking for might have been
        removed or the link is broken.
      </p>

      <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto justify-center items-center">
        <Link
          to=""
          onClick={() => navigate(-1)}
          className={`${commonBtnStyles} bg-lime-300 hover:bg-lime-400 text-black`}
        >
          <FaArrowLeft size={18} /> Go Back
        </Link>

        <Link
          to="/"
          onClick={() => navigate("/")}
          className={`${commonBtnStyles} border border-black hover:bg-gray-100 text-black`}
        >
          <FaHome size={18} /> Go to Home
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
