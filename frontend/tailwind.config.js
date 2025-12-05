/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Use CSS variables so we can control colors at runtime and keep
      // consistency between custom CSS and Tailwind utilities.
      colors: {
        'primary': 'var(--color-primary)',
        'secondary': 'var(--color-secondary)',
        'brand': 'var(--color-primary)',
        'accent': 'var(--color-secondary)'
      }
    },
  },
  plugins: [],
}
