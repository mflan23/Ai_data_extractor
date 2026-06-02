import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { CheckCircle, FileText, Loader2, Upload, XCircle } from 'lucide-react'
import { uploadFiles } from '../services/api'
import { useStore } from '../store/useStore'
import { getJob } from '../services/api'

const ACCEPTED_TYPES: Record<string, string[]> = {
  'application/pdf': ['.pdf'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/tiff': ['.tiff', '.tif'],
  'image/bmp': ['.bmp'],
  'image/webp': ['.webp'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/vnd.ms-excel': ['.xls'],
  'text/csv': ['.csv'],
  'text/tab-separated-values': ['.tsv'],
  'text/plain': ['.txt', '.md'],
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function FileUpload() {
  const { setJob, setActiveTab, setBusy, isBusy } = useStore()
  const [pendingFiles, setPendingFiles] = useState<File[]>([])
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback((accepted: File[]) => {
    setPendingFiles((prev) => [...prev, ...accepted])
    setError(null)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: 50 * 1024 * 1024,
    onDropRejected: (rejected) => {
      const msg = rejected.map((r) => r.errors.map((e) => e.message).join(', ')).join('; ')
      setError(msg)
    },
  })

  const removeFile = (index: number) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (!pendingFiles.length) return
    setBusy(true)
    setError(null)
    try {
      const result = await uploadFiles(pendingFiles)
      const job = await getJob(result.job_id)
      setJob(job)
      setPendingFiles([])
      setActiveTab('schema')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setError(msg)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Upload Files</h2>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 hover:border-indigo-400 hover:bg-slate-50'}`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto mb-3 text-slate-400 w-10 h-10" />
        {isDragActive ? (
          <p className="text-indigo-600 font-medium">Drop files here…</p>
        ) : (
          <>
            <p className="font-medium text-slate-700">Drag & drop files here, or click to select</p>
            <p className="text-sm text-slate-500 mt-1">
              PDF, Word, Excel, CSV, TSV, images (PNG/JPG/TIFF/BMP/WebP), plain text · max 50 MB
            </p>
          </>
        )}
      </div>

      {/* Pending file list */}
      {pendingFiles.length > 0 && (
        <ul className="space-y-2">
          {pendingFiles.map((file, i) => (
            <li
              key={i}
              className="flex items-center justify-between bg-white border border-slate-200 rounded-lg px-4 py-2 shadow-sm"
            >
              <div className="flex items-center gap-2 min-w-0">
                <FileText className="w-4 h-4 text-indigo-500 shrink-0" />
                <span className="text-sm text-slate-700 truncate">{file.name}</span>
                <span className="text-xs text-slate-400 shrink-0">{formatBytes(file.size)}</span>
              </div>
              <button
                onClick={() => removeFile(i)}
                className="text-slate-400 hover:text-red-500 transition-colors ml-2"
              >
                <XCircle className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>
      )}

      {error && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          <XCircle className="w-4 h-4 shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!pendingFiles.length || isBusy}
        className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium flex items-center justify-center gap-2 transition-colors"
      >
        {isBusy ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Uploading & parsing…
          </>
        ) : (
          <>
            <CheckCircle className="w-4 h-4" />
            Upload {pendingFiles.length > 0 ? `${pendingFiles.length} file${pendingFiles.length > 1 ? 's' : ''}` : ''}
          </>
        )}
      </button>
    </div>
  )
}
