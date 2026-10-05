import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <section className="section">
      <h1>404: This page took a gap year.</h1>
      <p>
        Try the <Link to="/">home page</Link> or browse <Link to="/products">all products</Link>.
      </p>
    </section>
  )
}
