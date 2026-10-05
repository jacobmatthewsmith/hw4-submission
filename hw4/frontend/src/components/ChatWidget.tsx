import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ApiError, fetchChatHistory, formatPrice, sendChat, type PageResults, type User } from '../api'
import { useAuth } from '../auth'
import { CHAT_RESULTS_PATH, useChatResults } from '../chatResults'
import { AlienSprite } from './Sprites'

interface Message {
  role: 'user' | 'assistant'
  content: string
  results?: PageResults
}

// The opening bubble is shown locally and never sent to the agent or saved.
function greetingFor(user: User | null, returning: boolean): Message {
  if (!user) {
    return {
      role: 'assistant',
      content:
        "Hi! I'm the Campus Customs assistant. Ask me about hoodies, sizes, or what goes with navy. (Spoiler: navy.)",
    }
  }
  return {
    role: 'assistant',
    content: returning
      ? `Welcome back, ${user.first_name}! Here's where we left off.`
      : `Hi ${user.first_name}! I'm the Campus Customs assistant. Ask me about hoodies, sizes, or anything on the page.`,
  }
}

// Seed history contains **bold** markdown; the panel shows plain text.
const plain = (text: string) => text.replace(/\*\*(.+?)\*\*/g, '$1')

const PREVIEW_COUNT = 3 // product links shown inside the chat bubble; the full set goes to the page

export default function ChatWidget() {
  const { user, loading } = useAuth()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([greetingFor(null, false)])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const { setResults } = useChatResults()
  const navigate = useNavigate()
  const location = useLocation()
  // Which conversation is showing: a user id or 'guest'. Replies that arrive after the
  // shopper logs in or out belong to the old conversation and are dropped.
  const sessionKey = loading ? null : (user?.id ?? 'guest')
  const sessionRef = useRef(sessionKey)

  // Load the right conversation whenever the logged-in user changes (login, logout, page load).
  useEffect(() => {
    sessionRef.current = sessionKey
    if (sessionKey === null) return
    if (!user) {
      setMessages([greetingFor(null, false)])
      setResults(null)
      return
    }
    let cancelled = false
    fetchChatHistory()
      .then((history) => {
        if (cancelled) return
        const saved: Message[] = history.map((m) => ({ role: m.role, content: m.content, results: m.results ?? undefined }))
        setMessages([greetingFor(user, saved.length > 0), ...saved])
      })
      .catch(() => !cancelled && setMessages([greetingFor(user, false)]))
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionKey])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open])

  // Put the agent's matches on the page, as if the shopper had searched for them.
  function showOnPage(results: PageResults) {
    setResults(results)
    const viewingOnlyThisItem =
      results.products.length === 1 && location.pathname === `/products/${results.products[0].product_id}`
    if (!viewingOnlyThisItem) navigate(CHAT_RESULTS_PATH)
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return
    // Guests: earlier turns give the agent context ("what about in medium?"); the greeting is skipped.
    // Logged-in customers: the server uses their saved history instead.
    const history = messages.slice(1).map(({ role, content }) => ({ role, content }))
    const sentFrom = sessionRef.current
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: text }])
    setSending(true)
    try {
      const res = await sendChat(text, history, location.pathname)
      if (sessionRef.current !== sentFrom) return
      setMessages((m) => [...m, { role: 'assistant', content: res.reply, results: res.results ?? undefined }])
      if (res.results) showOnPage(res.results)
    } catch (err) {
      if (sessionRef.current !== sentFrom) return
      // Server messages (incl. 429 "try again in N seconds") are shown as-is; nothing retries automatically.
      const detail = err instanceof ApiError ? err.message : null
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: detail ?? "Sorry, I can't reach the store right now. Is the backend running?" },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="chat-widget">
      {open && (
        <section className="chat-panel" aria-label="Shopping assistant">
          <header className="chat-header">
            <span className="chat-title">
              <AlienSprite size={18} /> BULLDOGBOT.EXE
            </span>
            <span className="chat-sub">Scans live stock · merch questions only</span>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </header>
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg chat-msg-${m.role}`}>
                <b className="chat-who">{m.role === 'user' ? 'you:' : 'BulldogBot:'}</b>
                <p>{plain(m.content)}</p>
                {m.results && (
                  <div className="chat-products">
                    {m.results.products.slice(0, PREVIEW_COUNT).map((p) => (
                      <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-product">
                        <img src={p.image_url} alt="" />
                        <span>{p.name}</span>
                        <span>{formatPrice(p.price)}</span>
                      </Link>
                    ))}
                    <button className="chat-show-all" onClick={() => showOnPage(m.results!)}>
                      {m.results.products.length > PREVIEW_COUNT
                        ? `See all ${m.results.products.length} on the page →`
                        : 'Show on the page →'}
                    </button>
                  </div>
                )}
              </div>
            ))}
            {sending && <div className="chat-typing">BulldogBot is scanning the inventory…</div>}
            <div ref={bottomRef} />
          </div>
          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about merch…"
              aria-label="Message"
              maxLength={500}
            />
            <button type="submit" className="btn" disabled={sending || !input.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        className={`chat-toggle ${open ? 'is-open' : ''}`}
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Chat with BulldogBot'}
        aria-expanded={open}
      >
        <AlienSprite size={34} />
        <span>{open ? 'Close chat' : 'Chat with BulldogBot'}</span>
      </button>
    </div>
  )
}
