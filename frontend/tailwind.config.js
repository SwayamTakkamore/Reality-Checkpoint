/** @type {import('tailwindcss').Config} */
const rgb = (v) => `rgb(var(--${v}) / <alpha-value>)`

export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Semantic tokens, driven by CSS variables so the whole UI
        // flips between the daylight and night palettes.
        canvas: rgb('canvas'),
        'canvas-2': rgb('canvas-2'),
        surface: rgb('surface'),
        'surface-2': rgb('surface-2'),
        'surface-3': rgb('surface-3'),
        line: rgb('line'),
        'line-strong': rgb('line-strong'),
        ink: rgb('ink'),
        'ink-2': rgb('ink-2'),
        'ink-3': rgb('ink-3'),
        pine: rgb('pine'),
        sage: rgb('sage'),
        moss: rgb('moss'),
        'moss-deep': rgb('moss-deep'),
        amber: rgb('amber'),
        'amber-ink': rgb('amber-ink'),
        track: rgb('track'),

        // Botanical pine / sage moss.
        forest: {
          500: rgb('sage'),
          400: rgb('sage'),
          600: rgb('pine'),
          700: rgb('moss-deep'),
          900: rgb('moss-deep'),
        },
        // Warm paper, now the readable ink scale.
        paper: {
          50: rgb('ink'),
          100: rgb('ink'),
          200: rgb('ink-2'),
          300: rgb('ink-2'),
          400: rgb('ink-3'),
          500: rgb('ink-3'),
        },
        // Obsidian surfaces, now the layered canvas scale.
        obsidian: {
          950: rgb('canvas'),
          900: rgb('surface'),
          850: rgb('surface-2'),
          800: rgb('surface-3'),
          700: rgb('track'),
          600: rgb('scroll'),
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['Newsreader', 'Spectral', 'Georgia', 'ui-serif', 'serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      boxShadow: {
        natural: 'var(--shadow-natural)',
        lift: 'var(--shadow-lift)',
        glow: 'var(--shadow-glow)',
        inner_soft: 'inset 0 1px 0 0 rgb(var(--ink) / 0.04)',
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
