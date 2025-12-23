/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#2E365A",
        secondary: "#6C5E82",
        tertiary: "#AB8BA3",
        accent: "#CA747D",
        background: "#e5e5e5",
        sidebar: "#f8f9fa",
      }
    },
  },
  plugins: [],
}
