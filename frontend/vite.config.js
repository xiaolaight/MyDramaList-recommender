import path from "path";
import { fileURLToPath } from "url";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..");

function pickGoogleClientId(rootEnv, feEnv) {
  const raw =
    feEnv.VITE_GOOGLE_CLIENT_ID ||
    rootEnv.VITE_GOOGLE_CLIENT_ID ||
    rootEnv.GOOGLE_CLIENT_ID ||
    rootEnv.client_id ||
    "";
  return String(raw).trim().replace(/^["']|["']$/g, "");
}

export default defineConfig(({ mode }) => {
  const rootEnv = loadEnv(mode, projectRoot, "");
  const feEnv = loadEnv(mode, __dirname, "");
  const googleClientId = pickGoogleClientId(rootEnv, feEnv);

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
