import { useState, useRef } from 'react'
import { submitAnalysis, getStatus, getLog, getResults } from '../lib/api'
import { GAME_OPTIONS, GAME_NAMES, GAME_TEAMS } from '../lib/constants'
import Pipeline, { currentStep } from '../components/Pipeline'
import Analysis from '../components/Analysis'

function Label({ children }) {
  return <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500 mb-1.5">{children}</div>
}

function Input({ label, ...props }) {
  return (
    <div>
      {label && <Label>{label}</Label>}
      <input
        {...props}
        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-cyan-500 placeholder-slate-600"
      />
    </div>
  )
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

export default function AnalyzeClip() {
  const [file,       setFile]       = useState(null)
  const [game,       setGame]       = useState('r6siege')
  const [atk,        setAtk]        = useState('')
  const [def,        setDef]        = useState('')
  const [winner,     setWinner]     = useState('Unknown')
  const [roundNum,   setRoundNum]   = useState(1)
  const [minConf,    setMinConf]    = useState(0.75)
  const [webhook,    setWebhook]    = useState('')
  const [customDesc, setCustomDesc] = useState('')

  const [state,     setState]    = useState('idle')   // idle | uploading | polling | done | error
  const [sid,       setSid]      = useState(null)
  const [step,      setStep]     = useState(0)
  const [log,       setLog]      = useState([])
  const [elapsed,   setElapsed]  = useState(0)
  const [results,   setResults]  = useState(null)
  const [errMsg,    setErrMsg]   = useState('')
  const pollRef = useRef(null)
  const t0Ref   = useRef(null)

  const [la, lb] = GAME_TEAMS[game] || ['Team A','Team B']

  function stopPolling() {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
  }

  async function handleRun() {
    if (!file) return
    setState('uploading'); setErrMsg(''); setStep(0); setLog([]); setElapsed(0); setResults(null)
    try {
      const fd = new FormData()
      fd.append('clip', file)
      fd.append('game', game)
      fd.append('attacking_team', atk || la)
      fd.append('defending_team', def || lb)
      fd.append('winner', winner)
      fd.append('round_number', roundNum)
      fd.append('notes', '')
      fd.append('webhook_url', webhook)
      fd.append('min_confidence', minConf)
      fd.append('custom_game_description', customDesc)

      const { session_id } = await submitAnalysis(fd)
      setSid(session_id); setState('polling')
      t0Ref.current = Date.now()

      pollRef.current = setInterval(async () => {
        try {
          setElapsed(Math.floor((Date.now() - t0Ref.current) / 1000))
          const [statusRes, logRes] = await Promise.all([
            getStatus(session_id),
            getLog(session_id),
          ])
          const ll = logRes.log || []
          setLog(ll); setStep(currentStep(ll))

          if (statusRes.status === 'complete') {
            stopPolling()
            setStep(7)
            const data = await getResults(session_id)
            setResults(data); setState('done')
          } else if (statusRes.status === 'failed') {
            stopPolling()
            setErrMsg(statusRes.error || 'Analysis failed')
            setState('error')
          }
        } catch (_) {}
      }, 2000)
    } catch(e) {
      setErrMsg(e.message); setState('error')
    }
  }

  const confLabel = minConf >= 0.85 ? 'Strict' : minConf >= 0.7 ? 'Balanced' : 'Permissive'

  return (
    <div className="grid grid-cols-[420px_1fr] gap-8">
      {/* ── Form panel ── */}
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-black text-slate-50 tracking-tight">Analyze a Clip</h1>
          <p className="text-slate-500 text-sm mt-1">Upload a round clip — the full 9-source pipeline runs automatically.</p>
        </div>

        {/* File drop */}
        <div
          onClick={() => document.getElementById('clip-input').click()}
          className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
            file ? 'border-cyan-500/50 bg-cyan-500/5' : 'border-slate-700 hover:border-slate-500 bg-slate-900/50'
          }`}
        >
          <input
            id="clip-input"
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
              <div className="text-slate-500 text-sm font-medium">Drop clip here or click to browse</div>
              <div className="text-slate-700 text-xs mt-1">MP4 · MKV · MOV · up to 2 GB</div>
            </div>
          )}
        </div>

        <Select label="Game" options={GAME_OPTIONS} nameMap={GAME_NAMES} value={game} onChange={setGame} />

        {game === 'auto' && (
          <p className="text-slate-600 text-xs -mt-2">Gemini will identify the game from the clip.</p>
        )}
        {game === 'custom' && (
          <div>
            <Label>Describe the game</Label>
            <textarea
              value={customDesc}
              onChange={e => setCustomDesc(e.target.value)}
              placeholder="e.g. Rocket League — vehicular soccer"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm resize-none h-14 focus:outline-none focus:border-cyan-500"
            />
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <Input label={la} value={atk} onChange={e => setAtk(e.target.value)} placeholder="e.g. FaZe" />
          <Input label={lb} value={def} onChange={e => setDef(e.target.value)} placeholder="e.g. G2" />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Select
            label="Winner"
            options={[la, lb, 'Unknown']}
            value={winner}
            onChange={setWinner}
          />
          <div>
            <Label>Round #</Label>
            <input
              type="number" min={1} max={30} value={roundNum}
              onChange={e => setRoundNum(parseInt(e.target.value)||1)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between mb-1.5">
            <Label>Confidence threshold</Label>
            <span className="text-[9.5px] text-slate-500 font-semibold">{Math.round(minConf*100)}% — {confLabel}</span>
          </div>
          <input
            type="range" min={0.5} max={1} step={0.05} value={minConf}
            onChange={e => setMinConf(parseFloat(e.target.value))}
            className="w-full accent-cyan-400"
          />
        </div>

        <Input label="Webhook URL (optional)" value={webhook} onChange={e => setWebhook(e.target.value)} placeholder="https://…" />

        <button
          onClick={handleRun}
          disabled={!file || state === 'polling' || state === 'uploading'}
          className="w-full py-3 rounded-xl font-bold text-sm transition-all bg-gradient-to-r from-cyan-500 to-cyan-400 text-slate-950 hover:from-cyan-400 hover:to-cyan-300 shadow-[0_4px_20px_rgba(34,211,238,0.25)] hover:shadow-[0_6px_28px_rgba(34,211,238,0.4)] disabled:opacity-30 disabled:cursor-not-allowed disabled:shadow-none"
        >
          {state === 'uploading' ? 'Uploading…' : state === 'polling' ? `Analyzing… ${elapsed}s` : 'Run Analysis →'}
        </button>

        {state === 'error' && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-red-400 text-sm">{errMsg}</div>
        )}
      </div>

      {/* ── Results panel ── */}
      <div>
        {(state === 'polling' || state === 'uploading') && (
          <div>
            <Pipeline step={step} log={log} />
            <div className="text-center text-slate-600 text-xs mt-3">{elapsed}s elapsed</div>
          </div>
        )}
        {state === 'done' && results && (
          <Analysis data={results} sid={sid} />
        )}
        {state === 'idle' && (
          <div className="flex items-center justify-center h-80 text-center">
            <div>
              <div className="text-5xl opacity-5 mb-4">◆</div>
              <div className="text-slate-700 text-sm font-semibold">Results appear here</div>
              <div className="text-slate-800 text-xs mt-1">Upload a clip and hit Run Analysis.</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
