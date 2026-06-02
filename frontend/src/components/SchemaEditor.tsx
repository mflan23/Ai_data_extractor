import { useState } from 'react'
import { Loader2, Plus, Save, Trash2 } from 'lucide-react'
import type { FieldType, SchemaField } from '../types'
import { useStore } from '../store/useStore'
import { runExtraction, updateSchema } from '../services/api'

const FIELD_TYPES: FieldType[] = ['string', 'number', 'boolean', 'date', 'list']

const EMPTY_FIELD: SchemaField = { name: '', type: 'string', description: '', required: false }

export default function SchemaEditor() {
  const { schema, setSchema, jobId, setRecords, setJob, job, isBusy, setBusy } = useStore()
  const [fields, setFields] = useState<SchemaField[]>(schema.fields)
  const [instructions, setInstructions] = useState(schema.instructions ?? '')
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const addField = () => setFields((prev) => [...prev, { ...EMPTY_FIELD }])

  const removeField = (i: number) => setFields((prev) => prev.filter((_, idx) => idx !== i))

  const updateField = (i: number, patch: Partial<SchemaField>) =>
    setFields((prev) => prev.map((f, idx) => (idx === i ? { ...f, ...patch } : f)))

  const handleSave = async () => {
    if (!jobId) return
    const newSchema = { fields, instructions }
    setSchema(newSchema)
    await updateSchema(jobId, newSchema)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleExtract = async () => {
    if (!jobId) return
    setError(null)
    setBusy(true)
    try {
      const schema = { fields, instructions }
      setSchema(schema)
      const result = await runExtraction(jobId, schema)
      setRecords(result.records)
      if (job) setJob({ ...job, records: result.records, extraction_schema: schema })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Extraction failed')
    } finally {
      setBusy(false)
    }
  }

  if (!jobId) {
    return (
      <div className="text-center py-20 text-slate-500">
        Upload files first, then define your extraction schema here.
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Schema Editor</h2>

      {/* Fields */}
      <div className="space-y-3">
        {fields.map((field, i) => (
          <div
            key={i}
            className="grid grid-cols-[1fr_120px_1fr_auto_auto] gap-2 items-center bg-white border border-slate-200 rounded-lg p-3 shadow-sm"
          >
            <input
              placeholder="Field name"
              value={field.name}
              onChange={(e) => updateField(i, { name: e.target.value })}
              className="border border-slate-200 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
            <select
              value={field.type}
              onChange={(e) => updateField(i, { type: e.target.value as FieldType })}
              className="border border-slate-200 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            >
              {FIELD_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <input
              placeholder="Description (optional)"
              value={field.description ?? ''}
              onChange={(e) => updateField(i, { description: e.target.value })}
              className="border border-slate-200 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
            <label className="flex items-center gap-1 text-xs text-slate-600 whitespace-nowrap">
              <input
                type="checkbox"
                checked={field.required ?? false}
                onChange={(e) => updateField(i, { required: e.target.checked })}
                className="accent-indigo-600"
              />
              req
            </label>
            <button
              onClick={() => removeField(i)}
              className="text-slate-400 hover:text-red-500 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      <button
        onClick={addField}
        className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
      >
        <Plus className="w-4 h-4" />
        Add field
      </button>

      {/* Extra instructions */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Additional extraction instructions
        </label>
        <textarea
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          rows={3}
          placeholder="e.g. 'Extract one record per invoice line item', 'Dates should be in ISO format'…"
          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
        />
      </div>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
          {error}
        </div>
      )}

      <div className="flex gap-3">
        <button
          onClick={handleSave}
          className="flex-1 py-2 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium flex items-center justify-center gap-2 text-sm transition-colors"
        >
          <Save className="w-4 h-4" />
          {saved ? 'Saved!' : 'Save schema'}
        </button>

        <button
          onClick={handleExtract}
          disabled={isBusy || !fields.some((f) => f.name.trim())}
          className="flex-1 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium flex items-center justify-center gap-2 text-sm transition-colors"
        >
          {isBusy ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Extracting…
            </>
          ) : (
            'Run Extraction'
          )}
        </button>
      </div>
    </div>
  )
}
