import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, formatPrice, type Product } from '../api'
import { categories } from '../categories'
import ProductCard from '../components/ProductCard'
import { AlienSprite, PixelHeading, UfoSprite } from '../components/Sprites'

const heroId = 'district-vit-hoodie-vintage-sailor-bulldog'
const featuredIds = [
  'basic-hoodie-big-yale',
  '2025-yale-vs-harvard-t-shirt',
  'berkeley-1-4-zip',
  'brooks-brothers-bomber-jacket-yale',
]

const taglines: Record<string, string> = {
  hoodie: 'Standard-issue crew gear',
  crewneck: 'Blend in with the humans',
  'quarter-zip': 'For first contact (interviews)',
  't-shirt': 'Lightweight atmosphere',
  jacket: 'Rated for New England',
}

// The alien's speech bubble quotes live data, so even the joke is honest about price and stock.
function heroLine(p: Product) {
  const low = p.inventory.filter((s) => s.quantity > 0 && s.quantity <= 5).sort((a, b) => a.quantity - b.quantity)[0]
  return low
    ? `it's ${formatPrice(p.price)}. only ${low.quantity} left in ${low.size}!!`
    : `it's ${formatPrice(p.price)}. abduct one today!!`
}

export default function Home() {
  const [products, setProducts] = useState<Product[]>([])

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setProducts([]))
  }, [])

  const hero = products.find((p) => p.product_id === heroId)
  const featured = featuredIds.map((id) => products.find((p) => p.product_id === id)).filter((p) => p !== undefined)

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <p className="hero-kicker">
            <span className="blink-new">NEW!</span> Fall 2026 shipment has landed
          </p>
          <h1>
            TAKE ME TO
            <br />
            YOUR <span>HOODIE</span>
            <span className="cursor">_</span>
          </h1>
          <p className="hero-sub">
            Bulldog gear, abducted from the finest closets in New Haven and beamed straight to yours. Hoodies,
            crewnecks, and quarter-zips engineered for 8 a.m. lectures and other hostile environments.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-big">
              ► Shop all merch
            </Link>
            <Link to="/products?type=hoodie" className="btn btn-big btn-outline">
              Browse hoodies
            </Link>
          </div>
          <dl className="hero-stats">
            <div>
              <dt>Specimens</dt>
              <dd>{products.length || '…'}</dd>
            </div>
            <div>
              <dt>Sizes</dt>
              <dd>XS–XXL</dd>
            </div>
            <div>
              <dt>Signal</dt>
              <dd>Strong</dd>
            </div>
          </dl>
        </div>

        <div className="stage" aria-hidden={!hero}>
          <UfoSprite size={210} className="stage-ufo" />
          <div className="beam" />
          {hero && (
            <Link to={`/products/${hero.product_id}`} className="stage-item" aria-label={`View ${hero.name}`}>
              <img src={hero.image_url} alt={hero.name} />
            </Link>
          )}
          <AlienSprite size={64} className="stage-alien" />
          {hero && <p className="bubble">{heroLine(hero)}</p>}
          {hero && (
            <p className="readout">
              SPECIMEN #042
              <br />
              {hero.name.toUpperCase()}
            </p>
          )}
        </div>
      </section>

      <section className="section">
        <PixelHeading>SHOP BY LAYER</PixelHeading>
        <div className="category-grid">
          {categories.map((c) => (
            <Link key={c.key} to={`/products?type=${c.key}`} className="category-tile">
              <UfoSprite size={40} />
              <span>
                <strong>{c.label}</strong>
                <small>{taglines[c.key]}</small>
              </span>
            </Link>
          ))}
        </div>
      </section>

      {featured.length > 0 && (
        <section className="section">
          <PixelHeading>MOST ABDUCTED</PixelHeading>
          <div className="product-grid">
            {featured.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
          <p className="center">
            <Link to="/products" className="btn btn-big">
              ► See all {products.length} items
            </Link>
          </p>
        </section>
      )}

      <section className="section">
        <div className="promo">
          <AlienSprite size={72} />
          <div>
            <h2>Not sure what size you are?</h2>
            <p>
              BulldogBot scans live inventory for price, sizes, and stock. Open a channel with the big green button in
              the corner. (It only talks merch. It's not doing your p-set.)
            </p>
          </div>
        </div>
      </section>
    </>
  )
}
