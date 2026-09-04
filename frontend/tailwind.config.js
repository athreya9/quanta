/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        quanta: {
          dark: '#0B1020',
          card: '#131B2E',
          elevated: '#1A243B',
          blue: '#2F7BFF',
          gold: '#F5B544',
        }
      }
    },
  },
  plugins: [],
};
