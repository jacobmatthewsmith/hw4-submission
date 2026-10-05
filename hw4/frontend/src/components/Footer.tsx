import { Link } from 'react-router-dom'
import { AlienSprite } from './Sprites'

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div>
          <p className="footer-brand">
            <AlienSprite size={28} /> CAMPUS CUSTOMS
          </p>
          <p>Earth branch: 57 Broadway, New Haven, CT 06511</p>
          <p className="muted">Open whenever the library is. Roughly.</p>
        </div>
        <div>
          <p className="footer-heading">Shop</p>
          <Link to="/products">All Products</Link>
          <Link to="/products?type=hoodie">Hoodies</Link>
          <Link to="/products?type=crewneck">Crewnecks</Link>
          <Link to="/products?type=t-shirt">T-Shirts</Link>
        </div>
        <div>
          <p className="footer-heading">Your stuff</p>
          <Link to="/cart">Your Bag</Link>
          <Link to="/login">Log In</Link>
          <Link to="/signup">Create an Account</Link>
          <Link to="/about">About Us</Link>
        </div>
      </div>
      <div className="footer-retro">
        <p className="webring">
          &lt;&lt; prev · <strong>IVY LEAGUE MERCH WEBRING</strong> · random · next &gt;&gt;
        </p>
        <p>
          You are visitor <span className="counter">0001847</span>
        </p>
        <div className="badges88" aria-hidden="true">
          <span>BEST VIEWED IN NETSCAPE</span>
          <span>Y2K COMPLIANT</span>
          <span>MADE W/ NOTEPAD</span>
        </div>
      </div>
      <p className="footer-legal">
        © 2026 Campus Customs. A fictional store built for a class project. No humans were harmed in the making of these
        crewnecks.
      </p>
    </footer>
  )
}
