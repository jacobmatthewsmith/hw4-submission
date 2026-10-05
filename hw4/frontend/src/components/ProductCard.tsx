import { Link } from 'react-router-dom'
import { formatPrice, type Product } from '../api'

// `compact` is the smaller version used in the "similar items" row (no description).
export default function ProductCard({ product, compact = false }: { product: Product; compact?: boolean }) {
  const soldOut = product.total_stock === 0
  return (
    <Link to={`/products/${product.product_id}`} className={`product-card ${compact ? 'compact' : ''}`}>
      <div className="product-card-image">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {soldOut && <span className="badge">Sold out</span>}
      </div>
      <div className="product-card-body">
        <h3>{product.name}</h3>
        <p className="price">{formatPrice(product.price)}</p>
        {!compact && <p className="product-card-desc">{product.description}</p>}
      </div>
    </Link>
  )
}
