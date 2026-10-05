import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, fetchProducts, formatPrice, placeOrder, type Order, type Product } from '../api'
import { useAuth } from '../auth'
import { MAX_LINE_QUANTITY, useCart } from '../cart'

interface Duplicate {
  message: string
  minutesAgo: number | null
}

function minutesSince(sqliteUtc: unknown): number | null {
  if (typeof sqliteUtc !== 'string') return null
  const then = Date.parse(sqliteUtc.replace(' ', 'T') + 'Z')
  return Number.isNaN(then) ? null : Math.max(0, Math.round((Date.now() - then) / 60000))
}

export default function Cart() {
  const cart = useCart()
  const { user } = useAuth()
  const [products, setProducts] = useState<Map<string, Product> | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [placing, setPlacing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [duplicate, setDuplicate] = useState<Duplicate | null>(null)
  const [order, setOrder] = useState<Order | null>(null)

  useEffect(() => {
    fetchProducts()
      .then((all) => setProducts(new Map(all.map((p) => [p.product_id, p]))))
      .catch((e) => setLoadError(e instanceof ApiError ? e.message : "We couldn't load your bag. Is the backend running?"))
  }, [])

  const rows = useMemo(
    () =>
      cart.lines.flatMap((line) => {
        const product = products?.get(line.product_id)
        if (!product) return []
        const stock = product.inventory.find((s) => s.size === line.size)?.quantity ?? 0
        return [{ line, product, stock }]
      }),
    [cart.lines, products],
  )
  const subtotal = rows.reduce((sum, r) => sum + r.product.price * r.line.quantity, 0)
  const stockProblem = rows.some((r) => r.line.quantity > r.stock)

  async function checkout(confirmDuplicate = false) {
    setPlacing(true) // the button stays disabled until we hear back, so a double-click can't send twice
    setError(null)
    try {
      const placed = await placeOrder(cart.lines, confirmDuplicate)
      setDuplicate(null)
      setOrder(placed)
      cart.clear()
    } catch (e) {
      if (e instanceof ApiError && e.code === 'duplicate_order') {
        setDuplicate({ message: e.message, minutesAgo: minutesSince(e.data?.previous_order_at) })
      } else {
        setError(e instanceof Error ? e.message : 'Checkout failed. Please try again.')
      }
    } finally {
      setPlacing(false)
    }
  }

  if (order) {
    return (
      <section className="section auth">
        <div className="auth-card order-done">
          <p className="eyebrow">Order #{order.order_id}</p>
          <h1>You're all set!</h1>
          <p>
            Thanks for shopping Campus Customs. Your order total is <strong>{formatPrice(order.total)}</strong>.
          </p>
          <ul className="order-lines">
            {order.items.map((i) => (
              <li key={`${i.product_id}-${i.size}`}>
                {i.quantity} × {i.name} ({i.size}) <span>{formatPrice(i.unit_price * i.quantity)}</span>
              </li>
            ))}
          </ul>
          <p className="muted">This is a demo store, so no payment was taken and nothing will ship. Sorry.</p>
          <Link to="/products" className="btn btn-block">
            Keep shopping
          </Link>
        </div>
      </section>
    )
  }

  return (
    <section className="section">
      <div className="page-head">
        <h1>Your bag</h1>
        <p className="muted">
          {user
            ? 'Saved to your account, so it follows you to any device.'
            : 'Saved on this browser, so it will still be here when you come back.'}
        </p>
      </div>

      {loadError && <p className="error">{loadError}</p>}
      {!products && !loadError && <p className="muted">Loading your bag…</p>}

      {products && rows.length === 0 && (
        <div className="empty-bag">
          <p>Your bag is empty. Even our mascot has more layers on.</p>
          <Link to="/products" className="btn">
            Start shopping
          </Link>
        </div>
      )}

      {products && rows.length > 0 && (
        <div className="cart-layout">
          <ul className="cart-lines">
            {rows.map(({ line, product, stock }) => (
              <li key={`${line.product_id}-${line.size}`} className="cart-line">
                <Link to={`/products/${product.product_id}`} className="cart-thumb">
                  <img src={product.image_url} alt={product.name} />
                </Link>
                <div className="cart-line-info">
                  <Link to={`/products/${product.product_id}`} className="cart-line-name">
                    {product.name}
                  </Link>
                  <p className="muted">
                    Size {line.size} · {formatPrice(product.price)} each
                  </p>
                  {line.quantity > stock && (
                    <p className="form-error">
                      {stock === 0 ? 'Now sold out in this size. Please remove it.' : `Only ${stock} left. Please lower the quantity.`}
                    </p>
                  )}
                  <div className="cart-line-actions">
                    <select
                      aria-label={`Quantity for ${product.name}`}
                      value={line.quantity}
                      onChange={(e) => cart.setQuantity(line.product_id, line.size, Number(e.target.value))}
                    >
                      {Array.from({ length: Math.max(line.quantity, Math.min(stock, MAX_LINE_QUANTITY)) }, (_, i) => i + 1).map(
                        (n) => (
                          <option key={n} value={n}>
                            {n}
                          </option>
                        ),
                      )}
                    </select>
                    <button className="link-button" onClick={() => cart.remove(line.product_id, line.size)}>
                      Remove
                    </button>
                  </div>
                </div>
                <p className="cart-line-total">{formatPrice(product.price * line.quantity)}</p>
              </li>
            ))}
          </ul>

          <aside className="cart-summary">
            <h2>Summary</h2>
            <p className="summary-row">
              <span>Items</span>
              <span>{cart.count}</span>
            </p>
            <p className="summary-row total">
              <span>Subtotal</span>
              <span>{formatPrice(subtotal)}</span>
            </p>

            {duplicate ? (
              <div className="duplicate-warning" role="alertdialog" aria-labelledby="dup-title">
                <strong id="dup-title">Already ordered?</strong>
                <p>
                  {duplicate.minutesAgo !== null
                    ? `You ordered these exact items ${duplicate.minutesAgo === 0 ? 'less than a minute' : `${duplicate.minutesAgo} minute${duplicate.minutesAgo === 1 ? '' : 's'}`} ago. `
                    : `${duplicate.message} `}
                  Do you want to place the same order again?
                </p>
                <div className="duplicate-actions">
                  <button className="btn btn-small" onClick={() => checkout(true)} disabled={placing}>
                    Yes, order again
                  </button>
                  <button className="btn btn-small btn-outline" onClick={() => setDuplicate(null)} disabled={placing}>
                    No, cancel
                  </button>
                </div>
              </div>
            ) : user ? (
              <button className="btn btn-block" onClick={() => checkout()} disabled={placing || stockProblem}>
                {placing ? 'Placing order…' : 'Place order'}
              </button>
            ) : (
              <>
                <Link to="/login" state={{ from: '/cart' }} className="btn btn-block">
                  Log in to check out
                </Link>
                <p className="muted small">Your bag comes with you when you log in.</p>
              </>
            )}
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
          </aside>
        </div>
      )}
    </section>
  )
}
