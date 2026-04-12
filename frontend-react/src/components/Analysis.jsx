import { useState } from 'react'
import { submitFeedback, pdfUrl } from '../lib/api'
import { SEV_ORDER, GAME_NAMES } from '../lib/constants'

const BASE = import.meta.env.VITE_BACKEND_URL || ''

function ts(t) {
  const s = Math.floor(t || 0)
  return `${String(Math.floor(s / 60)).padStart(2,'0')}:${String(s % 60).padStart(2,'0')}`
}

function SevBadge({ sev }) {
  const cfg = {
    critical: 'bg-red-500/10 text-red-400 border-red-500/20',
    major:    'bg-amber-500/10 text-amber-400 border-amber-500/20',
    minor:    'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  }
  const dot = {
    critical: 'bg-red-400',
    major:    'bg-amber-400',
    minor:    'bg-emerald-400',
  }
  const cls = cfg[sev] || 'bg-slate-500/10 text-slate-400 border-slate-500/20'
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ${cls}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot[sev] || 'bg-slate-400'}`} />
      {sev}
    </span>
  )
}

function Callout({ color, label, children }) {
  const colors = {
    blue:   'border-indigo-500 bg-indigo-500/5 text-indigo-300',
    red:    'border-red-500 bg-red-500/5 text-red-300',
    amber:  'border-amber-500 bg-amber-500/5 text-amber-200',
    green:  'border-emerald-500 bg-emerald-500/5 text-emerald-300',
    purple: 'border-violet-500 bg-violet-500/5 text-violet-300',
    cyan:   'border-cyan-500 bg-cyan-500/5 text-cyan-300',
  }
  const labelColors = {
    blue:'text-indigo-400', red:'text-red-400', amber:'text-amber-400',
    green:'text-emerald-400', purple:'text-violet-400', cyan:'text-cyan-400',
  }
  return (
    <div className={`border-l-2 rounded-r-xl pl-4 pr-4 py-3 ${colors[color]}`}>
      {label && <div className={`text-[9.5px] font-bold uppercase tracking-widest mb-1.5 ${labelColors[color]}`}>{label}</div>}
      <p className="text-sm leading-relaxed m-0">{children}</p>
    </div>
  )
}

function MistakeCard({ m, persistent }) {
  const [open, setOpen] = useState(false)
  const sev    = (m.severity || 'minor').toLowerCase()
  const cat    = (m.category || '').replace(/-/g,' ')
  const isPers = persistent.some(p => p.category === m.category)

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden mb-2">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-slate-800/50 transition-colors"
      >
        <span className="text-slate-600 text-xs font-mono shrink-0">{ts(m.timestamp)}</span>
        <SevBadge sev={sev} />
        <span className="text-slate-400 text-sm truncate flex-1">
          {m.team && <span className="text-slate-500 mr-2">{m.team} —</span>}
          {(m.description || '').slice(0, 80)}{(m.description||'').length > 80 ? '…' : ''}
        </span>
        {m.confidence >= 3 && (
          <span className="shrink-0 text-[9px] font-bold text-cyan-400 border border-cyan-400/20 bg-cyan-400/5 px-2 py-0.5 rounded-full uppercase tracking-wider">
            ◆ Validated
          </span>
        )}
        {isPers && (
          <span className="shrink-0 text-[9px] font-bold text-amber-400 border border-amber-400/20 bg-amber-400/5 px-2 py-0.5 rounded-full uppercase tracking-wider">
            ⚠ Recurring
          </span>
        )}
        <span className="text-slate-600 text-xs shrink-0">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="px-4 pb-4 border-t border-slate-800 pt-3 space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono text-slate-600 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">{ts(m.timestamp)}</span>
            <SevBadge sev={sev} />
            <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400 border border-slate-700 bg-slate-800 px-2 py-0.5 rounded">
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </span>
          </div>

          <div>
            <div className="text-[9.5px] font-bold uppercase tracking-widest text-indigo-400 mb-1.5">What went wrong</div>
            <p className="text-slate-300 text-[13px] leading-relaxed">{m.description}</p>
          </div>

          {m.better_alternative && (
            <div>
              <div className="text-[9.5px] font-bold uppercase tracking-widest text-emerald-400 mb-1.5">Better alternative</div>
              <p className="text-slate-400 text-[12.5px] leading-relaxed">{m.better_alternative}</p>
            </div>
          )}

          {m.debate?.challenge && (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="text-[9.5px] font-bold uppercase tracking-widest text-violet-400">Debater Challenge</div>
                {m.debate.verdict && (
                  <span className={`text-[9px] font-bold uppercase ${
                    m.debate.verdict === 'supported' ? 'text-emerald-400' : 'text-amber-400'
                  }`}>{m.debate.verdict}</span>
                )}
              </div>
              <p className="text-slate-500 text-xs italic">&ldquo;{m.debate.challenge}&rdquo;</p>
              {m.debate.rebuttal && (
                <p className="text-slate-600 text-xs mt-1">→ {m.debate.rebuttal}</p>
              )}
            </div>
          )}

          {m.scenario && (
            <Callout color="purple" label="If Corrected">{m.scenario}</Callout>
          )}

          {m.clip_path && (
            <video
              src={`${BASE}${m.clip_path}`}
              controls
              className="w-full rounded-lg mt-1 max-h-48 bg-black"
            />
          )}
        </div>
      )}
    </div>
  )
}

function FeedbackSection({ sid }) {
  const [rating, setRating] = useState(3)
  const [notes, setNotes]   = useState('')
  const [done, setDone]     = useState(false)
  const [err, setErr]       = useState('')

  async function submit() {
    try {
      await submitFeedback(sid, rating, notes)
      setDone(true)
    } catch(e) {
      setErr(e.message)
    }
  }

  if (done) {
    return (
      <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 text-emerald-400 text-sm font-medium">
        ✓ Feedback saved — {rating}/5
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div>
        <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500 mb-2">Quality Rating</div>
        <div className="flex gap-2">
          {[1,2,3,4,5].map(n => (
            <button
              key={n}
              onClick={() => setRating(n)}
              className={`w-9 h-9 rounded-lg text-sm font-bold border transition-all ${
                rating === n
                  ? 'bg-cyan-400 text-slate-950 border-cyan-400'
                  : 'bg-slate-900 text-slate-500 border-slate-700 hover:border-slate-500'
              }`}
            >{n}</button>
          ))}
        </div>
      </div>
      <div>
        <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500 mb-2">Notes (optional)</div>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="What was useful or missing?"
          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-300 text-sm resize-none h-16 focus:outline-none focus:border-cyan-500"
        />
      </div>
      {err && <div className="text-red-400 text-xs">{err}</div>}
      <button
        onClick={submit}
        className="bg-gradient-to-r from-cyan-500 to-cyan-400 text-slate-950 font-bold text-sm px-5 py-2 rounded-lg hover:from-cyan-400 hover:to-cyan-300 transition-all"
      >
        Save Feedback
      </button>
    </div>
  )
}

export default function Analysis({ data, sid }) {
  const result   = data?.full_result || {}
  const mistakes = data?.mistakes || []
  const [activeTab, setActiveTab] = useState('overview')

  if (!result && !mistakes.length) {
    return (
      <div className="text-center py-20 text-slate-700">
        <div className="text-4xl mb-3 opacity-20">◈</div>
        <div className="text-sm font-semibold">No analysis data</div>
      </div>
    )
  }

  const crit  = mistakes.filter(m => m.severity === 'critical').length
  const maj   = mistakes.filter(m => m.severity === 'major').length
  const minn  = mistakes.filter(m => m.severity === 'minor').length
  const valid = mistakes.filter(m => (m.confidence||2) >= 3).length

  const trend      = result.trend_report || {}
  const persistent = trend.persistent_patterns || []

  const tabs = ['overview', 'breakdown', 'highlights']
  if (result.next_round_plan) tabs.push('next round')
  if (result.trend_report)    tabs.push('trends')

  return (
    <div>
      {/* KPI row */}
      <div className="grid grid-cols-6 gap-3 mb-6">
        {[
          { v: mistakes.length, l: 'Total',     cls: '' },
          { v: crit,  l: 'Critical',   cls: 'border-t-red-500' },
          { v: maj,   l: 'Major',      cls: 'border-t-amber-500' },
          { v: minn,  l: 'Minor',      cls: 'border-t-emerald-500' },
          { v: valid, l: 'Validated',  cls: 'border-t-cyan-500' },
        ].map(k => (
          <div key={k.l} className={`bg-slate-900 border border-slate-800 rounded-xl p-4 text-center border-t-2 ${k.cls || 'border-t-slate-800'}`}>
            <div className={`text-2xl font-black leading-none mb-1 ${
              k.l==='Critical'?'text-red-400':k.l==='Major'?'text-amber-400':k.l==='Minor'?'text-emerald-400':k.l==='Validated'?'text-cyan-400':'text-slate-100'
            }`}>{k.v}</div>
            <div className="text-[9px] font-bold uppercase tracking-widest text-slate-600">{k.l}</div>
          </div>
        ))}
        {sid && (
          <a
            href={pdfUrl(sid)}
            target="_blank"
            rel="noreferrer"
            className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center border-t-2 border-t-sky-500 hover:border-sky-400 transition-all group"
          >
            <div className="text-xl font-black text-sky-400 leading-none mb-1 group-hover:text-sky-300">↓</div>
            <div className="text-[9px] font-bold uppercase tracking-widest text-slate-600">PDF</div>
          </a>
        )}
      </div>

      {/* Tab nav */}
      <div className="flex gap-1 bg-slate-900 border border-slate-800 rounded-xl p-1 w-fit mb-6">
        {tabs.map(t => (
          <button
            key={t}
            onClick={() => setActiveTab(t)}
            className={`px-4 py-1.5 rounded-lg text-[12px] font-semibold capitalize transition-all ${
              activeTab === t
                ? 'bg-cyan-400 text-slate-950'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >{t}</button>
        ))}
      </div>

      {/* Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-3">
              {result.summary && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="text-[9.5px] font-bold uppercase tracking-widest text-indigo-400 mb-2">Summary</div>
                  <p className="text-slate-300 text-sm leading-relaxed">{result.summary}</p>
                </div>
              )}
              {result.key_takeaway && (
                <Callout color="blue" label="Key Takeaway">{result.key_takeaway}</Callout>
              )}
            </div>
            <div className="space-y-3">
              {result.loss_reason && (
                <Callout color="red" label="Why They Lost">{result.loss_reason}</Callout>
              )}
              {mistakes.length > 0 && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="text-[9.5px] font-bold uppercase tracking-widest text-indigo-400 mb-3">Severity Breakdown</div>
                  <div className="flex gap-0.5 h-1.5 rounded overflow-hidden mb-3">
                    {crit  > 0 && <div style={{flex:crit}}  className="bg-gradient-to-r from-red-600 to-red-400" />}
                    {maj   > 0 && <div style={{flex:maj}}   className="bg-gradient-to-r from-amber-600 to-amber-400" />}
                    {minn  > 0 && <div style={{flex:minn}}  className="bg-gradient-to-r from-emerald-600 to-emerald-400" />}
                  </div>
                  <div className="flex gap-4 text-xs">
                    <span className="flex items-center gap-1.5 text-red-400"><span className="w-1.5 h-1.5 rounded-full bg-red-400" />{crit} Critical</span>
                    <span className="flex items-center gap-1.5 text-amber-400"><span className="w-1.5 h-1.5 rounded-full bg-amber-400" />{maj} Major</span>
                    <span className="flex items-center gap-1.5 text-emerald-400"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />{minn} Minor</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Phase breakdown */}
          {result.phase_breakdown && (
            <div className="grid grid-cols-3 gap-3">
              {[
                { num:'01', key:'setup',     label:'Setup',    color:'border-l-cyan-500',   tc:'text-cyan-400'   },
                { num:'02', key:'mid_round', label:'Mid-Game', color:'border-l-amber-500',  tc:'text-amber-400'  },
                { num:'03', key:'endgame',   label:'Endgame',  color:'border-l-red-500',    tc:'text-red-400'    },
              ].map(p => (
                <div key={p.key} className={`bg-slate-900 border border-slate-800 rounded-xl p-4 border-l-2 ${p.color}`}>
                  <div className={`text-[9.5px] font-bold uppercase tracking-widest mb-2 ${p.tc}`}>{p.num} {p.label}</div>
                  <p className="text-slate-400 text-[12.5px] leading-relaxed">{result.phase_breakdown[p.key] || '—'}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Breakdown */}
      {activeTab === 'breakdown' && (
        <div>
          {persistent.map((p, i) => (
            <div key={i} className="flex items-center gap-2 bg-amber-500/5 border border-amber-500/15 rounded-lg px-3 py-2 mb-2">
              <span className="text-[9px] font-bold uppercase text-amber-400">⚠ Recurring</span>
              <span className="text-xs text-slate-400">
                {p.category?.replace(/-/g,' ')} · <strong className="text-amber-400">{p.occurrences}×</strong> sessions
              </span>
            </div>
          ))}

          {mistakes.length === 0 ? (
            <div className="text-center py-16 text-slate-700">
              <div className="text-3xl mb-2 opacity-20">◇</div>
              <div className="text-sm font-semibold">No mistakes flagged</div>
            </div>
          ) : (
            [...mistakes]
              .sort((a,b) => (SEV_ORDER[a.severity]||2) - (SEV_ORDER[b.severity]||2))
              .map((m, i) => <MistakeCard key={i} m={m} persistent={persistent} />)
          )}
        </div>
      )}

      {/* Highlights */}
      {activeTab === 'highlights' && (
        <div className="space-y-4">
          {(result.strengths||[]).length > 0 ? (
            <div>
              <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500 mb-3">What They Did Well</div>
              {result.strengths.map((s, i) => (
                <div key={i} className="flex gap-3 items-start bg-emerald-500/5 border border-emerald-500/12 rounded-xl px-4 py-3 mb-2">
                  <span className="text-emerald-400 mt-0.5">✓</span>
                  <p className="text-emerald-300/80 text-[13px] leading-relaxed">{s}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-700 text-sm">No strengths noted</div>
          )}

          {sid != null && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mt-4">
              <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500 mb-4">Rate This Analysis</div>
              <FeedbackSection sid={sid} />
            </div>
          )}
        </div>
      )}

      {/* Next Round */}
      {activeTab === 'next round' && result.next_round_plan && (
        <div>
          {result.next_round_plan.priority_fix && (
            <Callout color="amber" label="Priority Fix">{result.next_round_plan.priority_fix}</Callout>
          )}
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div className="space-y-2">
              {result.next_round_plan.setup_adjustments?.length > 0 && (
                <>
                  <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500 mb-2">Setup Adjustments</div>
                  {result.next_round_plan.setup_adjustments.map((item, i) => (
                    <div key={i} className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-400 text-xs">→ {item}</div>
                  ))}
                </>
              )}
              {result.next_round_plan.positions_to_avoid?.length > 0 && (
                <>
                  <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500 mb-2 mt-3">Positions to Avoid</div>
                  {result.next_round_plan.positions_to_avoid.map((item, i) => (
                    <div key={i} className="bg-slate-900 border-l-2 border-l-red-500 border border-slate-800 rounded-lg px-3 py-2 text-red-300/70 text-xs">✕ {item}</div>
                  ))}
                </>
              )}
            </div>
            <div className="space-y-2">
              {result.next_round_plan.utility_plan?.length > 0 && (
                <>
                  <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500 mb-2">Utility Plan</div>
                  {result.next_round_plan.utility_plan.map((item, i) => (
                    <div key={i} className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-400 text-xs">→ {item}</div>
                  ))}
                </>
              )}
              {result.next_round_plan.coordinated_plays?.length > 0 && (
                <>
                  <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500 mb-2 mt-3">Coordinated Plays</div>
                  {result.next_round_plan.coordinated_plays.map((item, i) => (
                    <div key={i} className="bg-slate-900 border-l-2 border-l-emerald-500 border border-slate-800 rounded-lg px-3 py-2 text-emerald-300/70 text-xs">◆ {item}</div>
                  ))}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Trends */}
      {activeTab === 'trends' && result.trend_report && (() => {
        const t = result.trend_report
        const traj = t.overall_trajectory || 'unknown'
        const tc = { improving:'text-emerald-400', declining:'text-red-400' }[traj] || 'text-amber-400'
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
                <div className="text-2xl font-black text-slate-100 mb-1">{t.sessions_analysed||0}</div>
                <div className="text-[9px] font-bold uppercase tracking-widest text-slate-600">Sessions</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
                <div className="text-2xl font-black text-slate-100 mb-1">{Math.round((t.win_rate_attacking||0)*100)}%</div>
                <div className="text-[9px] font-bold uppercase tracking-widest text-slate-600">ATK Win Rate</div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center border-t-2 border-t-current">
                <div className={`text-xl font-black mb-1 capitalize ${tc}`}>{traj}</div>
                <div className="text-[9px] font-bold uppercase tracking-widest text-slate-600">Trajectory</div>
              </div>
            </div>
            {t.coaching_priority && <Callout color="blue" label="Coaching Priority">{t.coaching_priority}</Callout>}
            {t.top_recurring_mistakes?.length > 0 && (
              <div>
                <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500 mb-3">Recurring Patterns</div>
                {t.top_recurring_mistakes.map((m, i) => (
                  <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-3 mb-2 flex justify-between items-start">
                    <div>
                      <div className="text-slate-200 text-[13px] font-semibold capitalize">{(m.category||'').replace(/-/g,' ')}</div>
                      <p className="text-slate-500 text-xs mt-1 leading-relaxed">{m.insight}</p>
                    </div>
                    <span className="text-[10px] text-slate-500 border border-slate-700 bg-slate-950 px-2 py-0.5 rounded font-semibold shrink-0 ml-3">{m.frequency}× sessions</span>
                  </div>
                ))}
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              {t.improving?.length > 0 && (
                <div>
                  <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500 mb-2">Improving</div>
                  {t.improving.map((cat, i) => (
                    <div key={i} className="border-l-2 border-l-emerald-500 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 mb-1 text-emerald-300/70 text-xs font-medium">↑ {cat.replace(/-/g,' ')}</div>
                  ))}
                </div>
              )}
              {t.regressing?.length > 0 && (
                <div>
                  <div className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500 mb-2">Regressing</div>
                  {t.regressing.map((cat, i) => (
                    <div key={i} className="border-l-2 border-l-red-500 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 mb-1 text-red-300/70 text-xs font-medium">↓ {cat.replace(/-/g,' ')}</div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )
      })()}
    </div>
  )
}
