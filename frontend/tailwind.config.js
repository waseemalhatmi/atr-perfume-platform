/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gold: {
          primary:   '#d4af37',
          secondary: '#f0d060',
          muted:     '#a08820',
        },
        brand: {
          orange: '#e8a020',
        },
        dark: {
          DEFAULT: '#09090b',
          card:    '#18181b',
          border:  '#27272a',
          muted:   '#71717a',
          secondary: '#1e1e24',
        },
      },
      fontFamily: {
        serif: ["'Cormorant Garamond'", 'Georgia', 'serif'],
        sans:  ["'Inter'", 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        sm:   '0.375rem',
        md:   '0.625rem',
        lg:   '1rem',
        xl:   '1.5rem',
        full: '9999px',
      },
      backdropBlur: {
        luxury: '12px',
      },
      animation: {
        'fade-up':        'fadeUp 0.6s cubic-bezier(0.4,0,0.2,1) forwards',
        'skeleton':       'skeleton-shimmer 1.5s infinite',
        'pulse-gold':     'pulseGold 2s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'skeleton-shimmer': {
          '0%':   { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
        pulseGold: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(212,175,55,0)' },
          '50%':      { boxShadow: '0 0 20px 4px rgba(212,175,55,0.3)' },
        },
      },
    },
  },
  plugins: [],
}
