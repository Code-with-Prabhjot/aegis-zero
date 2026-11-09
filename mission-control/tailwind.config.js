/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080c14",
        surface: "#0f172a",
        surfaceHover: "#1e293b",
        borderDark: "#334155",
        brandCyan: "#06b6d4",
        brandGreen: "#10b981",
        brandRose: "#f43f5e",
        brandAmber: "#f59e0b",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Menlo", "Courier New", "monospace"],
      }
    },
  },
  plugins: [],
};
