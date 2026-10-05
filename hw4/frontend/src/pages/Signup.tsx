import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const MIN_PASSWORD = 8

export default function Signup() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm_password: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const update = (e: ChangeEvent<HTMLInputElement>) => setForm({ ...form, [e.target.name]: e.target.value })

  const tooShort = form.password.length > 0 && form.password.length < MIN_PASSWORD
  const mismatch = form.confirm_password.length > 0 && form.password !== form.confirm_password
  const matches = form.confirm_password.length > 0 && !mismatch

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (tooShort || mismatch) return
    setError(null)
    setSubmitting(true)
    try {
      await signup(form)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign-up failed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="section auth">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Join the pack</h1>
        <p className="muted">Create an account to save your chats with our shopping assistant.</p>
        <div className="auth-row">
          <label>
            First name
            <input name="first_name" autoComplete="given-name" value={form.first_name} onChange={update} required />
          </label>
          <label>
            Last name
            <input name="last_name" autoComplete="family-name" value={form.last_name} onChange={update} required />
          </label>
        </div>
        <label>
          Email
          <input type="email" name="email" autoComplete="email" value={form.email} onChange={update} required />
        </label>
        <label>
          Password
          <input
            type="password"
            name="password"
            autoComplete="new-password"
            minLength={MIN_PASSWORD}
            value={form.password}
            onChange={update}
            aria-invalid={tooShort}
            required
          />
          <span className={`field-hint ${tooShort ? 'bad' : ''}`}>At least {MIN_PASSWORD} characters.</span>
        </label>
        <label>
          Verify password
          <input
            type="password"
            name="confirm_password"
            autoComplete="new-password"
            value={form.confirm_password}
            onChange={update}
            aria-invalid={mismatch}
            required
          />
          {mismatch && <span className="field-hint bad">Passwords don't match.</span>}
          {matches && <span className="field-hint good">Passwords match ✓</span>}
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="btn btn-block" disabled={submitting || tooShort || mismatch}>
          {submitting ? 'Creating account…' : 'Create Account'}
        </button>
        <p className="auth-switch">
          Already a member? <Link to="/login">Log in</Link>
        </p>
      </form>
    </section>
  )
}
