import React from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Layout from "./layouts/Layout";
import Home from "./pages/Home";
import ContactUs from "./pages/ContactUs";
import { Compare } from "./pages/Compare";
import "./App.css";
import { Products } from "./pages/Products";
import Category from "./pages/Category";
import NotFound from "./components/NotFound";
import ProductDetails from "./components/product/ProductDetails";
import CompareNowSingle from "./pages/CompareNowSingle";


const App = () => {
  const router = createBrowserRouter([
    {
      path: "/",
      element: <Layout />,
      children: [
        {
          index: true, // for "/"
          element: <Home />,
        },
        {
          path: "category",
          element: <Category />,
        },
        {
          path: "products",
          element: <Products />,
        },
        {
          path: "contact-us",
          element: <ContactUs />,
        },
        {
          path: "compare",
          element: <Compare />,
        },
        {
          path:"CompareNowSingle",
          element: <CompareNowSingle />,
        },
        {
          path: "error",
          element: <NotFound />,
        },
        {
          path: "product/:id",
          element: <ProductDetails />,
        },
        
      ],
    },
  ]);

  return <RouterProvider router={router} />;
};

export default App;
