import type { Config } from 'tailwindcss'

// Color tokens + xl radius ported verbatim from frontend/tailwind.config.ts.
// The canvas components reference surface-*/semantic-*/text-*/brand-primary
// classes — without these tokens every such class renders as nothing.
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
          canvas: '#07070C',
          base: '#0D0D14',
          elevated: '#13131E',
          overlay: '#1A1A28',
          border: '#252535',
          borderLight: '#333348',
          muted: '#4A4A6A',
          subtle: '#6B6B8F',
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
          secondary: '#8888AA',
          disabled: '#4A4A6A',
          inverse: '#07070C',
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
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}

export default config
