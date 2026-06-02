import { BrainCircuit } from 'lucide-react'
import type { AppState } from '../store/useStore'
import { useStore } from '../store/useStore'

const TABS: { key: AppState['activeTab']; label: string }[] = [
  { key: 'upload', label: 'Upload' },
  { key: 'table', label: 'Data Table' },
  { key: 'schema', label: 'Schema' },
  { key: 'agent', label: 'AI Agent' },
  { key: 'export', label: 'Export' },
]

export default function Header() {
  const { activeTab, setActiveTab, jobId } = useStore()

  return (
    <header className="bg-slate-900 text-white shadow-lg">
      <div className="max-w-screen-xl mx-auto px-4 py-3 flex items-center gap-4">
        <div className="flex items-center gap-2 min-w-fit">
          <BrainCircuit className="w-7 h-7 text-indigo-400" />
          <span className="font-bold text-lg tracking-tight">AI Data Extractor</span>
        </div>

        <nav className="flex gap-1 flex-wrap ml-4">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors
                ${activeTab === t.key
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-300 hover:bg-slate-700'
                }`}
            >
              {t.label}
            </button>
          ))}
        </nav>

        {jobId && (
          <span className="ml-auto text-xs text-slate-400 font-mono truncate max-w-[180px]">
            Job: {jobId.slice(0, 8)}…
          </span>
        )}
      </div>
    </header>
  )
}
