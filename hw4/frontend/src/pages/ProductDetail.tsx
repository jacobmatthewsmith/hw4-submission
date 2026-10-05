import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type Product } from '../api'
import { MAX_LINE_QUANTITY, useCart } from '../cart'
import SimilarItems from '../components/SimilarItems'

function stockLabel(quantity: number) {
  if (quantity === 0) return 'Sold out'
  if (quantity <= 5) return `Only ${quantity} left`
  return `${quantity} in stock`
}

export default function ProductDetail() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState(false)
  const [size, setSize] = useState<string | null>(null)
  const [quantity, setQuantity] = useState(1)
  const [added, setAdded] = useState<string | null>(null)
  const cart = useCart()

  useEffect(() => {
    setProduct(null)
    setError(false)
    setSize(null)
    setQuantity(1)
    setAdded(null)
    window.scrollTo(0, 0) // e.g. after clicking a similar item
    fetchProduct(productId)
      .then(setProduct)
      .catch(() => setError(true))
  }, [productId])

  if (error) {
    return (
      <section className="section">
        <h1>We couldn't find that one.</h1>
        <p>
          It may have graduated. <Link to="/products">Back to all products</Link>
        </p>
      </section>
    )
  }
  if (!product) return <section className="section muted">Loading…</section>

  const selected = product.inventory.find((s) => s.size === size)
  const inBag = selected
    ? (cart.lines.find((l) => l.product_id === product.product_id && l.size === selected.size)?.quantity ?? 0)
    : 0
  // Can't add more than is in stock (minus what's already in the bag), or more than 10 per line.
  const maxAddable = selected ? Math.max(0, Math.min(selected.quantity, MAX_LINE_QUANTITY) - inBag) : 0

  function addToBag() {
    if (!selected || maxAddable === 0) return
    const qty = Math.min(quantity, maxAddable)
    cart.add(product!.product_id, selected.size, qty)
    setAdded(`Added ${qty} × ${product!.name} (${selected.size}) to your bag.`)
    setQuantity(1)
  }

  return (
    <section className="section">
      <nav className="breadcrumb">
        <Link to="/products">Products</Link> / <span>{product.name}</span>
      </nav>
      <div className="detail">
        <div className="detail-image">
          <img src={product.image_url} alt={product.name} />
        </div>
        <div className="detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="detail-price">{formatPrice(product.price)}</p>
          <p>{product.description}</p>

          <dl className="detail-meta">
            <dt>Colors</dt>
            <dd className="capitalize">{product.colors.join(', ')}</dd>
            <dt>Availability</dt>
            <dd>
              {product.total_stock > 0 ? `${product.total_stock} in stock across all sizes` : 'Sold out in every size'}
            </dd>
          </dl>

          <h2 className="detail-subhead">Size</h2>
          <div className="sizes">
            {product.inventory.map((s) => (
              <button
                key={s.size}
                className={`size ${size === s.size ? 'active' : ''}`}
                disabled={s.quantity === 0}
                onClick={() => {
                  setSize(s.size)
                  setQuantity(1)
                  setAdded(null)
                }}
                title={stockLabel(s.quantity)}
              >
                {s.size}
              </button>
            ))}
          </div>
          <p className="size-status">
            {selected ? `${selected.size}: ${stockLabel(selected.quantity)}` : 'Pick a size to check stock.'}
            {inBag > 0 && ` · ${inBag} already in your bag`}
          </p>

          <div className="add-to-bag">
            <label className="qty">
              <span>Qty</span>
              <select
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                disabled={!selected || maxAddable === 0}
                aria-label="Quantity"
              >
                {Array.from({ length: Math.max(1, maxAddable) }, (_, i) => i + 1).map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
            <button className="btn add-btn" onClick={addToBag} disabled={!selected || maxAddable === 0}>
              {!selected
                ? 'Select a size'
                : maxAddable === 0
                  ? inBag > 0
                    ? 'Max in your bag'
                    : 'Sold out'
                  : 'Add to bag'}
            </button>
          </div>
          {added && (
            <p className="added-notice" role="status">
              ✓ {added} <Link to="/cart">View bag →</Link>
            </p>
          )}

          <table className="stock-table">
            <thead>
              <tr>
                <th>Size</th>
                <th>Stock</th>
              </tr>
            </thead>
            <tbody>
              {product.inventory.map((s) => (
                <tr key={s.size} className={s.quantity === 0 ? 'sold-out' : ''}>
                  <td>{s.size}</td>
                  <td>{stockLabel(s.quantity)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <SimilarItems productId={product.product_id} />
    </section>
  )
}
