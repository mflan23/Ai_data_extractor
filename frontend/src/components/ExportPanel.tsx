import { Download } from 'lucide-react'
import type { ExportFormat } from '../types'
import { useStore } from '../store/useStore'
import { buildExportUrl } from '../services/api'

const FORMATS: { key: ExportFormat; label: string; description: string }[] = [
  { key: 'json', label: 'JSON', description: 'Pretty-printed JSON array' },
  { key: 'jsonl', label: 'JSONL', description: 'Newline-delimited JSON (one object per line)' },
  { key: 'csv', label: 'CSV', description: 'Comma-separated values (UTF-8 with BOM)' },
  { key: 'tsv', label: 'TSV', description: 'Tab-separated values' },
  { key: 'xlsx', label: 'Excel (.xlsx)', description: 'Microsoft Excel workbook' },
]

export default function ExportPanel() {
  const { jobId, records } = useStore()

  if (!jobId) {
    return (
      <div className="text-center py-20 text-slate-500">
        Upload files and run extraction before exporting.
      </div>
    )
  }

  if (!records.length) {
    return (
      <div className="text-center py-20 text-slate-500">
        No records to export yet. Run extraction first.
      </div>
    )
  }

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-800">Export Data</h2>
        <p className="text-sm text-slate-500 mt-1">
          {records.length} record{records.length !== 1 ? 's' : ''} ready to download
        </p>
      </div>

      <div className="space-y-3">
        {FORMATS.map((fmt) => (
          <a
            key={fmt.key}
            href={buildExportUrl(jobId, fmt.key)}
            download
            className="flex items-center justify-between bg-white border border-slate-200 rounded-xl px-5 py-4 shadow-sm hover:border-indigo-400 hover:shadow-md transition-all group"
          >
            <div>
              <p className="font-semibold text-slate-800 group-hover:text-indigo-600 transition-colors">
                {fmt.label}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">{fmt.description}</p>
            </div>
            <Download className="w-5 h-5 text-slate-400 group-hover:text-indigo-500 transition-colors" />
          </a>
        ))}
      </div>
    </div>
  )
}
