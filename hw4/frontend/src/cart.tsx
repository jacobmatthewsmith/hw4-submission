import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import * as api from './api'
import { useAuth } from './auth'

// Saved cart (Problem 9).
// - Guests: the cart is kept in this browser's localStorage, so it's still there when they come back.
// - Logged in: the cart is saved on the server (cart_items table), so it follows the account to any device.
//   On login, anything in the guest cart is merged into the account's cart, and the guest copy is cleared.

const GUEST_KEY = 'cc_cart_guest'
export const MAX_LINE_QUANTITY = 10

type CartLine = api.CartLine

function readGuestCart(): CartLine[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(GUEST_KEY) ?? '[]')
    return Array.isArray(parsed) ? parsed.filter((l) => l && typeof l.product_id === 'string' && l.quantity > 0) : []
  } catch {
    return []
  }
}

const writeGuestCart = (lines: CartLine[]) => localStorage.setItem(GUEST_KEY, JSON.stringify(lines))

interface CartState {
  lines: CartLine[]
  count: number
  ready: boolean
  add: (productId: string, size: string, quantity: number) => void
  setQuantity: (productId: string, size: string, quantity: number) => void
  remove: (productId: string, size: string) => void
  clear: () => void
}

const CartContext = createContext<CartState | null>(null)

const same = (l: CartLine, productId: string, size: string) => l.product_id === productId && l.size === size

export function CartProvider({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const [lines, setLines] = useState<CartLine[]>(readGuestCart)
  const [ready, setReady] = useState(false)
  // The cart owner the current `lines` belong to; saves are skipped while switching owners.
  const owner = useRef<number | 'guest' | null>(null)

  // Load the right cart whenever the logged-in user changes.
  useEffect(() => {
    if (loading) return
    const next = user?.id ?? 'guest'
    if (owner.current === next) return
    owner.current = null
    setReady(false)
    if (next === 'guest') {
      owner.current = 'guest'
      setLines(readGuestCart())
      setReady(true)
      return
    }
    const guestLines = readGuestCart()
    const load = guestLines.length ? api.mergeCart(guestLines) : api.fetchCart()
    load
      .then((serverLines) => {
        if (guestLines.length) writeGuestCart([])
        owner.current = next
        setLines(serverLines)
      })
      .catch(() => {
        owner.current = next
        setLines([])
      })
      .finally(() => setReady(true))
  }, [user, loading])

  // Persist every change to wherever this cart lives.
  useEffect(() => {
    if (!ready || owner.current === null) return
    if (owner.current === 'guest') {
      writeGuestCart(lines)
      return
    }
    const timer = setTimeout(() => api.saveCart(lines).catch(() => {}), 300)
    return () => clearTimeout(timer)
  }, [lines, ready])

  const value: CartState = {
    lines,
    ready,
    count: lines.reduce((n, l) => n + l.quantity, 0),
    add: (productId, size, quantity) =>
      setLines((ls) =>
        ls.some((l) => same(l, productId, size))
          ? ls.map((l) =>
              same(l, productId, size) ? { ...l, quantity: Math.min(l.quantity + quantity, MAX_LINE_QUANTITY) } : l,
            )
          : [...ls, { product_id: productId, size, quantity: Math.min(quantity, MAX_LINE_QUANTITY) }],
      ),
    setQuantity: (productId, size, quantity) =>
      setLines((ls) =>
        ls.map((l) => (same(l, productId, size) ? { ...l, quantity: Math.max(1, Math.min(quantity, MAX_LINE_QUANTITY)) } : l)),
      ),
    remove: (productId, size) => setLines((ls) => ls.filter((l) => !same(l, productId, size))),
    clear: () => setLines([]),
  }

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart() {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart must be used inside <CartProvider>')
  return ctx
}
