import { useState } from 'react'
import { segmentVod } from '../lib/api'
import { GAME_OPTIONS, GAME_NAMES, GAME_TEAMS } from '../lib/constants'

function Label({ children }) {
  return <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500 mb-1.5">{children}</div>
}

function Select({ label, options, nameMap, value, onChange }) {
  return (
    <div>
      {label && <Label>{label}</Label>}
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-cyan-500"
      >
        {options.map(o => <option key={o} value={o}>{nameMap ? nameMap[o] : o}</option>)}
      </select>
    </div>
  )
}

function fmt(s) {
  return `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`
}

export default function FullVOD() {
  const [file,    setFile]    = useState(null)
  const [game,    setGame]    = useState('r6siege')
  const [atk,     setAtk]     = useState('')
  const [def,     setDef]     = useState('')
  const [state,   setState]   = useState('idle')   // idle | loading | done | error
  const [segs,    setSegs]    = useState([])
  const [errMsg,  setErrMsg]  = useState('')

  const [la, lb] = GAME_TEAMS[game] || ['Team A','Team B']

  async function handleDetect() {
    if (!file) return
    setState('loading'); setErrMsg(''); setSegs([])
    try {
      const fd = new FormData()
      fd.append('vod', file)
      fd.append('game', game)
      fd.append('attacking_team', atk || la)
      fd.append('defending_team', def || lb)
      const data = await segmentVod(fd)
      setSegs(data.segments || [])
      setState('done')
    } catch(e) {
      setErrMsg(e.message); setState('error')
    }
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h1 className="text-xl font-black text-slate-50 tracking-tight">Analyze Full VOD</h1>
        <p className="text-slate-500 text-sm mt-1">
          Upload a full match. Gemini detects round boundaries and queues each round for analysis automatically.
        </p>
      </div>

      <div className="space-y-4">
        {/* File drop */}
        <div
          onClick={() => document.getElementById('vod-input').click()}
          className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
            file ? 'border-cyan-500/50 bg-cyan-500/5' : 'border-slate-700 hover:border-slate-500 bg-slate-900/50'
          }`}
        >
          <input
            id="vod-input"
            type="file"
            accept=".mp4,.mkv,.mov"
            className="hidden"
            onChange={e => { if (e.target.files[0]) setFile(e.target.files[0]) }}
          />
          {file ? (
            <div>
              <div className="text-cyan-400 font-semibold text-sm mb-0.5">✓ {file.name}</div>
              <div className="text-slate-500 text-xs">{(file.size / 1048576).toFixed(1)} MB</div>
            </div>
          ) : (
            <div>
              <div className="text-3xl opacity-10 mb-3">▶</div>
              <div className="text-slate-500 text-sm font-medium">Drop full match VOD here</div>
              <div className="text-slate-700 text-xs mt-1">MP4 · MKV · MOV</div>
            </div>
          )}
        </div>

        <Select label="Game" options={GAME_OPTIONS} nameMap={GAME_NAMES} value={game} onChange={setGame} />

        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label>{la}</Label>
            <input
              value={atk} onChange={e => setAtk(e.target.value)}
              placeholder="Team A"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-cyan-500 placeholder-slate-600"
            />
          </div>
          <div>
            <Label>{lb}</Label>
            <input
              value={def} onChange={e => setDef(e.target.value)}
              placeholder="Team B"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-cyan-500 placeholder-slate-600"
            />
          </div>
        </div>

        <button
          onClick={handleDetect}
          disabled={!file || state === 'loading'}
          className="w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-cyan-500 to-cyan-400 text-slate-950 hover:from-cyan-400 hover:to-cyan-300 shadow-[0_4px_20px_rgba(34,211,238,0.25)] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
        >
          {state === 'loading' ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 rounded-full border-2 border-slate-950/30 border-t-slate-950 animate-spin" />
              Detecting rounds…
            </span>
          ) : 'Detect Rounds & Queue Analysis'}
        </button>

        {state === 'error' && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-red-400 text-sm">{errMsg}</div>
        )}

        {state === 'done' && (
          <div className="space-y-3 mt-2">
            <div className="flex items-center justify-between">
              <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500">
                {segs.length} round{segs.length !== 1 ? 's' : ''} detected
              </div>
              <div className="text-xs text-cyan-400/70 font-medium">All queued for analysis</div>
            </div>
            {segs.map(seg => (
              <div key={seg.session_id} className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 flex items-center justify-between">
                <div>
                  <div className="text-slate-200 text-sm font-semibold">Round {seg.round_number}</div>
                  <div className="text-slate-500 text-xs mt-0.5">
                    {fmt(seg.start_s)} → {fmt(seg.end_s)} · {seg.end_s - seg.start_s}s · Session #{seg.session_id}
                  </div>
                </div>
                <span className="text-[9px] font-bold uppercase tracking-wider text-cyan-400 border border-cyan-400/20 bg-cyan-400/5 px-2.5 py-1 rounded-full">
                  Queued
                </span>
              </div>
            ))}
            {segs.length > 0 && (
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl px-4 py-3 text-slate-500 text-xs">
                Switch to the <strong className="text-slate-300">History</strong> tab to monitor each round's analysis progress.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
