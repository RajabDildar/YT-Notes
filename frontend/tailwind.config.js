/** @type {import('tailwindcss').Config} */
export default {
  content: ["./sidepanel.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        yt: {
          red: "#FF0000",
          dark: "#0f0f0f",
          surface: "#1a1a1a",
          border: "#2a2a2a",
          muted: "#aaaaaa",
        },
      },
    },
  },
  plugins: [],
};
