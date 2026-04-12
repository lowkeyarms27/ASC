import { PIPELINE_STEPS, AGENT_TO_STEP } from '../lib/constants'

export function currentStep(log) {
  for (let i = (log || []).length - 1; i >= 0; i--) {
    const e = log[i]
    if (e.action === 'complete' && e.agent in AGENT_TO_STEP) {
      return AGENT_TO_STEP[e.agent] + 1
    }
  }
  return 0
}

export default function Pipeline({ step, log }) {
  const recent = (log || [])
    .filter(e => ['complete','re-examine','enriched'].includes(e.action))
    .slice(-3)

  const desc = PIPELINE_STEPS[Math.min(step, PIPELINE_STEPS.length - 1)]?.desc || ''

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
      <div className="text-[10px] font-bold uppercase tracking-widest text-slate-600 mb-4">
        Pipeline
      </div>

      {/* Steps */}
      <div className="flex items-start">
        {PIPELINE_STEPS.map((s, i) => {
          const done   = i < step
          const active = i === step
          return (
            <div key={i} className="flex-1 flex flex-col items-center relative">
              {/* connector line */}
              {i < PIPELINE_STEPS.length - 1 && (
                <div className={`absolute top-[13px] left-1/2 right-0 h-px ${
                  done ? 'bg-gradient-to-r from-cyan-500 to-cyan-400/50' : 'bg-slate-800'
                }`} style={{ left: 'calc(50% + 14px)', right: 'calc(-50% + 14px)' }} />
              )}
              {/* dot */}
              <div className={`relative z-10 w-7 h-7 rounded-full border-2 flex items-center justify-center text-[10px] font-bold transition-all ${
                done
                  ? 'border-cyan-400 bg-gradient-to-br from-cyan-400 to-cyan-600 text-slate-950 shadow-[0_0_10px_rgba(34,211,238,0.4)]'
                  : active
                  ? 'border-cyan-400 bg-slate-900 text-cyan-400 animate-pulse'
                  : 'border-slate-700 bg-slate-900 text-slate-600'
              }`}>
                {done ? '✓' : i + 1}
              </div>
              {/* label */}
              <div className={`mt-2 text-center text-[8.5px] font-semibold uppercase tracking-wider max-w-[52px] leading-tight ${
                done ? 'text-cyan-500' : active ? 'text-slate-300' : 'text-slate-700'
              }`}>
                {s.label}
              </div>
            </div>
          )
        })}
      </div>

      {/* Current step description */}
      <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-600 text-center italic">
        {desc}…
      </div>

      {/* Recent log rows */}
      {recent.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-900 space-y-1">
          {recent.map((e, i) => (
            <div key={i} className="flex gap-2 text-[10.5px]">
              <span className="text-cyan-500 font-bold uppercase min-w-[64px] shrink-0">
                {e.agent}
              </span>
              <span className="text-slate-600 truncate">{(e.detail || '').slice(0, 80)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
