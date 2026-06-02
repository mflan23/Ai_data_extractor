import { useRef, useState } from 'react'
import { Loader2, Send } from 'lucide-react'
import type { AgentMessage } from '../types'
import { useStore } from '../store/useStore'
import { agentChat } from '../services/api'

export default function AiAgent() {
  const { messages, addMessage, jobId, setSchema, setRecords, setBusy, isBusy } = useStore()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const send = async () => {
    const text = input.trim()
    if (!text || isBusy) return

    const userMsg: AgentMessage = { role: 'user', content: text }
    addMessage(userMsg)
    setInput('')
    setBusy(true)

    try {
      // Send all messages (including the one just added) to the agent
      const allMessages = [...messages, userMsg]
      const result = await agentChat(allMessages, jobId ?? undefined)

      addMessage(result.message)

      // Apply schema / record updates from tool calls
      if (result.updated_schema) {
        setSchema(result.updated_schema)
      }
      if (result.updated_records) {
        setRecords(result.updated_records)
      }
    } catch (err: unknown) {
      addMessage({
        role: 'assistant',
        content: `⚠️ Error: ${err instanceof Error ? err.message : 'Something went wrong'}`,
      })
    } finally {
      setBusy(false)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] max-w-2xl mx-auto">
      <h2 className="text-xl font-semibold text-slate-800 mb-4">AI Agent</h2>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap shadow-sm
                ${msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-sm'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-bl-sm'
                }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {isBusy && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-sm px-4 py-3 text-slate-500 text-sm flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Thinking…
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="mt-4 flex gap-2">
        <textarea
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask the AI agent anything… (Enter to send, Shift+Enter for newline)"
          className="flex-1 border border-slate-200 rounded-xl px-4 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
        <button
          onClick={send}
          disabled={!input.trim() || isBusy}
          className="self-end px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
