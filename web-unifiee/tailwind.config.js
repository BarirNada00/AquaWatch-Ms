/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        aqua: {
          primary: '#0ea5e9',
          secondary: '#06b6d4',
          dark: '#0284c7',
          light: '#e0f2fe'
        }
      }
    },
  },
  plugins: [],
}

