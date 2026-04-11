import path from "path";
import { fileURLToPath } from "url";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..");

export default defineConfig(({ mode }) => {
  const rootEnv = loadEnv(mode, projectRoot, "");
  const googleClientId =
    rootEnv.VITE_GOOGLE_CLIENT_ID ||
    rootEnv.GOOGLE_CLIENT_ID ||
    rootEnv.client_id ||
    "";

  return {
    plugins: [react()],
    define: {
      "import.meta.env.VITE_GOOGLE_CLIENT_ID": JSON.stringify(googleClientId),
    },
    server: {
      port: 5173,
      proxy: {
        "/api": "http://127.0.0.1:8000",
      },
    },
  };
});
