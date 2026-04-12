export default function Topbar({ tab, tabs, onTab }) {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/90 backdrop-blur-sm">
      <div className="max-w-screen-xl mx-auto px-8 flex items-center gap-8 h-14">
        {/* Logo */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center text-slate-950 text-xs font-black shadow-[0_0_16px_rgba(34,211,238,0.35)]">
            ◆
          </div>
          <div>
            <div className="text-sm font-bold text-slate-50 leading-none tracking-tight">ASC</div>
            <div className="text-[9px] text-slate-700 uppercase tracking-[2px] font-semibold leading-none mt-0.5">
              Strategic Coach
            </div>
          </div>
        </div>

        {/* Tabs */}
        <nav className="flex items-center gap-1">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => onTab(t.id)}
              className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                tab === t.id
                  ? 'bg-cyan-400 text-slate-950'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>

        {/* Status chips */}
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[9px] font-bold uppercase tracking-widest text-cyan-400/60 border border-cyan-400/15 bg-cyan-400/5 px-2.5 py-1 rounded-full">
            ◆ Gemini 2.5 Flash
          </span>
          <span className="text-[9px] font-bold uppercase tracking-widest text-slate-600 border border-slate-800 bg-slate-900 px-2.5 py-1 rounded-full">
            9 ML Sources
          </span>
          <span className="text-[9px] font-bold uppercase tracking-widest text-slate-600 border border-slate-800 bg-slate-900 px-2.5 py-1 rounded-full">
            Multi-Agent
          </span>
        </div>
      </div>
    </header>
  )
}
