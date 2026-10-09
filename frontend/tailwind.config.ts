import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // MemoryLeak brand palette — extended in Phase 11
        brand: {
          50: "#f0f4ff",
          500: "#4f46e5",
          900: "#1e1b4b",
        },
        risk: {
          critical: "#dc2626",
          high: "#ea580c",
          medium: "#ca8a04",
          low: "#16a34a",
          info: "#2563eb",
        },
      },
    },
  },
  plugins: [],
};

export default config;
