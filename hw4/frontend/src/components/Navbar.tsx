import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { useCart } from '../cart'
import { BagSprite, UfoSprite } from './Sprites'

const links = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Shop Merch' },
  { to: '/about', label: 'About Us' },
]

const TICKER =
  '*** WELCOME 2 CAMPUS CUSTOMS *** NEW FALL DROP BEAMED DOWN TO 57 BROADWAY *** YOU ARE VISITOR #0001847 *** BEST VIEWED IN NETSCAPE NAVIGATOR 4.0 AT 800x600 *** WE COME IN PEACE (AND IN CREWNECKS) *** BOOLA BOOLA, EARTHLINGS ***'

export default function Navbar() {
  const { user, loading, logout } = useAuth()
  const { count } = useCart()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <header className="site-header">
      <div className="ticker" aria-hidden="true">
        <span>{TICKER}</span>
      </div>
      <nav className="navbar" aria-label="Main">
        <Link to="/" className="brand" aria-label="Campus Customs home">
          <UfoSprite size={52} />
          <span className="brand-name">
            CAMPUS CUSTOMS<small>est. New Haven, Earth</small>
          </span>
        </Link>
        <ul className="nav-links">
          {links.map((l) => (
            <li key={l.to}>
              <NavLink to={l.to} end={l.end}>
                {l.label}
              </NavLink>
            </li>
          ))}
        </ul>
        <div className="nav-account">
          {loading ? null : user ? (
            <>
              <span className="nav-greeting">Hi, {user.first_name || user.name}!</span>
              <button className="btn btn-gray" onClick={handleLogout}>
                Log Out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className="btn btn-gray">
                Log In
              </NavLink>
              <NavLink to="/signup" className="btn btn-outline">
                Create an Account
              </NavLink>
            </>
          )}
          <NavLink to="/cart" className="btn nav-bag" aria-label={`View bag, ${count} item${count === 1 ? '' : 's'}`}>
            <BagSprite />
            Bag
            <span className="bag-count">{count}</span>
          </NavLink>
        </div>
      </nav>
    </header>
  )
}
