import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // All tokens resolve through the dual-mode CSS custom properties
        // defined in index.css (`[data-mode='user'|'developer']`); the -rgb
        // channels keep Tailwind opacity modifiers (e.g. /70) working.
        brand: {
          primary: {
            DEFAULT: 'rgb(var(--brand-primary-rgb) / <alpha-value>)',
            light: 'rgb(var(--brand-primary-light-rgb) / <alpha-value>)',
            dim: 'rgb(var(--brand-primary-dim-rgb) / <alpha-value>)',
            deep: 'rgb(var(--brand-primary-deep-rgb) / <alpha-value>)',
            hover: 'rgb(var(--brand-primary-hover-rgb) / <alpha-value>)',
          },
          secondary: {
            DEFAULT: 'rgb(var(--brand-secondary-rgb) / <alpha-value>)',
            dim: 'rgb(var(--brand-secondary-dim-rgb) / <alpha-value>)',
            hover: 'rgb(var(--brand-secondary-hover-rgb) / <alpha-value>)',
          },
        },
        surface: {
          canvas: 'rgb(var(--surface-canvas-rgb) / <alpha-value>)',
          base: 'rgb(var(--surface-base-rgb) / <alpha-value>)',
          elevated: 'rgb(var(--surface-elevated-rgb) / <alpha-value>)',
          overlay: 'rgb(var(--surface-overlay-rgb) / <alpha-value>)',
          border: 'rgb(var(--surface-border-rgb) / <alpha-value>)',
          borderLight: 'rgb(var(--surface-border-light-rgb) / <alpha-value>)',
          muted: 'rgb(var(--surface-muted-rgb) / <alpha-value>)',
          subtle: 'rgb(var(--surface-subtle-rgb) / <alpha-value>)',
        },
        semantic: {
          success: 'rgb(var(--semantic-success-rgb) / <alpha-value>)',
          successDim: 'rgb(var(--semantic-success-dim-rgb) / <alpha-value>)',
          warning: 'rgb(var(--semantic-warning-rgb) / <alpha-value>)',
          warningDim: 'rgb(var(--semantic-warning-dim-rgb) / <alpha-value>)',
          error: 'rgb(var(--semantic-error-rgb) / <alpha-value>)',
          errorDim: 'rgb(var(--semantic-error-dim-rgb) / <alpha-value>)',
          info: 'rgb(var(--semantic-info-rgb) / <alpha-value>)',
          infoDim: 'rgb(var(--semantic-info-dim-rgb) / <alpha-value>)',
          purple: 'rgb(var(--semantic-purple-rgb) / <alpha-value>)',
          purpleDim: 'rgb(var(--semantic-purple-dim-rgb) / <alpha-value>)',
        },
        text: {
          heading: 'rgb(var(--text-heading-rgb) / <alpha-value>)',
          body: 'rgb(var(--text-body-rgb) / <alpha-value>)',
          secondary: 'rgb(var(--text-secondary-rgb) / <alpha-value>)',
          disabled: 'rgb(var(--text-disabled-rgb) / <alpha-value>)',
          inverse: 'rgb(var(--text-inverse-rgb) / <alpha-value>)',
          brand: 'rgb(var(--text-brand-rgb) / <alpha-value>)',
          accent: 'rgb(var(--text-accent-rgb) / <alpha-value>)',
        },
      },
      borderRadius: {
        xs: '4px',
        sm: '6px',
        md: '8px',
        lg: '12px',
        xl: '16px',
        full: '9999px',
      },
      boxShadow: {
        sm: '0 1px 3px rgba(0,0,0,0.4)',
        md: '0 4px 16px rgba(0,0,0,0.5)',
        lg: '0 8px 32px rgba(0,0,0,0.6)',
        blue: '0 0 20px rgba(59,110,248,0.25)',
        cyan: '0 0 12px rgba(0,200,232,0.2)',
      },
      fontSize: {
        display: ['48px', { lineHeight: '56px', fontWeight: '700' }],
        h1: ['36px', { lineHeight: '44px', fontWeight: '700' }],
        h2: ['28px', { lineHeight: '36px', fontWeight: '600' }],
        h3: ['20px', { lineHeight: '28px', fontWeight: '600' }],
        'body-lg': ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'body-md': ['14px', { lineHeight: '22px', fontWeight: '400' }],
        label: ['13px', { lineHeight: '20px', fontWeight: '500' }],
        caption: ['11px', { lineHeight: '16px', fontWeight: '400' }],
        mono: ['13px', { lineHeight: '20px', fontWeight: '400' }],
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
        display: ['Space Grotesk', 'Inter', 'ui-sans-serif', 'system-ui'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      letterSpacing: {
        caps: '0.075em',
      },
      spacing: {
        '18': '4.5rem',
      },
    },
  },
  plugins: [],
}

export default config
