import React, { useState, useRef, useEffect } from "react";
import { NavLink } from "react-router-dom";
import { FiChevronDown, FiMenu, FiX } from "react-icons/fi";
import { FaInstagram, FaFacebookF, FaYoutube } from "react-icons/fa";

const navLinks = [
  { name: "Home", path: "/" },
  { name: "Products", path: "/products" },
  { name: "Category", path: "/category" },
  // { name: "Compare", path: "/compare" },
  { name: "Contact Us", path: "/contact-us" },
];

const socialLinks = [
  {
    name: "Instagram",
    icon: <FaInstagram size={20} className="text-primary" />,
    path: "https://instagram.com",
  },
  {
    name: "Facebook",
    icon: <FaFacebookF size={20} className="text-primary" />,
    path: "https://facebook.com",
  },
  {
    name: "Youtube",
    icon: <FaYoutube size={20} className="text-primary" />,
    path: "https://youtube.com",
  },
];

const navLinkClasses = ({ isActive }) =>
  `${
    isActive ? "font-bold border-b border-primary" : "text-primary"
  } pb-0.5 hover:text-white transition duration-200`;

const Header = () => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <header className="header">
<nav className="fixed top-0 left-0 w-full bg-black text-white px-6 py-4 flex justify-between items-center z-50">
        {/* Logo */}
        <div className="text-[18px] font-bold font-[Poppins]">Daam Dekho</div>

        {/* Hamburger Icon (mobile only) */}
        <div className="md:hidden">
          <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
            {isMobileMenuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
          </button>
        </div>

        {/* Desktop Nav */}
        <ul className="hidden md:flex items-center space-x-6 text-xs md:text-md 2xl:text-xl font-[Poppins]">
          {navLinks.map((link) => (
            <li key={link.path}>
              <NavLink
                to={link.path}
                className={({ isActive }) => navLinkClasses({ isActive })}
              >
                {link.name}
              </NavLink>
            </li>
          ))}

          {/* "More" dropdown */}
          <li className="relative" ref={dropdownRef}>
            <div
              className="text-primary flex items-center gap-1 cursor-pointer"
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            >
              More <FiChevronDown size={14} />
            </div>

            {isDropdownOpen && (
              <div className="absolute top-full right-0 mt-2 w-56 bg-black text-white border border-gray-700 rounded-md z-20">
                {socialLinks.map((item, index) => (
                  <a
                    key={index}
                    href={item.path}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-4 px-4 py-3 text-[15px] font-[Poppins] hover:bg-gray-800 transition-all border-b border-gray-700"
                  >
                    {item.icon}
                    <span className="text-primary font-medium">
                      {item.name}
                    </span>
                  </a>
                ))}
              </div>
            )}
          </li>
        </ul>

        {/* Mobile Nav Dropdown */}
        {isMobileMenuOpen && (
          <div className="absolute top-full left-0 w-full bg-black text-white px-6 py-4 z-20 flex flex-col gap-4 md:hidden">
            {navLinks.map((link) => (
              <NavLink
                key={link.path}
                to={link.path}
                className={({ isActive }) => navLinkClasses({ isActive })}
                onClick={() => setIsMobileMenuOpen(false)}
              >
                {link.name}
              </NavLink>
            ))}

            {/* Divider */}
            <div className="border-t border-gray-700 pt-2" />

            {/* Social Links */}
            <div className="flex flex-col gap-3">
              {socialLinks.map((item, index) => (
                <a
                  key={index}
                  href={item.path}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3"
                >
                  {item.icon}
                  <span className="text-primary">{item.name}</span>
                </a>
              ))}
            </div>
          </div>
        )}
      </nav>
    </header>
  );
};

export default Header;
