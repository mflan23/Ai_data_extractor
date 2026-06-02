import { useState } from 'react'
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table'
import { ArrowUpDown, ChevronLeft, ChevronRight, Pencil, Search, Trash2 } from 'lucide-react'
import { useStore } from '../store/useStore'
import { updateRecords } from '../services/api'

export default function DataTable() {
  const { records, setRecords, jobId, schema } = useStore()
  const [sorting, setSorting] = useState<SortingState>([])
  const [globalFilter, setGlobalFilter] = useState('')
  const [editingCell, setEditingCell] = useState<{ row: number; col: string } | null>(null)
  const [editValue, setEditValue] = useState('')

  if (!jobId) {
    return (
      <div className="text-center py-20 text-slate-500">
        Upload files first to see extracted data here.
      </div>
    )
  }

  if (!records.length) {
    return (
      <div className="text-center py-20 text-slate-500">
        No records yet. Go to the <strong>Schema</strong> tab to define fields, then run extraction.
      </div>
    )
  }

  // Build columns dynamically from schema fields (or from first record keys)
  const colKeys =
    schema.fields.length > 0
      ? schema.fields.map((f) => f.name)
      : Object.keys(records[0] || {})

  const columns: ColumnDef<Record<string, unknown>>[] = colKeys.map((key) => ({
    accessorKey: key,
    header: ({ column }) => (
      <button
        className="flex items-center gap-1 font-semibold text-slate-700 hover:text-indigo-600"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        {key}
        <ArrowUpDown className="w-3 h-3" />
      </button>
    ),
    cell: ({ row, getValue }) => {
      const rowIndex = row.index
      const isEditing = editingCell?.row === rowIndex && editingCell?.col === key
      const value = getValue() as string

      if (isEditing) {
        return (
          <input
            autoFocus
            className="w-full border border-indigo-400 rounded px-1 py-0.5 text-sm outline-none"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={() => commitEdit(rowIndex, key)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') commitEdit(rowIndex, key)
              if (e.key === 'Escape') setEditingCell(null)
            }}
          />
        )
      }

      return (
        <span
          className="block truncate max-w-xs cursor-pointer hover:text-indigo-600"
          title={String(value ?? '')}
          onDoubleClick={() => {
            setEditingCell({ row: rowIndex, col: key })
            setEditValue(String(value ?? ''))
          }}
        >
          {String(value ?? '')}
        </span>
      )
    },
  }))

  // Actions column
  columns.push({
    id: '_actions',
    header: '',
    cell: ({ row }) => (
      <div className="flex gap-1 justify-end">
        <button
          title="Edit row"
          onClick={() => {
            const col = colKeys[0]
            setEditingCell({ row: row.index, col })
            setEditValue(String(row.original[col] ?? ''))
          }}
          className="text-slate-400 hover:text-indigo-500"
        >
          <Pencil className="w-3.5 h-3.5" />
        </button>
        <button
          title="Delete row"
          onClick={() => deleteRow(row.index)}
          className="text-slate-400 hover:text-red-500"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    ),
  })

  function commitEdit(rowIndex: number, col: string) {
    const updated = records.map((r, i) =>
      i === rowIndex ? { ...r, [col]: editValue } : r,
    )
    setRecords(updated)
    if (jobId) updateRecords(jobId, updated).catch(() => {})
    setEditingCell(null)
  }

  function deleteRow(rowIndex: number) {
    const updated = records.filter((_, i) => i !== rowIndex)
    setRecords(updated)
    if (jobId) updateRecords(jobId, updated).catch(() => {})
  }

  const table = useReactTable({
    data: records,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 25 } },
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-800">
          Data Table
          <span className="ml-2 text-sm font-normal text-slate-500">
            {records.length} record{records.length !== 1 ? 's' : ''}
          </span>
        </h2>

        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 w-4 h-4 text-slate-400" />
          <input
            placeholder="Search…"
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="pl-8 pr-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((h) => (
                  <th
                    key={h.id}
                    className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wide"
                  >
                    {flexRender(h.column.columnDef.header, h.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-slate-100">
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="hover:bg-slate-50 transition-colors">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-2 text-slate-700">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-slate-600">
        <span>
          Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="p-1 rounded hover:bg-slate-100 disabled:opacity-40"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="p-1 rounded hover:bg-slate-100 disabled:opacity-40"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
