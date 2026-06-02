// Mirrors backend models/schemas.py

export type FieldType = 'string' | 'number' | 'boolean' | 'date' | 'list'

export interface SchemaField {
  name: string
  type: FieldType
  description?: string
  required?: boolean
}

export interface ExtractionSchema {
  fields: SchemaField[]
  instructions?: string
}

export type FileStatus = 'pending' | 'processing' | 'done' | 'error'
export type JobStatus = 'created' | 'extracting' | 'done' | 'error'

export interface UploadedFile {
  file_id: string
  filename: string
  content_type: string
  size: number
  status: FileStatus
  raw_text?: string
  error?: string
}

export interface ExtractionJob {
  job_id: string
  status: JobStatus
  files: UploadedFile[]
  extraction_schema: ExtractionSchema
  records: Record<string, unknown>[]
  error?: string
}

export interface AgentMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export type ExportFormat = 'json' | 'jsonl' | 'csv' | 'tsv' | 'xlsx'
