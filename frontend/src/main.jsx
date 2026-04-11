import React from "react";
import ReactDOM from "react-dom/client";
import { GoogleOAuthProvider } from "@react-oauth/google";
import App from "./App.jsx";
import "./index.css";

const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    {clientId ? (
      <GoogleOAuthProvider clientId={clientId}>
        <App />
      </GoogleOAuthProvider>
    ) : (
      <div className="mx-auto max-w-lg p-8 text-center">
        <p className="text-rose-300">
          Set <code className="text-slate-300">VITE_GOOGLE_CLIENT_ID</code> in{" "}
          <code className="text-slate-300">frontend/.env</code> (same Web client
          ID as Google Cloud Console).
        </p>
      </div>
    )}
  </React.StrictMode>
);
