import { createContext, useContext, useState, type ReactNode } from 'react'
import type { PageResults } from './api'

// The latest product matches from the chat agent. ChatWidget writes them;
// the Products page renders them as cards (at /products?view=chat).
interface ChatResultsState {
  results: PageResults | null
  setResults: (results: PageResults | null) => void
}

const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<PageResults | null>(null)
  return <ChatResultsContext.Provider value={{ results, setResults }}>{children}</ChatResultsContext.Provider>
}

export function useChatResults() {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return ctx
}

export const CHAT_RESULTS_PATH = '/products?view=chat'
