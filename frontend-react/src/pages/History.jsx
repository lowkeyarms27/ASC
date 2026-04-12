import { useState, useEffect, useRef } from 'react'
import { getSessions, getResults, getLog, search as searchApi } from '../lib/api'
import { GAME_NAMES, GAME_OPTIONS } from '../lib/constants'
import Analysis from '../components/Analysis'
import Pipeline, { currentStep } from '../components/Pipeline'

const STATUS_COLOR = {
  complete:  'bg-emerald-400',
  failed:    'bg-red-400',
  analysing: 'bg-amber-400 animate-pulse',
  uploading: 'bg-amber-400',
}
const STATUS_LABEL = {
  complete:  'Done',
  failed:    'Failed',
  analysing: 'Live',
  uploading: 'Upload',
}

export default function History() {
  const [sessions, setSessions] = useState([])
  const [selId,    setSelId]    = useState(null)
  const [detail,   setDetail]   = useState(null)
  const [live,     setLive]     = useState({ step: 0, log: [] })
  const [loading,  setLoading]  = useState(true)

  // search
  const [query,    setQuery]    = useState('')
  const [sgame,    setSgame]    = useState('All')
  const [hits,     setHits]     = useState(null)
  const [searching,setSearching]= useState(false)

  const liveRef = useRef(null)

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [])

  async function loadSessions() {
    try {
      const data = await getSessions(100)
      const list = data.sessions || []
      setSessions(list)
      if (!selId && list.length > 0) selectSession(list[0].id, list[0].status)
    } catch(_) {}
    setLoading(false)
  }

  function stopLive() {
    if (liveRef.current) { clearInterval(liveRef.current); liveRef.current = null }
  }

  async function selectSession(id, status) {
    stopLive()
    setSelId(id)
    setDetail(null)
    setLive({ step:0, log:[] })

    if (status === 'complete' || status === 'failed') {
      try {
        const data = await getResults(id)
        setDetail(data)
      } catch(_) {}
    } else if (status === 'analysing' || status === 'uploading') {
      // Poll for live progress
      liveRef.current = setInterval(async () => {
        try {
          const [logRes, statusRes] = await Promise.all([getLog(id), getSessions(100)])
          const ll = logRes.log || []
          setLive({ step: currentStep(ll), log: ll })
          const updated = statusRes.sessions?.find(s => s.id === id)
          if (updated && (updated.status === 'complete' || updated.status === 'failed')) {
            stopLive()
            setSessions(statusRes.sessions || [])
            if (updated.status === 'complete') {
              const data = await getResults(id)
              setDetail(data)
            }
          }
        } catch(_) {}
      }, 2000)
    }
  }

  async function doSearch() {
    if (!query.trim()) return
    setSearching(true)
    try {
      const gf = sgame === 'All' ? null : sgame
      const data = await searchApi(query.trim(), gf, 8)
      setHits(data.results || [])
    } catch(e) {
      setHits([])
    }
    setSearching(false)
  }

  const selSession = sessions.find(s => s.id === selId)

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-black text-slate-50 tracking-tight">History</h1>
        <p className="text-slate-500 text-sm mt-1">Past sessions and semantic mistake search.</p>
      </div>

      {/* Search bar */}
      <div className="flex gap-2 mb-6">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && doSearch()}
          placeholder='"bad rotation when outnumbered"'
          className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-cyan-500 placeholder-slate-600"
        />
        <select
          value={sgame}
          onChange={e => setSgame(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-slate-300 text-sm focus:outline-none focus:border-cyan-500"
        >
          <option value="All">All games</option>
          {GAME_OPTIONS.slice(1,-1).map(g => <option key={g} value={g}>{GAME_NAMES[g]}</option>)}
        </select>
        <button
          onClick={doSearch}
          disabled={searching}
          className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-cyan-400 text-slate-950 font-bold text-sm rounded-xl hover:from-cyan-400 hover:to-cyan-300 disabled:opacity-50 transition-all"
        >
          {searching ? '…' : 'Search'}
        </button>
      </div>

      {/* Search results */}
      {hits !== null && (
        <div className="mb-6">
          {hits.length === 0 ? (
            <div className="text-slate-600 text-sm text-center py-4">No similar mistakes found.</div>
          ) : (
            <div>
              <div className="text-[9.5px] font-bold uppercase tracking-widest text-cyan-400/70 mb-3">
                {hits.length} semantic match{hits.length !== 1 ? 'es' : ''}
              </div>
              <div className="space-y-2">
                {hits.map((h, i) => {
                  const sev = (h.severity || 'minor').toLowerCase()
                  const sevColor = { critical:'text-red-400 bg-red-500/10 border-red-500/20', major:'text-amber-400 bg-amber-500/10 border-amber-500/20', minor:'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' }[sev] || 'text-slate-400 bg-slate-500/10 border-slate-500/20'
                  return (
                    <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-3">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`text-[9px] font-bold uppercase tracking-wider border px-2 py-0.5 rounded ${sevColor}`}>{sev}</span>
                        <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500 border border-slate-700 bg-slate-800 px-2 py-0.5 rounded">
                          {(h.category||'').replace(/-/g,' ')}
                        </span>
                        <span className="ml-auto text-[10px] text-slate-600">
                          {Math.round((h._similarity||0)*100)}% · R{h.round_number} · {GAME_NAMES[h.game]||''}
                        </span>
                      </div>
                      <p className="text-slate-400 text-xs leading-relaxed">
                        {(h.description||'').slice(0,120)}
                      </p>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sessions + detail */}
      {loading ? (
        <div className="text-center py-16 text-slate-600 text-sm">Loading…</div>
      ) : sessions.length === 0 ? (
        <div className="text-center py-20 text-slate-700">
          <div className="text-4xl opacity-10 mb-3">◈</div>
          <div className="text-sm font-semibold">No analyses yet</div>
          <div className="text-xs mt-1">Upload a clip on the Analyze tab.</div>
        </div>
      ) : (
        <div className="grid grid-cols-[280px_1fr] gap-6">
          {/* Session list */}
          <div>
            <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-600 mb-3">Sessions</div>
            <div className="space-y-1.5">
              {sessions.map(s => {
                const dot   = STATUS_COLOR[s.status] || 'bg-slate-600'
                const lbl   = STATUS_LABEL[s.status] || s.status
                const fname = (s.clip_filename || '—').slice(0, 22)
                const gname = (GAME_NAMES[s.game] || '').slice(0, 14)
                const isSel = selId === s.id
                return (
                  <button
                    key={s.id}
                    onClick={() => selectSession(s.id, s.status)}
                    className={`w-full text-left px-3 py-2.5 rounded-xl border transition-all flex items-center gap-2.5 ${
                      isSel
                        ? 'border-cyan-500/40 bg-cyan-500/5'
                        : 'border-slate-800 bg-slate-900 hover:border-slate-700'
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full shrink-0 ${dot}`} />
                    <div className="flex-1 min-w-0">
                      <div className="text-slate-300 text-xs font-semibold truncate">
                        R{s.round_number} — {fname}
                      </div>
                      <div className="text-slate-600 text-[10px] mt-0.5">{lbl} · {gname}</div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Detail panel */}
          <div>
            {!selId && (
              <div className="flex items-center justify-center h-64 text-slate-700 text-sm">
                Select a session
              </div>
            )}

            {selId && selSession?.status === 'failed' && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-2xl px-5 py-4 text-red-400 text-sm">
                Analysis failed: {selSession.error_message || 'Unknown error'}
              </div>
            )}

            {selId && (selSession?.status === 'analysing' || selSession?.status === 'uploading') && (
              <div>
                <Pipeline step={live.step} log={live.log} />
                <div className="text-center text-slate-600 text-xs mt-2">
                  Status: <span className="text-amber-400 font-medium">{selSession.status}</span>
                </div>
              </div>
            )}

            {detail && selSession?.status === 'complete' && (
              <div>
                <div className="mb-5">
                  <div className="text-slate-50 text-base font-bold tracking-tight">
                    R{detail.round_number} — {detail.clip_filename?.slice(0,40) || `Session ${selId}`}
                  </div>
                  <div className="text-slate-500 text-xs mt-0.5">
                    {GAME_NAMES[detail.game]} · {detail.attacking_team} vs {detail.defending_team} · {detail.winner} won
                  </div>
                </div>
                <Analysis data={detail} sid={selId} />
              </div>
            )}

            {selId && !detail && selSession?.status === 'complete' && (
              <div className="text-center py-16 text-slate-600 text-sm">Loading results…</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
