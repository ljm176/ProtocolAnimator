/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          0: '#0a0d0a',
          1: '#0f140f',
          2: '#131a13',
          3: '#1a231a',
          4: '#212d21',
        },
        edge: {
          DEFAULT: 'rgba(0,255,65,0.08)',
          hover: 'rgba(0,255,65,0.14)',
          active: 'rgba(0,255,65,0.20)',
        },
        text: {
          primary: '#b8f0b8',
          secondary: '#7bc47b',
          tertiary: '#4a8a4a',
          ghost: '#2d5e2d',
        },
        matrix: {
          DEFAULT: '#00ff41',
          dim: '#3ddc84',
          amber: '#e6b800',
          teal: '#00bfa5',
          warm: '#c8a000',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'SF Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
