import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: {
            DEFAULT: '#3B6EF8',
            light: '#6B93FA',
            dim: '#0A1F3D',
            deep: '#060F3A',
            hover: '#2251D6',
          },
          secondary: {
            DEFAULT: '#00C8E8',
            dim: '#002A30',
            hover: '#009BB8',
          },
        },
        surface: {
          canvas: '#09090B',
          base: '#121214',
          elevated: '#18181B',
          overlay: '#1F1F23',
          border: '#27272A',
          borderLight: '#3F3F46',
          muted: '#52525B',
          subtle: '#71717A',
        },
        semantic: {
          success: '#22C55E',
          successDim: '#052E16',
          warning: '#F59E0B',
          warningDim: '#1C1400',
          error: '#EF4444',
          errorDim: '#2D0A0A',
          info: '#3B82F6',
          infoDim: '#0A1F3D',
          purple: '#A78BFA',
          purpleDim: '#1A0A3D',
        },
        text: {
          heading: '#EEEEF2',
          body: '#C4C4D4',
          secondary: '#9CA3AF',
          disabled: '#52525B',
          inverse: '#09090B',
          brand: '#3B6EF8',
          accent: '#00C8E8',
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
