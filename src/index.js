import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import AppVideo from "./AppVideo";
import "./styles.css";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    {/* <App />     */}
    <AppVideo />
  </React.StrictMode>
);
