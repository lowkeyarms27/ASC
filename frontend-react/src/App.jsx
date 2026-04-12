import { useState } from 'react'
import Topbar from './components/Topbar'
import AnalyzeClip from './pages/AnalyzeClip'
import History from './pages/History'

const TABS = [
  { id: 'analyze', label: 'Analyze Clip' },
  { id: 'history', label: 'History'      },
]

export default function App() {
  const [tab, setTab] = useState('analyze')

  return (
    <div className="min-h-screen flex flex-col bg-slate-950">
      <Topbar tab={tab} tabs={TABS} onTab={setTab} />
      <main className="flex-1 px-8 py-8 max-w-screen-xl mx-auto w-full">
        {tab === 'analyze' && <AnalyzeClip />}
        {tab === 'history' && <History />}
      </main>
    </div>
  )
}
