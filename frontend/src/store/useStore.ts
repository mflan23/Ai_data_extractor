import { create } from 'zustand'
import type { AgentMessage, ExtractionJob, ExtractionSchema } from '../types'

export interface AppState {
  // Current job
  jobId: string | null
  job: ExtractionJob | null
  setJob: (job: ExtractionJob) => void
  clearJob: () => void

  // Schema editor
  schema: ExtractionSchema
  setSchema: (schema: ExtractionSchema) => void

  // Records (editable)
  records: Record<string, unknown>[]
  setRecords: (records: Record<string, unknown>[]) => void

  // Agent conversation
  messages: AgentMessage[]
  addMessage: (msg: AgentMessage) => void
  clearMessages: () => void

  // UI state
  activeTab: 'upload' | 'table' | 'schema' | 'agent' | 'export'
  setActiveTab: (tab: AppState['activeTab']) => void

  isBusy: boolean
  setBusy: (busy: boolean) => void
}

export const useStore = create<AppState>((set) => ({
  jobId: null,
  job: null,
  setJob: (job) => set({ job, jobId: job.job_id, records: job.records, schema: job.extraction_schema }),
  clearJob: () => set({ job: null, jobId: null, records: [], schema: { fields: [] } }),

  schema: { fields: [] },
  setSchema: (schema) => set({ schema }),

  records: [],
  setRecords: (records) => set({ records }),

  messages: [
    {
      role: 'assistant',
      content:
        "Hi! I'm your AI extraction assistant. Upload some files to get started, and I'll help you define a schema and extract structured data.",
    },
  ],
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  clearMessages: () => set({ messages: [] }),

  activeTab: 'upload',
  setActiveTab: (activeTab) => set({ activeTab }),

  isBusy: false,
  setBusy: (isBusy) => set({ isBusy }),
}))
