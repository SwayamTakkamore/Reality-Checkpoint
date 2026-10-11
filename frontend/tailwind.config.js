/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Obsidian: the night the checkpoint opens into.
        obsidian: {
          950: '#070a09',
          900: '#0b0f0e',
          850: '#101614',
          800: '#161d1a',
          700: '#1e2724',
          600: '#2a3531',
        },
        // Forest green: the world outside.
        forest: {
          500: '#3f8f68',
          400: '#4da97c',
          600: '#2f6b4f',
          700: '#245240',
          900: '#12291f',
        },
        // Warm paper: the journal you carry back in.
        paper: {
          50: '#f7f3e9',
          100: '#efe8d8',
          200: '#e2d8c2',
          300: '#cdbfa2',
          400: '#a9977a',
          500: '#8a7a5e',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['Spectral', 'Georgia', 'ui-serif', 'serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(77,169,124,0.18), 0 18px 60px -24px rgba(63,143,104,0.45)',
        inner_soft: 'inset 0 1px 0 0 rgba(255,255,255,0.04)',
      },
      keyframes: {
        breathe: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.55' },
          '50%': { transform: 'scale(1.06)', opacity: '0.9' },
        },
        ripple: {
          '0%': { transform: 'scale(0.82)', opacity: '0.5' },
          '100%': { transform: 'scale(1.5)', opacity: '0' },
        },
        riseIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        breathe: 'breathe 4.5s ease-in-out infinite',
        ripple: 'ripple 3.4s ease-out infinite',
        riseIn: 'riseIn 420ms cubic-bezier(0.22, 1, 0.36, 1) both',
        shimmer: 'shimmer 2.4s linear infinite',
      },
    },
  },
  plugins: [],
}
