/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Palette ispirata a intelligeo.ch — sobria, professionale
        brand: {
          50:  '#f0f4ff',
          100: '#dce6ff',
          200: '#b9ccff',
          300: '#8aaeff',
          400: '#5585fd',
          500: '#2f5ff5', // accento principale
          600: '#1e44d4',
          700: '#1834ab',
          800: '#192c8c',
          900: '#1a2a6e',
          950: '#111840',
        },
        surface: {
          DEFAULT: '#ffffff',
          muted:   '#f7f8fa',
          subtle:  '#eef1f6',
          border:  '#dde2ec',
        },
        ink: {
          DEFAULT: '#1a1f2e',   // quasi-nero
          muted:   '#4e5668',
          light:   '#8a93a8',
        },
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        panel: '0 1px 4px 0 rgb(0 0 0 / 0.08), 0 4px 16px 0 rgb(0 0 0 / 0.06)',
        card:  '0 1px 3px 0 rgb(0 0 0 / 0.10)',
      },
      borderRadius: {
        xl2: '1rem',
      },
    },
  },
  plugins: [],
}
