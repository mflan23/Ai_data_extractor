import axios from 'axios'
import type { AgentMessage, ExportFormat, ExtractionJob, ExtractionSchema } from '../types'

const api = axios.create({ baseURL: '/api' })

// ---------- Upload ----------
export async function uploadFiles(files: File[]): Promise<{ job_id: string; files: unknown[] }> {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  const { data } = await api.post('/upload', form)
  return data
}

// ---------- Jobs ----------
export async function getJob(jobId: string): Promise<ExtractionJob> {
  const { data } = await api.get(`/jobs/${jobId}`)
  return data
}

export async function runExtraction(
  jobId: string,
  schema?: ExtractionSchema,
): Promise<{ job_id: string; records: Record<string, unknown>[]; total: number }> {
  const { data } = await api.post(`/jobs/${jobId}/extract`, schema ? { schema } : {})
  return data
}

export async function updateSchema(jobId: string, schema: ExtractionSchema): Promise<void> {
  await api.put(`/jobs/${jobId}/schema`, schema)
}

export async function updateRecords(
  jobId: string,
  records: Record<string, unknown>[],
): Promise<void> {
  await api.patch(`/jobs/${jobId}/records`, records)
}

// ---------- Export ----------
export function buildExportUrl(jobId: string, fmt: ExportFormat): string {
  return `/api/jobs/${jobId}/export/${fmt}`
}

// ---------- Agent ----------
export async function agentChat(
  messages: AgentMessage[],
  jobId?: string,
): Promise<{
  message: AgentMessage
  tool_calls: unknown[]
  updated_schema?: ExtractionSchema
  updated_records?: Record<string, unknown>[]
}> {
  const { data } = await api.post('/agent/chat', { messages, job_id: jobId })
  return data
}
