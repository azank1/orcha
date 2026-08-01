import { cn } from './cn'

interface LogoProps {
  readonly size?: number
  readonly className?: string
}

/** Orcha prismatic hexagon logo (inline SVG, no external fetch) */
export function Logo({ size = 32, className }: LogoProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 64 64"
      fill="none"
      width={size}
      height={size}
      className={cn('shrink-0', className)}
      aria-label="Orcha logo"
    >
      {/* Six triangular facets — blue-cyan prismatic spectrum */}
      <polygon points="32,32 32,10 51.1,21"   fill="#4A7FFA" />
      <polygon points="32,32 51.1,21 51.1,43" fill="#6366F1" />
      <polygon points="32,32 51.1,43 32,54"   fill="#2352D4" />
      <polygon points="32,32 32,54 12.9,43"   fill="#0A7A9C" />
      <polygon points="32,32 12.9,43 12.9,21" fill="#009BB8" />
      <polygon points="32,32 12.9,21 32,10"   fill="#A5A8FF" />

      {/* Seam lines */}
      <g stroke="rgba(7,7,12,0.4)" strokeWidth="0.5" strokeLinecap="round">
        <line x1="32" y1="32" x2="32"   y2="10" />
        <line x1="32" y1="32" x2="51.1" y2="21" />
        <line x1="32" y1="32" x2="51.1" y2="43" />
        <line x1="32" y1="32" x2="32"   y2="54" />
        <line x1="32" y1="32" x2="12.9" y2="43" />
        <line x1="32" y1="32" x2="12.9" y2="21" />
      </g>

      {/* Outer hex border */}
      <polygon
        points="32,10 51.1,21 51.1,43 32,54 12.9,43 12.9,21"
        fill="none"
        stroke="rgba(255,255,255,0.08)"
        strokeWidth="1"
      />

      {/* Center glow — emergent unity */}
      <circle cx="32" cy="32" r="5"   fill="#AECBFD" opacity="0.6" />
      <circle cx="32" cy="32" r="2.5" fill="#D0E8FF" opacity="0.9" />
    </svg>
  )
}
