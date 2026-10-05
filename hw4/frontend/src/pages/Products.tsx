import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ApiError, fetchProducts, type Product } from '../api'
import { categories, categoryOf } from '../categories'
import { useChatResults } from '../chatResults'
import ProductCard from '../components/ProductCard'

export default function Products() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [params, setParams] = useSearchParams()
  const type = params.get('type') ?? ''
  const query = params.get('q') ?? ''
  // ?view=chat shows the chat agent's latest matches instead of the filtered catalogue.
  const { results: chatResults } = useChatResults()
  const chatView = params.get('view') === 'chat' && chatResults !== null

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch((e) => setError(e instanceof ApiError ? e.message : "We couldn't load the catalogue. Is the backend running?"))
  }, [])

  const visible = useMemo(() => {
    if (!products) return []
    const q = query.trim().toLowerCase()
    return products.filter((p) => {
      if (type && categoryOf(p) !== type) return false
      if (!q) return true
      return [p.name, p.garment_type, p.description, ...p.colors, ...p.search_tags]
        .join(' ')
        .toLowerCase()
        .includes(q)
    })
  }, [products, type, query])

  function update(key: string, value: string) {
    const next = new URLSearchParams(params)
    next.delete('view') // using the filters switches back to the regular catalogue
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }

  return (
    <section className="section">
      <div className="page-head">
        <h1>All Products</h1>
        <p className="muted">Every piece of navy we could get our paws on.</p>
      </div>

      <div className="filters">
        <div className="chips">
          <button className={`chip ${type === '' && !chatView ? 'active' : ''}`} onClick={() => update('type', '')}>
            All
          </button>
          {categories.map((c) => (
            <button
              key={c.key}
              className={`chip ${type === c.key ? 'active' : ''}`}
              onClick={() => update('type', c.key)}
            >
              {c.label}
            </button>
          ))}
        </div>
        <input
          className="search"
          type="search"
          placeholder="Search hoodies, colleges, sports…"
          value={query}
          onChange={(e) => update('q', e.target.value)}
        />
      </div>

      {chatView ? (
        <div className="chat-results" aria-live="polite">
          <div className="chat-results-head">
            <div>
              <p className="eyebrow">💬 From your chat with our assistant</p>
              <h2>{chatResults.title}</h2>
              <p className="muted result-count">
                {chatResults.products.length} {chatResults.products.length === 1 ? 'item' : 'items'}
              </p>
            </div>
            <button className="btn btn-small btn-outline" onClick={() => update('view', '')}>
              Back to all products
            </button>
          </div>
          <div className="product-grid">
            {chatResults.products.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
        </div>
      ) : error ? (
        <p className="error">{error}</p>
      ) : !products ? (
        <p className="muted">Loading the goods…</p>
      ) : (
        <>
          <p className="muted result-count">
            {visible.length} {visible.length === 1 ? 'item' : 'items'}
          </p>
          {visible.length === 0 ? (
            <p>Nothing matches that. Try fewer words, or more navy.</p>
          ) : (
            <div className="product-grid">
              {visible.map((p) => (
                <ProductCard key={p.product_id} product={p} />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  )
}
