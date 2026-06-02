import { useStore } from './store/useStore'
import Header from './components/Header'
import FileUpload from './components/FileUpload'
import DataTable from './components/DataTable'
import SchemaEditor from './components/SchemaEditor'
import AiAgent from './components/AiAgent'
import ExportPanel from './components/ExportPanel'

function App() {
  const { activeTab } = useStore()

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col">
      <Header />
      <main className="flex-1 max-w-screen-xl mx-auto w-full px-4 py-8">
        {activeTab === 'upload' && <FileUpload />}
        {activeTab === 'table' && <DataTable />}
        {activeTab === 'schema' && <SchemaEditor />}
        {activeTab === 'agent' && <AiAgent />}
        {activeTab === 'export' && <ExportPanel />}
      </main>
    </div>
  )
}

export default App
