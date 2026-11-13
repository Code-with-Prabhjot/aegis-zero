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
        background: "#06040e",
        surface: "#0d081c",
        surfaceHover: "#170e30",
        borderDark: "rgba(168, 85, 247, 0.2)",
        cosmicPurple: "#8b5cf6",
        cosmicFuchsia: "#d946ef",
        cosmicLavender: "#e9d5ff",
        brandCyan: "#22d3ee",
        brandGreen: "#10b981",
        brandRose: "#f43f5e",
        brandAmber: "#f59e0b",
      },
      fontFamily: {
        display: ["Michroma", "Space Grotesk", "sans-serif"],
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "Menlo", "Courier New", "monospace"],
      },
      boxShadow: {
        glass: "0 0 30px rgba(139, 92, 246, 0.08)",
        "glass-glow": "0 0 35px rgba(168, 85, 247, 0.2)",
      },
    },
  },
  plugins: [],
};
