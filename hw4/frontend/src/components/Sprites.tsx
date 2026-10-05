import type { ReactNode } from 'react'

// Pixel-art clipart for the Y2K alien theme (Problem 10). Drawn as crisp SVG rectangles so they
// scale without blurring and need no image files.

type SpriteProps = { size?: number; className?: string; title?: string }

function a11y(title?: string) {
  return title ? { role: 'img', 'aria-label': title } : { 'aria-hidden': true }
}

export function UfoSprite({ size = 48, className = '', title }: SpriteProps) {
  return (
    <svg className={`sprite ${className}`} width={size} height={(size * 9) / 16} viewBox="0 0 16 9" {...a11y(title)}>
      <rect x="6" y="0" width="4" height="1" fill="#9fffb0" />
      <rect x="5" y="1" width="6" height="1" fill="#39ff5a" />
      <rect x="4" y="2" width="8" height="2" fill="#39ff5a" />
      <rect x="6" y="2" width="1" height="1" fill="#eaffee" />
      <rect x="1" y="4" width="14" height="1" fill="#c9d1cb" />
      <rect x="0" y="5" width="16" height="2" fill="#8d998f" />
      <rect x="1" y="7" width="14" height="1" fill="#46524a" />
      {[2, 8, 13].map((x) => (
        <rect key={x} x={x} y="5" width="1" height="1" fill="#c8ff3a" />
      ))}
      {[5, 11].map((x) => (
        <rect key={x} x={x} y="6" width="1" height="1" fill="#c8ff3a" />
      ))}
      <rect x="4" y="8" width="2" height="1" fill="#1fbf45" />
      <rect x="10" y="8" width="2" height="1" fill="#1fbf45" />
    </svg>
  )
}

export function AlienSprite({ size = 48, className = '', title }: SpriteProps) {
  return (
    <svg className={`sprite ${className}`} width={size} height={size} viewBox="0 0 12 12" {...a11y(title)}>
      <rect x="3" y="0" width="6" height="1" fill="#39ff5a" />
      <rect x="2" y="1" width="8" height="1" fill="#39ff5a" />
      <rect x="1" y="2" width="10" height="4" fill="#39ff5a" />
      <rect x="2" y="3" width="3" height="2" fill="#000" />
      <rect x="7" y="3" width="3" height="2" fill="#000" />
      <rect x="2" y="3" width="1" height="1" fill="#fff" />
      <rect x="7" y="3" width="1" height="1" fill="#fff" />
      <rect x="2" y="6" width="8" height="1" fill="#39ff5a" />
      <rect x="3" y="7" width="6" height="1" fill="#22c445" />
      <rect x="5" y="7" width="2" height="1" fill="#0b5a1a" />
      <rect x="4" y="8" width="4" height="1" fill="#22c445" />
      <rect x="2" y="9" width="8" height="3" fill="#00366b" />
      <rect x="4" y="10" width="4" height="1" fill="#fff" />
      <rect x="1" y="10" width="1" height="2" fill="#39ff5a" />
      <rect x="10" y="10" width="1" height="2" fill="#39ff5a" />
    </svg>
  )
}

// Pixel shopping bag for the cart button.
export function BagSprite({ size = 22, className = '' }: SpriteProps) {
  return (
    <svg className={`sprite ${className}`} width={size} height={size} viewBox="0 0 10 10" aria-hidden>
      <rect x="3" y="0" width="4" height="1" fill="currentColor" />
      <rect x="2" y="1" width="1" height="2" fill="currentColor" />
      <rect x="7" y="1" width="1" height="2" fill="currentColor" />
      <rect x="0" y="3" width="10" height="7" fill="currentColor" />
      <rect x="1" y="4" width="8" height="5" fill="#39ff5a" />
      <rect x="3" y="5" width="1" height="1" fill="currentColor" />
      <rect x="6" y="5" width="1" height="1" fill="currentColor" />
    </svg>
  )
}

// A section heading flanked by little aliens, like a 1999 <hr>.
export function PixelHeading({ children, as: Tag = 'h2' }: { children: ReactNode; as?: 'h1' | 'h2' }) {
  return (
    <div className="pixel-heading">
      <AlienSprite size={26} />
      <Tag>{children}</Tag>
      <AlienSprite size={26} />
    </div>
  )
}
