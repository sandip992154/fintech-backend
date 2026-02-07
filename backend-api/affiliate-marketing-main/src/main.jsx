import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";
import { FooterObserverProvider } from "./contexts/FooterOnserverContext.jsx";
import axios from "axios";

axios.defaults.baseURL = import.meta.env.VITE_URL || "";
// axios.defaults.headers.common['Authorization'] = AUTH_TOKEN;
axios.defaults.headers.post["Content-Type"] =
  "application/x-www-form-urlencoded";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <FooterObserverProvider>
      <App />
    </FooterObserverProvider>
  </StrictMode>
);
