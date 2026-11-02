/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0B0F17',
        surface: '#111827',
        surfaceHover: '#1F2937',
        panel: '#151D2C',
        borderDim: '#1E293B',
        brand: {
          cyan: '#06B6D4',
          emerald: '#10B981',
          violet: '#8B5CF6',
          amber: '#F59E0B',
          rose: '#F43F5E'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
      },
      boxShadow: {
        'glow-cyan': '0 0 20px -5px rgba(6, 182, 212, 0.4)',
        'glow-emerald': '0 0 20px -5px rgba(16, 185, 129, 0.4)',
        'glow-violet': '0 0 20px -5px rgba(139, 92, 246, 0.4)',
      }
    },
  },
  plugins: [],
}

