import { Link } from "react-router-dom";
import { FaInstagram, FaFacebookF, FaYoutube } from "react-icons/fa";
import { useFooterVisible } from "../constants/footerContext";

// ✅ Reusable column for links
const FooterLinkColumn = ({ links }) => (
  <div className="flex flex-col gap-2 text-sm">
    {links.map((link, i) => (
      <Link key={i} to={link.href} className="footer-link">
        {link.label}
      </Link>
    ))}
  </div>
);

const Footer = () => {
  const { footerRef } = useFooterVisible();
  return (
    <footer className="footer  " ref={footerRef}>
      <div className="maxscreen  screen-margin px-4 sm:px-10 md:px-20 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-8">
        {/* Brand Info */}
        <div className="md:col-span-1">
          <h2 className="text-white text-xl font-bold">Daam Dekho</h2>
          <p className="text-customGray text-sm mt-1">
            Compare Prices. Save Big.
          </p>
        </div>

        {/* Navigation Columns */}
        <div>
          <FooterLinkColumn
            links={[
              { label: "Home", href: "/" },
              { label: "Category", href: "/category" },
              // { label: "Compare", href: "/compare" },
            ]}
          />
        </div>

        <div>
          <FooterLinkColumn
            links={[
              { label: "Contact Us", href: "/contact" },
              { label: "More", href: "/more" },
            ]}
          />
        </div>

        {/* Newsletter */}
        <div className="sm:col-span-2 md:col-span-2">
          <h3 className="text-white font-semibold mb-2">Newsletter</h3>
          <div className="flex flex-col sm:flex-row md:flex-col lg:flex-row  items-center gap-2 w-full">
            <input
              type="email"
              placeholder="Enter your email"
              className="w-full px-3 py-2 rounded text-sm ring-1 ring-white "
            />
            <button className="btn-cta py-2 px-5 text-sm xm:shrink-0 w-full xm:min-w-[120px]">
              Sign Up
            </button>
          </div>

          <p className="text-xs mt-2 text-customGray">
            By clicking Sign Up you're confirming that you agree with our{" "}
            <Link to="/terms" className="underline">
              Terms and Conditions
            </Link>
            .
          </p>
        </div>
      </div>

      {/* Bottom Section */}
      <div className=" maxscreen screen-margin mt-10 border-t border-gray-700 pt-4 px-4 flex flex-col md:flex-row md:justify-between items-center gap-4 text-sm">
        <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-4 text-customWhite text-center md:text-left">
          <p>© 2025 Daam Dekho. All rights reserved.</p>
          <div className="flex gap-4 justify-center">
            <Link to="/privacy-policy" className="footer-link">
              Privacy Policy
            </Link>
            <Link to="/terms-of-use" className="footer-link">
              Terms of Use
            </Link>
          </div>
        </div>
        <div className="flex gap-4 text-primary justify-center">
          {[FaInstagram, FaFacebookF, FaYoutube].map((Icon, i) => (
            <Icon key={i} className="cursor-pointer text-lg" />
          ))}
        </div>
      </div>
    </footer>
  );
};

export default Footer;
