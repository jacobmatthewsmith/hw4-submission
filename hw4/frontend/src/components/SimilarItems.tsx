import { useEffect, useState } from 'react'
import { fetchSimilar, type Product } from '../api'
import ProductCard from './ProductCard'

// "Items similar to this one": a scrollable row of smaller product cards under the product details.
// Picked by the backend (same category, shared tags and colors, similar price, in stock first).
export default function SimilarItems({ productId }: { productId: string }) {
  const [items, setItems] = useState<Product[]>([])

  useEffect(() => {
    let cancelled = false
    fetchSimilar(productId)
      .then((found) => !cancelled && setItems(found))
      .catch(() => !cancelled && setItems([]))
    return () => {
      cancelled = true
    }
  }, [productId])

  if (items.length === 0) return null

  return (
    <section className="similar" aria-labelledby="similar-heading">
      <h2 id="similar-heading">Items similar to this one</h2>
      <div className="similar-row">
        {items.map((p) => (
          <ProductCard key={p.product_id} product={p} compact />
        ))}
      </div>
    </section>
  )
}
