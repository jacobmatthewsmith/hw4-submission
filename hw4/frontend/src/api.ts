export interface SizeStock {
  size: string
  quantity: number
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  price: number
  inventory: SizeStock[]
  total_stock: number
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

// Contract for POST /api/chat (backend/models.py ChatResponse / PageResults).
export interface PageResults {
  title: string
  products: Product[]
}

export interface ChatReply {
  reply: string
  results: PageResults | null // null: nothing to show, so leave the page as it is
  stopped_early: boolean // the turn hit its budget; the reply asks the shopper to rephrase
}

// Errors carry the server's friendly `detail` message. For rate limits (429) that message already says
// when to try again (from Retry-After); nothing retries automatically.
export class ApiError extends Error {
  status: number
  code?: string
  retryAfter?: number
  data: Record<string, unknown> | null

  constructor(status: number, message: string, data: Record<string, unknown> | null, retryAfter?: number) {
    super(message)
    this.status = status
    this.data = data
    this.code = typeof data?.code === 'string' ? data.code : undefined
    this.retryAfter = retryAfter
  }
}

async function toApiError(res: Response): Promise<ApiError> {
  const data = await res.json().catch(() => null)
  const message = typeof data?.detail === 'string' ? data.detail : 'Something went wrong. Please try again.'
  const retry = Number(res.headers.get('Retry-After'))
  return new ApiError(res.status, message, data, Number.isFinite(retry) && retry > 0 ? retry : undefined)
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw await toApiError(res)
  return res.json() as Promise<T>
}

async function sendJson<T>(method: 'POST' | 'PUT', url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) throw await toApiError(res)
  return (res.status === 204 ? undefined : res.json()) as Promise<T>
}

export function fetchProducts(query?: string): Promise<Product[]> {
  const params = query ? `?q=${encodeURIComponent(query)}` : ''
  return getJson<Product[]>(`/api/products${params}`)
}

export function fetchProduct(productId: string): Promise<Product> {
  return getJson<Product>(`/api/products/${encodeURIComponent(productId)}`)
}

export interface HistoryMessage extends ChatTurn {
  results: PageResults | null
  created_at: string
}

// Sends a message to the Pydantic AI shopping agent, with the page the shopper is on.
// `history` is only used for guests; logged-in history is loaded from the database server-side.
export function sendChat(message: string, history: ChatTurn[], pagePath: string): Promise<ChatReply> {
  return sendJson<ChatReply>('POST', '/api/chat', { message, history, page: { path: pagePath } })
}

export const formatPrice = (price: number) => `$${price.toFixed(2)}`

// --- Accounts ---------------------------------------------------------------

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  name: string
}

export interface SignupData {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

// The session lives in an HttpOnly cookie set by the backend, so there's no token to store here.
const postJson = <T,>(url: string, body?: unknown) => sendJson<T>('POST', url, body)

export const signup = (data: SignupData) => postJson<User>('/api/auth/signup', data)
export const login = (email: string, password: string) => postJson<User>('/api/auth/login', { email, password })
export const logout = () => postJson<void>('/api/auth/logout')

export async function fetchCurrentUser(): Promise<User | null> {
  const res = await fetch('/api/auth/me')
  return res.ok ? (res.json() as Promise<User>) : null
}

// The logged-in customer's saved chat (empty for guests).
export function fetchChatHistory(): Promise<HistoryMessage[]> {
  return getJson<HistoryMessage[]>('/api/chat/history')
}

export function fetchSimilar(productId: string): Promise<Product[]> {
  return getJson<Product[]>(`/api/products/${encodeURIComponent(productId)}/similar`)
}

// --- Cart and orders --------------------------------------------------------

export interface CartLine {
  product_id: string
  size: string
  quantity: number
}

export interface Order {
  order_id: number
  total: number
  created_at: string
  items: (CartLine & { name: string; unit_price: number })[]
}

export const fetchCart = () => getJson<{ items: CartLine[] }>('/api/cart').then((r) => r.items)
export const saveCart = (items: CartLine[]) => sendJson<{ items: CartLine[] }>('PUT', '/api/cart', { items }).then((r) => r.items)
export const mergeCart = (items: CartLine[]) =>
  sendJson<{ items: CartLine[] }>('POST', '/api/cart/merge', { items }).then((r) => r.items)

// Throws ApiError with code "duplicate_order" (409) if an identical order was placed in the last 5 minutes;
// call again with confirmDuplicate=true once the shopper confirms.
export const placeOrder = (items: CartLine[], confirmDuplicate = false) =>
  sendJson<Order>('POST', '/api/orders', { items, confirm_duplicate: confirmDuplicate })
