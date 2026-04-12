import streamlit as st
import os, requests, time, json

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
_API_KEY    = os.environ.get("ASC_API_KEY", "")
_sess       = requests.Session()
if _API_KEY:
    _sess.headers.update({"x-api-key": _API_KEY})

st.set_page_config(page_title="ASC", page_icon="◆", layout="wide",
                   initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* reset chrome */
*, *::before, *::after { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }
#MainMenu, footer, header,
[data-testid="stToolbar"], [data-testid="collapsedControl"],
.stDeployButton, section[data-testid="stSidebar"] { display:none !important; }

/* page */
.stApp { background:#09090b !important; }
.block-container { padding:0 !important; max-width:100% !important; }

/* ── nav bar ── */
.asc-nav {
  display:flex; align-items:center; justify-content:space-between;
  padding:0 40px; height:56px;
  background:#09090b; border-bottom:1px solid #27272a;
  position:sticky; top:0; z-index:200;
}
.asc-nav-logo { display:flex; align-items:center; gap:10px; }
.asc-nav-gem {
  width:30px; height:30px; border-radius:8px;
  background:linear-gradient(135deg,#7c3aed,#6366f1);
  display:flex; align-items:center; justify-content:center;
  font-size:13px; font-weight:800; color:#fff;
  box-shadow:0 0 16px rgba(124,58,237,.4);
}
.asc-nav-title { font-size:15px; font-weight:800; color:#fafafa; letter-spacing:-.4px; }
.asc-nav-sub   { font-size:9px; color:#3f3f46; text-transform:uppercase; letter-spacing:2px; font-weight:700; }
.asc-nav-chips { display:flex; gap:6px; }
.chip {
  font-size:9.5px; font-weight:700; text-transform:uppercase; letter-spacing:.8px;
  padding:4px 10px; border-radius:20px;
  background:#18181b; border:1px solid #27272a; color:#52525b;
}
.chip.lit { color:#a78bfa; background:rgba(124,58,237,.07); border-color:rgba(167,139,250,.2); }

/* ── page body ── */
.asc-body { padding:32px 40px 60px; max-width:1440px; margin:0 auto; }

/* ── section title ── */
.sec-title { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; color:#52525b; margin-bottom:16px; }

/* ── cards ── */
.card {
  background:#18181b; border:1px solid #27272a; border-radius:12px;
  padding:20px 24px; margin-bottom:12px;
}
.card-sm {
  background:#18181b; border:1px solid #27272a; border-radius:9px;
  padding:12px 16px; margin-bottom:8px;
}
.card-xs {
  background:#09090b; border:1px solid #1f1f23; border-radius:8px;
  padding:10px 14px; margin-bottom:6px;
}

/* ── KPI ── */
.krow { display:flex; gap:10px; margin-bottom:24px; }
.kpi {
  flex:1; background:#18181b; border:1px solid #27272a; border-radius:12px;
  padding:18px 16px; text-align:center; position:relative; overflow:hidden;
}
.kpi::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:#27272a; }
.kpi.kc::before { background:linear-gradient(90deg,#dc2626,#f87171); }
.kpi.km::before { background:linear-gradient(90deg,#d97706,#fbbf24); }
.kpi.kn::before { background:linear-gradient(90deg,#059669,#34d399); }
.kpi.kv::before { background:linear-gradient(90deg,#7c3aed,#a78bfa); }
.kpi.kp::before { background:linear-gradient(90deg,#0891b2,#22d3ee); }
.kv { font-size:26px; font-weight:800; color:#fafafa; letter-spacing:-.5px; line-height:1; margin-bottom:5px; }
.kl { font-size:9.5px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; color:#3f3f46; }
.kpi.kc .kv { color:#f87171; }
.kpi.km .kv { color:#fbbf24; }
.kpi.kn .kv { color:#34d399; }
.kpi.kv .kv { color:#a78bfa; }
.kpi.kp .kv { color:#22d3ee; }

/* ── badges ── */
.badge {
  display:inline-flex; align-items:center; gap:4px;
  padding:2px 8px; border-radius:4px;
  font-size:9.5px; font-weight:700; text-transform:uppercase; letter-spacing:.6px;
}
.b-c { color:#f87171; background:rgba(220,38,38,.08); border:1px solid rgba(248,113,113,.15); }
.b-m { color:#fbbf24; background:rgba(217,119,6,.08); border:1px solid rgba(251,191,36,.15); }
.b-n { color:#34d399; background:rgba(5,150,105,.08); border:1px solid rgba(52,211,153,.15); }
.b-v { color:#a78bfa; background:rgba(124,58,237,.08); border:1px solid rgba(167,139,250,.18); }
.b-g { color:#a1a1aa; background:rgba(161,161,170,.05); border:1px solid rgba(161,161,170,.12); }
.b-w { color:#fbbf24; background:rgba(217,119,6,.06); border:1px solid rgba(251,191,36,.14); }

/* ── dots ── */
.dot { width:6px; height:6px; border-radius:50%; display:inline-block; margin-right:4px; flex-shrink:0; }
.dot-c { background:#ef4444; box-shadow:0 0 6px rgba(239,68,68,.6); }
.dot-m { background:#f59e0b; box-shadow:0 0 6px rgba(245,158,11,.5); }
.dot-n { background:#10b981; box-shadow:0 0 6px rgba(16,185,129,.4); }

/* ── callouts ── */
.callout { border-left:2px solid; border-radius:0 10px 10px 0; padding:14px 18px; margin:10px 0; }
.c-blue   { background:rgba(99,102,241,.04); border-color:#6366f1; }
.c-red    { background:rgba(239,68,68,.04);  border-color:#ef4444; }
.c-purple { background:rgba(139,92,246,.04); border-color:#8b5cf6; }
.c-amber  { background:rgba(245,158,11,.04); border-color:#f59e0b; }
.c-green  { background:rgba(16,185,129,.04); border-color:#10b981; }

/* ── fl labels ── */
.fl { font-size:9.5px; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:6px; }
.f-blue   { color:#818cf8; } .f-green { color:#34d399; } .f-purple { color:#a78bfa; }
.f-amber  { color:#fbbf24; } .f-red   { color:#f87171; } .f-cyan   { color:#22d3ee; }

/* ── ts chip ── */
.ts { font-size:10.5px; font-weight:700; color:#52525b;
  background:#09090b; border:1px solid #27272a;
  border-radius:5px; padding:2px 9px; letter-spacing:.5px; }

/* ── pipeline ── */
.pipeline { display:flex; padding:20px 0 8px; }
.ps { flex:1; display:flex; flex-direction:column; align-items:center; position:relative; }
.ps:not(:last-child)::after {
  content:''; position:absolute; top:13px; left:calc(50% + 13px);
  right:calc(-50% + 13px); height:1px; background:#27272a;
}
.ps.done::after  { background:linear-gradient(90deg,#7c3aed,#6366f1); }
.ps.active::after { background:linear-gradient(90deg,#7c3aed,#27272a); }
.pd {
  width:27px; height:27px; border-radius:50%;
  border:2px solid #27272a; background:#18181b;
  display:flex; align-items:center; justify-content:center;
  font-size:10px; font-weight:700; color:#3f3f46;
  position:relative; z-index:1;
}
.pd.done   { border-color:#7c3aed; background:linear-gradient(135deg,#7c3aed,#6366f1); color:#fff; box-shadow:0 0 12px rgba(124,58,237,.4); }
.pd.active { border-color:#7c3aed; color:#a78bfa; animation:pulse 1.5s ease infinite; }
@keyframes pulse { 0%{box-shadow:0 0 0 0 rgba(124,58,237,.3);} 70%{box-shadow:0 0 0 6px rgba(124,58,237,0);} 100%{box-shadow:0 0 0 0 rgba(124,58,237,0);} }
.pl { font-size:8.5px; color:#3f3f46; margin-top:7px; text-align:center; font-weight:600; text-transform:uppercase; letter-spacing:.7px; max-width:52px; }
.pl.done   { color:#7c3aed; }
.pl.active { color:#a1a1aa; }
.log-row { display:flex; gap:8px; padding:3px 0; border-bottom:1px solid #18181b; }
.la { font-size:9px; font-weight:700; text-transform:uppercase; color:#7c3aed; min-width:68px; }
.ld { font-size:11px; color:#3f3f46; line-height:1.4; }

/* ── session rows ── */
.sr {
  display:flex; align-items:center; gap:10px;
  padding:10px 14px; border-radius:9px; margin-bottom:4px;
  background:#18181b; border:1px solid #27272a; cursor:pointer;
}
.sr:hover { border-color:#3f3f46; }
.sr.sel   { border-color:#7c3aed; background:rgba(124,58,237,.05); }
.sr-name  { font-size:12px; font-weight:600; color:#a1a1aa; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sr-meta  { font-size:10px; color:#3f3f46; margin-top:2px; }

/* ── strength ── */
.str-item {
  display:flex; align-items:flex-start; gap:10px; padding:11px 14px;
  background:rgba(16,185,129,.03); border:1px solid rgba(16,185,129,.09);
  border-radius:9px; margin-bottom:7px;
}

/* ── empty ── */
.empty { text-align:center; padding:60px 20px; }
.empty-icon  { font-size:28px; opacity:.12; margin-bottom:14px; }
.empty-title { font-size:14px; font-weight:700; color:#27272a; margin-bottom:6px; }
.empty-sub   { font-size:12px; color:#1f1f23; }

/* ── seg card ── */
.seg {
  background:#18181b; border:1px solid #27272a; border-radius:9px;
  padding:12px 18px; margin-bottom:7px;
  display:flex; align-items:center; justify-content:space-between;
}
.seg-n { font-size:13px; font-weight:600; color:#e4e4e7; }
.seg-m { font-size:11px; color:#3f3f46; margin-top:2px; }

/* ── inputs ── */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
  background:#18181b !important; border:1px solid #27272a !important;
  border-radius:8px !important; color:#e4e4e7 !important; font-size:13.5px !important;
}
.stSelectbox > div > div:focus-within,
.stTextInput > div > div > input:focus {
  border-color:#7c3aed !important; box-shadow:0 0 0 3px rgba(124,58,237,.12) !important;
}
.stTextArea textarea {
  background:#18181b !important; border:1px solid #27272a !important;
  border-radius:8px !important; color:#e4e4e7 !important; font-size:13px !important;
}
label, .stSelectbox label, .stTextInput label, .stNumberInput label {
  color:#52525b !important; font-size:10px !important; font-weight:700 !important;
  text-transform:uppercase !important; letter-spacing:1px !important;
}
[data-testid="stFileUploader"] {
  background:#18181b !important; border:1.5px dashed #27272a !important; border-radius:12px !important;
}
[data-testid="stFileUploader"]:hover { border-color:#7c3aed !important; }
[data-testid="stFileUploader"] section { background:transparent !important; }
[data-testid="stFileUploader"] button {
  background:#09090b !important; border:1px solid #27272a !important;
  color:#52525b !important; border-radius:6px !important;
}

/* ── buttons ── */
.stButton > button {
  background:#18181b !important; color:#52525b !important;
  border:1px solid #27272a !important; border-radius:8px !important;
  font-weight:600 !important; font-size:13px !important; padding:9px 18px !important;
  box-shadow:none !important; transition:all .15s !important;
}
.stButton > button:hover {
  background:#27272a !important; color:#a1a1aa !important;
  border-color:#3f3f46 !important; transform:none !important;
}
.stButton > button[data-testid="baseButton-primary"] {
  background:linear-gradient(135deg,#7c3aed,#6366f1) !important;
  color:#fff !important; border:none !important; border-radius:9px !important;
  font-size:14px !important; padding:12px 28px !important;
  box-shadow:0 4px 20px rgba(124,58,237,.3) !important;
}
.stButton > button[data-testid="baseButton-primary"]:hover {
  background:linear-gradient(135deg,#6d28d9,#4f46e5) !important;
  box-shadow:0 6px 28px rgba(124,58,237,.45) !important;
  transform:translateY(-1px) !important;
}
.stButton > button[data-testid="baseButton-primary"]:disabled {
  background:#18181b !important; color:#27272a !important;
  box-shadow:none !important; transform:none !important;
}

/* ── tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background:transparent !important; border-bottom:1px solid #27272a !important; gap:0 !important; padding:0 !important;
}
.stTabs [data-baseweb="tab"] {
  background:transparent !important; color:#3f3f46 !important;
  font-size:13px !important; font-weight:600 !important;
  padding:13px 24px 12px !important; border-radius:0 !important;
  border-bottom:2px solid transparent !important; letter-spacing:.1px !important;
}
.stTabs [data-baseweb="tab"]:hover { color:#71717a !important; }
.stTabs [aria-selected="true"] { color:#fafafa !important; border-bottom-color:#7c3aed !important; }
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display:none !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top:24px !important; }

/* ── expander ── */
[data-testid="stExpander"] {
  background:#18181b !important; border:1px solid #27272a !important;
  border-radius:10px !important; margin-bottom:6px !important;
}
[data-testid="stExpander"]:hover { border-color:#3f3f46 !important; }
[data-testid="stExpander"] > details > summary {
  color:#71717a !important; font-size:13px !important; font-weight:600 !important;
}

/* ── misc ── */
.stSlider [data-baseweb="slider"] [role="slider"] { background:#7c3aed !important; }
hr { border:none !important; border-top:1px solid #27272a !important; margin:20px 0 !important; }
.stMarkdown p, .stMarkdown li { color:#71717a !important; font-size:13.5px; line-height:1.7; }
h1 { color:#fafafa !important; font-size:20px !important; font-weight:800 !important; letter-spacing:-.4px !important; margin:0 0 4px !important; }
h2 { color:#e4e4e7 !important; font-size:16px !important; font-weight:700 !important; }
h3 { color:#3f3f46 !important; font-size:10.5px !important; font-weight:700 !important; text-transform:uppercase !important; letter-spacing:1.3px !important; margin-bottom:10px !important; }
[data-testid="column"] { min-width:0 !important; }
::-webkit-scrollbar { width:4px; } ::-webkit-scrollbar-track { background:#09090b; }
::-webkit-scrollbar-thumb { background:#27272a; border-radius:2px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SEV_ORDER = {"critical":0, "major":1, "minor":2}
PIPELINE_STEPS = ["Observe","Analyze","Debate","Critic","Coach","Enrich","Predict"]
AGENT_TO_STEP  = {
    "detector":0,"observer":0,"tactician":1,"debater":2,
    "critic":3,"coach":4,"statistician":5,"planner":5,"scenario":6,
}
GAME_OPTIONS = ["auto","r6siege","valorant","cs2","apex","lol","dota2","overwatch2","mlbb","marvelrivals","custom"]
GAME_NAMES   = {
    "auto":"Auto-detect","r6siege":"Rainbow Six Siege","valorant":"Valorant",
    "cs2":"Counter-Strike 2","apex":"Apex Legends","lol":"League of Legends",
    "dota2":"Dota 2","overwatch2":"Overwatch 2","mlbb":"Mobile Legends",
    "marvelrivals":"Marvel Rivals","custom":"Custom",
}
GAME_TEAMS = {
    "auto":("Team A","Team B"),"r6siege":("Attackers","Defenders"),
    "valorant":("Attackers","Defenders"),"cs2":("T Side","CT Side"),
    "apex":("Squad","Opponents"),"lol":("Blue Side","Red Side"),
    "dota2":("Radiant","Dire"),"overwatch2":("Attack","Defense"),
    "mlbb":("Blue Side","Red Side"),"marvelrivals":("Team A","Team B"),
    "custom":("Team A","Team B"),
}
STEP_DESCS = [
    "Observer builds a factual event log from the clip",
    "Tactician identifies tactical mistakes",
    "Debater adversarially challenges each finding",
    "Critic scores confidence and removes weak findings",
    "Coach writes the final actionable report",
    "Statistician and Planner add trends and opponent data",
    "Cosmos predicts what would have happened if corrected",
]

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _step(log):
    for e in reversed(log or []):
        if e.get("action")=="complete" and e.get("agent") in AGENT_TO_STEP:
            return AGENT_TO_STEP[e["agent"]]+1
    return 0

def ts(t): t=int(t or 0); return f"{t//60:02d}:{t%60:02d}"

def pipeline_html(step, log):
    dots=""
    for i,lbl in enumerate(PIPELINE_STEPS):
        s="done" if i<step else ("active" if i==step else "")
        cc="done" if i<step else ("active" if i==step else "")
        d="✓" if i<step else str(i+1)
        dots+=f'<div class="ps {cc}"><div class="pd {s}">{d}</div><div class="pl {s}">{lbl}</div></div>'
    desc = STEP_DESCS[min(step,len(STEP_DESCS)-1)]
    recent=[e for e in (log or [])[-6:] if e.get("action") in ("complete","re-examine","enriched")]
    lrows="".join(
        f'<div class="log-row"><span class="la">{e.get("agent","")}</span>'
        f'<span class="ld">{e.get("detail","")[:80]}</span></div>'
        for e in recent[-3:]
    )
    return f"""
<div class="card">
  <div class="sec-title" style="margin-bottom:2px;">Pipeline</div>
  <div class="pipeline">{dots}</div>
  <div style="font-size:11px;color:#3f3f46;text-align:center;padding-top:10px;border-top:1px solid #27272a;font-style:italic;">{desc}…</div>
  {"<div style='margin-top:10px;padding-top:8px;border-top:1px solid #18181b;'>"+lrows+"</div>" if lrows else ""}
</div>"""

def render_pipeline(step, log, ph):
    ph.markdown(pipeline_html(step, log), unsafe_allow_html=True)

def sev_badge(sev):
    cls = {"critical":"b-c","major":"b-m","minor":"b-n"}.get(sev,"b-g")
    dot = {"critical":"dot-c","major":"dot-m","minor":"dot-n"}.get(sev,"")
    return f'<span class="badge {cls}"><span class="dot {dot}"></span>{sev.upper()}</span>'

# ─────────────────────────────────────────────────────────────────────────────
# render_analysis
# ─────────────────────────────────────────────────────────────────────────────
def render_analysis(data, sid=None):
    result   = data.get("full_result") or {}
    mistakes = data.get("mistakes", [])

    if not result and not mistakes:
        st.markdown('<div class="empty"><div class="empty-icon">◈</div><div class="empty-title">No analysis data</div></div>', unsafe_allow_html=True)
        return

    crit  = sum(1 for m in mistakes if m.get("severity")=="critical")
    maj   = sum(1 for m in mistakes if m.get("severity")=="major")
    minn  = sum(1 for m in mistakes if m.get("severity")=="minor")
    valid = sum(1 for m in mistakes if m.get("confidence",2)>=3)

    pdf = ""
    if sid:
        pdf = f'<div class="kpi kp"><a href="{BACKEND_URL}/api/report/{sid}.pdf" target="_blank" style="text-decoration:none;display:block;"><div class="kv" style="font-size:19px;">↓ PDF</div><div class="kl">Report</div></a></div>'

    st.markdown(f"""
    <div class="krow">
      <div class="kpi"><div class="kv">{len(mistakes)}</div><div class="kl">Total</div></div>
      <div class="kpi kc"><div class="kv">{crit}</div><div class="kl">Critical</div></div>
      <div class="kpi km"><div class="kv">{maj}</div><div class="kl">Major</div></div>
      <div class="kpi kn"><div class="kv">{minn}</div><div class="kl">Minor</div></div>
      <div class="kpi kv"><div class="kv">{valid}</div><div class="kl">Validated</div></div>
      {pdf}
    </div>""", unsafe_allow_html=True)

    labels = ["Overview","Breakdown","Highlights"]
    if result.get("next_round_plan"): labels.append("Next Round")
    if result.get("trend_report"):    labels.append("Trends")
    tabs = st.tabs(labels)
    idx  = {l:t for l,t in zip(labels,tabs)}

    # Overview
    with idx["Overview"]:
        lc, rc = st.columns([3,2], gap="large")
        with lc:
            if result.get("summary"):
                st.markdown(f'<div class="card"><div class="fl f-blue">Summary</div><p style="color:#a1a1aa;font-size:13.5px;line-height:1.7;margin:6px 0 0;">{result["summary"]}</p></div>', unsafe_allow_html=True)
            if result.get("key_takeaway"):
                st.markdown(f'<div class="callout c-blue"><div class="fl f-blue" style="margin-bottom:5px;">Key Takeaway</div><p style="color:#c4c4cf;font-size:13px;font-style:italic;margin:0;line-height:1.65;">"{result["key_takeaway"]}"</p></div>', unsafe_allow_html=True)
        with rc:
            if result.get("loss_reason"):
                st.markdown(f'<div class="callout c-red"><div class="fl f-red" style="margin-bottom:5px;">Why They Lost</div><p style="color:#fca5a5;font-size:13px;margin:0;line-height:1.6;">{result["loss_reason"]}</p></div>', unsafe_allow_html=True)
            if mistakes:
                bc,bm,bn = max(crit,1),max(maj,0),max(minn,0)
                st.markdown(f"""
                <div class="card" style="padding:16px 18px;">
                  <div class="fl f-blue" style="margin-bottom:12px;">Severity Breakdown</div>
                  <div style="display:flex;gap:3px;height:5px;border-radius:3px;overflow:hidden;margin-bottom:10px;">
                    <div style="flex:{bc};background:linear-gradient(90deg,#dc2626,#f87171);min-width:4px;"></div>
                    <div style="flex:{bm};background:linear-gradient(90deg,#d97706,#fbbf24);min-width:{3 if maj else 0}px;"></div>
                    <div style="flex:{bn};background:linear-gradient(90deg,#059669,#34d399);min-width:{3 if minn else 0}px;"></div>
                  </div>
                  <div style="display:flex;gap:16px;">
                    <span style="font-size:12px;color:#f87171;display:flex;align-items:center;"><span class="dot dot-c"></span>{crit} Critical</span>
                    <span style="font-size:12px;color:#fbbf24;display:flex;align-items:center;"><span class="dot dot-m"></span>{maj} Major</span>
                    <span style="font-size:12px;color:#34d399;display:flex;align-items:center;"><span class="dot dot-n"></span>{minn} Minor</span>
                  </div>
                </div>""", unsafe_allow_html=True)

        phases = result.get("phase_breakdown") or {}
        if phases:
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            p1,p2,p3 = st.columns(3)
            for col,num,lbl,key,clr,fl in [
                (p1,"01","Setup","setup","#7c3aed","f-blue"),
                (p2,"02","Mid-Game","mid_round","#f59e0b","f-amber"),
                (p3,"03","Endgame","endgame","#ef4444","f-red"),
            ]:
                col.markdown(f'<div class="card-sm" style="border-left:2px solid {clr};padding-left:13px;"><div class="fl {fl}" style="margin-bottom:7px;">{num} {lbl}</div><p style="color:#71717a;font-size:12.5px;margin:0;line-height:1.6;">{phases.get(key,"—")}</p></div>', unsafe_allow_html=True)

    # Breakdown
    with idx["Breakdown"]:
        if not mistakes:
            st.markdown('<div class="empty"><div class="empty-icon">◇</div><div class="empty-title">No mistakes flagged</div><div class="empty-sub">The agents found nothing to flag in this clip.</div></div>', unsafe_allow_html=True)
        else:
            trend = result.get("trend_report") or {}
            persistent = trend.get("persistent_patterns") or []
            for p in persistent:
                uc = "#ef4444" if p.get("urgency")=="high" else "#f59e0b"
                st.markdown(f'<div style="background:rgba(245,158,11,.04);border:1px solid rgba(245,158,11,.12);border-radius:8px;padding:9px 14px;margin-bottom:6px;display:flex;align-items:center;gap:8px;"><span style="font-size:9px;font-weight:700;color:{uc};text-transform:uppercase;letter-spacing:1px;">⚠ Recurring</span><span style="font-size:12px;color:#71717a;">{p.get("category","").replace("-"," ").title()} · <b style="color:{uc};">{p.get("occurrences",0)}×</b> sessions</span></div>', unsafe_allow_html=True)

            for m in sorted(mistakes, key=lambda x: SEV_ORDER.get(x.get("severity","minor"),2)):
                sev    = m.get("severity","minor").lower()
                cat    = (m.get("category") or "").replace("-"," ").title()
                team   = m.get("team","")
                desc   = m.get("description","")
                alt    = m.get("better_alternative","")
                conf   = m.get("confidence",2)
                tstr   = ts(m.get("timestamp",0))
                short  = desc[:85]+("…" if len(desc)>85 else "")
                debate = m.get("debate",{})
                is_p   = any(p.get("category")==m.get("category") for p in persistent)
                vbadge = ' <span class="badge b-v">◆ Validated</span>' if conf>=3 else ""
                pbadge = ' <span class="badge b-w">⚠ Recurring</span>' if is_p else ""

                with st.expander(f"{tstr}  ·  {(team+' — ') if team else ''}{short}"):
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:14px;">
                      <span class="ts">{tstr}</span>
                      {sev_badge(sev)}
                      <span class="badge b-g">{cat}</span>{vbadge}{pbadge}
                    </div>
                    <div style="margin-bottom:14px;">
                      <div class="fl f-blue">What went wrong</div>
                      <p style="color:#a1a1aa;font-size:13px;line-height:1.7;margin:5px 0 0;">{desc}</p>
                    </div>
                    <div>
                      <div class="fl f-green">Better alternative</div>
                      <p style="color:#71717a;font-size:12.5px;line-height:1.65;margin:5px 0 0;">{alt}</p>
                    </div>""", unsafe_allow_html=True)
                    if debate and debate.get("challenge"):
                        verdict = debate.get("verdict","")
                        vc = {"supported":"#34d399","contested":"#fbbf24"}.get(verdict,"#52525b")
                        st.markdown(f"""
                        <div style="padding:12px 14px;background:#09090b;border:1px solid #27272a;border-radius:9px;margin-top:12px;">
                          <div style="display:flex;justify-content:space-between;margin-bottom:7px;">
                            <div class="fl f-purple" style="margin:0;">Debater Challenge</div>
                            <span style="font-size:9.5px;font-weight:700;color:{vc};text-transform:uppercase;">{verdict}</span>
                          </div>
                          <p style="color:#3f3f46;font-size:12px;margin:0 0 5px;font-style:italic;">"{debate.get('challenge','')}"</p>
                          {"" if not debate.get("rebuttal") else f'<p style="color:#52525b;font-size:12px;margin:0;">→ {debate["rebuttal"]}</p>'}
                        </div>""", unsafe_allow_html=True)
                    if m.get("scenario"):
                        st.markdown(f'<div class="callout c-purple" style="margin-top:10px;"><div class="fl f-purple" style="margin-bottom:5px;">If Corrected</div><p style="color:#c4b5fd;font-size:12.5px;margin:0;line-height:1.6;">{m["scenario"]}</p></div>', unsafe_allow_html=True)
                    if m.get("clip_path"):
                        st.video(f"{BACKEND_URL}{m['clip_path']}")

    # Highlights
    with idx["Highlights"]:
        strengths = result.get("strengths") or []
        if strengths:
            st.markdown("### What They Did Well")
            for s in strengths:
                st.markdown(f'<div class="str-item"><span style="color:#10b981;font-size:13px;margin-top:1px;">✓</span><p style="color:#4ade80;font-size:13px;margin:0;line-height:1.6;">{s}</p></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty"><div class="empty-icon">◇</div><div class="empty-title">No strengths noted</div></div>', unsafe_allow_html=True)

        if sid is not None:
            st.divider()
            st.markdown("### Rate This Analysis")
            fk = f"fb_{sid}"
            if st.session_state.get(f"{fk}_done"):
                st.success(f"Saved — {st.session_state.get(f'{fk}_r',0)}/5")
            else:
                cc,cn = st.columns([1,2])
                with cc:
                    rating = st.select_slider("Quality", options=[1,2,3,4,5], value=3,
                        format_func=lambda x:{1:"1 — Poor",2:"2",3:"3 — OK",4:"4",5:"5 — Excellent"}[x],
                        key=f"{fk}_sl")
                with cn:
                    notes = st.text_area("Notes (optional)", height=75, key=f"{fk}_n",
                                         placeholder="What was useful or missing?")
                if st.button("Save Feedback", type="primary", key=f"{fk}_btn"):
                    try:
                        _sess.post(f"{BACKEND_URL}/api/feedback/{sid}",
                                   json={"rating":rating,"notes":notes}, timeout=5).raise_for_status()
                        st.session_state[f"{fk}_done"] = True
                        st.session_state[f"{fk}_r"] = rating
                        st.toast("Saved!", icon="✓"); st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")

    if "Next Round" in idx:
        with idx["Next Round"]:
            plan = result.get("next_round_plan",{})
            if plan.get("priority_fix"):
                st.markdown(f'<div class="callout c-amber" style="margin-bottom:18px;"><div class="fl f-amber" style="margin-bottom:5px;">Priority Fix</div><p style="color:#fde68a;font-size:13px;margin:0;line-height:1.65;">{plan["priority_fix"]}</p></div>', unsafe_allow_html=True)
            c1,c2 = st.columns(2,gap="large")
            with c1:
                if plan.get("setup_adjustments"):
                    st.markdown("### Setup Adjustments")
                    for item in plan["setup_adjustments"]:
                        st.markdown(f'<div class="card-xs"><p style="color:#71717a;font-size:12.5px;margin:0;">→ {item}</p></div>', unsafe_allow_html=True)
                if plan.get("positions_to_avoid"):
                    st.markdown("### Positions to Avoid")
                    for item in plan["positions_to_avoid"]:
                        st.markdown(f'<div class="card-xs" style="border-left:2px solid #ef4444;"><p style="color:#fca5a5;font-size:12.5px;margin:0;">✕ {item}</p></div>', unsafe_allow_html=True)
            with c2:
                if plan.get("utility_plan"):
                    st.markdown("### Utility Plan")
                    for item in plan["utility_plan"]:
                        st.markdown(f'<div class="card-xs"><p style="color:#71717a;font-size:12.5px;margin:0;">→ {item}</p></div>', unsafe_allow_html=True)
                if plan.get("coordinated_plays"):
                    st.markdown("### Coordinated Plays")
                    for item in plan["coordinated_plays"]:
                        st.markdown(f'<div class="card-xs" style="border-left:2px solid #10b981;"><p style="color:#4ade80;font-size:12.5px;margin:0;">◆ {item}</p></div>', unsafe_allow_html=True)

    if "Trends" in idx:
        with idx["Trends"]:
            trend = result.get("trend_report",{})
            traj  = trend.get("overall_trajectory","unknown")
            tc    = {"improving":"#34d399","declining":"#f87171"}.get(traj,"#fbbf24")
            t1,t2,t3 = st.columns(3)
            t1.markdown(f'<div class="kpi"><div class="kv">{trend.get("sessions_analysed",0)}</div><div class="kl">Sessions</div></div>', unsafe_allow_html=True)
            t2.markdown(f'<div class="kpi"><div class="kv">{int(trend.get("win_rate_attacking",0)*100)}%</div><div class="kl">ATK Win Rate</div></div>', unsafe_allow_html=True)
            t3.markdown(f'<div class="kpi" style="border-top:2px solid {tc};"><div class="kv" style="color:{tc};">{traj.title()}</div><div class="kl">Trajectory</div></div>', unsafe_allow_html=True)
            if trend.get("coaching_priority"):
                st.markdown(f'<div class="callout c-blue" style="margin-top:16px;"><div class="fl f-blue" style="margin-bottom:5px;">Coaching Priority</div><p style="color:#a1a1aa;font-size:13px;margin:0;line-height:1.65;">{trend["coaching_priority"]}</p></div>', unsafe_allow_html=True)
            if trend.get("top_recurring_mistakes"):
                st.markdown("### Recurring Patterns")
                for m in trend["top_recurring_mistakes"]:
                    st.markdown(f'<div class="card-sm"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;"><span style="color:#e4e4e7;font-size:13px;font-weight:600;">{m.get("category","").replace("-"," ").title()}</span><span style="font-size:10px;color:#3f3f46;background:#09090b;border:1px solid #27272a;border-radius:4px;padding:2px 8px;font-weight:600;">{m.get("frequency",0)}× sessions</span></div><p style="color:#52525b;font-size:12px;margin:0;line-height:1.55;">{m.get("insight","")}</p></div>', unsafe_allow_html=True)
            r1,r2 = st.columns(2,gap="large")
            with r1:
                if trend.get("improving"):
                    st.markdown("### Improving")
                    for cat in trend["improving"]:
                        st.markdown(f'<div class="card-xs" style="border-left:2px solid #10b981;"><p style="color:#4ade80;font-size:12.5px;margin:0;font-weight:500;">↑ {cat.replace("-"," ").title()}</p></div>', unsafe_allow_html=True)
            with r2:
                if trend.get("regressing"):
                    st.markdown("### Regressing")
                    for cat in trend["regressing"]:
                        st.markdown(f'<div class="card-xs" style="border-left:2px solid #ef4444;"><p style="color:#fca5a5;font-size:12.5px;margin:0;font-weight:500;">↓ {cat.replace("-"," ").title()}</p></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# NAV BAR
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="asc-nav">
  <div class="asc-nav-logo">
    <div class="asc-nav-gem">◆</div>
    <div>
      <div class="asc-nav-title">ASC</div>
      <div class="asc-nav-sub">Agentic Strategic Coach</div>
    </div>
  </div>
  <div class="asc-nav-chips">
    <div class="chip lit">◆ Gemini 2.5 Flash</div>
    <div class="chip">9 ML Sources</div>
    <div class="chip">Multi-Agent</div>
  </div>
</div>
""", unsafe_allow_html=True)

# body padding
st.markdown('<div class="asc-body">', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_a, tab_v, tab_h = st.tabs(["  Analyze Clip  ", "  Full VOD  ", "  History  "])


# ═══════════════════════════════════════════════════════════════════
# ANALYZE CLIP
# ═══════════════════════════════════════════════════════════════════
with tab_a:
    fc, _, rc = st.columns([5, 1, 6])

    with fc:
        st.markdown("## Analyze a Clip")
        st.markdown('<p style="color:#52525b;font-size:13px;margin:0 0 20px;">Upload a round clip — the full 9-source pipeline runs automatically.</p>', unsafe_allow_html=True)

        clip_file = st.file_uploader("Upload clip", type=["mp4","mkv","mov"],
                                     label_visibility="collapsed", key="clip_up")
        if clip_file:
            sz = len(clip_file.getvalue())/1048576
            st.markdown(f'<p style="color:#34d399;font-size:12px;margin:4px 0 12px;">✓ {clip_file.name} · {sz:.1f} MB</p>', unsafe_allow_html=True)

        game = st.selectbox("Game", GAME_OPTIONS, format_func=lambda x: GAME_NAMES[x])
        custom_desc = ""
        if game == "auto":
            st.caption("Gemini will identify the game from the clip.")
        elif game == "custom":
            custom_desc = st.text_area("Describe the game", height=60, placeholder="e.g. Rocket League — vehicular soccer", key="cdesc")

        la, lb = GAME_TEAMS.get(game, ("Team A","Team B"))
        c1,c2 = st.columns(2)
        atk = c1.text_input(la, placeholder="e.g. FaZe", key="atk")
        dfn = c2.text_input(lb, placeholder="e.g. G2", key="def")

        cw,rn = st.columns(2)
        winner = cw.selectbox("Winner", [la, lb, "Unknown"])
        rnum   = rn.number_input("Round #", 1, 30, 1)

        min_conf = st.slider("Confidence threshold", 0.5, 1.0, 0.75, 0.05,
            help="Higher = fewer, more certain findings")
        lev = "Strict" if min_conf>=0.85 else "Balanced" if min_conf>=0.7 else "Permissive"
        st.caption(f"{min_conf:.0%} — {lev}")

        webhook = st.text_input("Webhook URL (optional)", placeholder="https://…", key="wh")

        go = st.button("Run Analysis →", type="primary", use_container_width=True,
                       disabled=(clip_file is None), key="run")
        if go:
            st.session_state.update({
                "analyzing":True, "clip_file":clip_file,
                "done":False, "last_sid":None,
                "g":game,"ak":atk,"dk":dfn,"wi":winner,
                "rn":rnum,"cf":min_conf,"wh2":webhook,"cd":custom_desc,
            })

    with rc:
        if st.session_state.get("analyzing") and st.session_state.get("clip_file"):
            doc = st.session_state["clip_file"]
            ph  = st.empty(); sp = st.empty()
            try:
                sp.markdown('<p style="color:#52525b;font-size:12px;text-align:center;padding-top:40px;">Uploading…</p>', unsafe_allow_html=True)
                render_pipeline(0, [], ph)
                r = _sess.post(f"{BACKEND_URL}/api/analyze",
                    files={"clip":(doc.name, doc.getvalue(), "video/mp4")},
                    data={"game":st.session_state.get("g","r6siege"),
                          "attacking_team":st.session_state.get("ak","Attackers"),
                          "defending_team":st.session_state.get("dk","Defenders"),
                          "winner":st.session_state.get("wi","Unknown"),
                          "round_number":str(st.session_state.get("rn",1)),
                          "notes":"",
                          "webhook_url":st.session_state.get("wh2",""),
                          "min_confidence":str(st.session_state.get("cf",0.75)),
                          "custom_game_description":st.session_state.get("cd","")},
                    timeout=60)
                r.raise_for_status()
                sid = r.json()["session_id"]; t0 = time.time()
                for _ in range(200):
                    el = time.time()-t0
                    try:
                        lr = _sess.get(f"{BACKEND_URL}/api/log/{sid}", timeout=5).json()
                        ll = lr.get("log",[]); cur = _step(ll)
                    except Exception:
                        ll=[]; cur=min(int(el/20),len(PIPELINE_STEPS)-1)
                    render_pipeline(cur, ll, ph)
                    sp.markdown(f'<p style="color:#3f3f46;font-size:12px;text-align:center;">{int(el)}s elapsed</p>', unsafe_allow_html=True)
                    s = _sess.get(f"{BACKEND_URL}/api/status/{sid}", timeout=5).json()
                    if s.get("status")=="complete":
                        render_pipeline(len(PIPELINE_STEPS), ll, ph)
                        sp.markdown('<p style="color:#34d399;font-size:12px;text-align:center;font-weight:600;">✓ Complete</p>', unsafe_allow_html=True)
                        st.session_state.update({"analyzing":False,"done":True,"last_sid":sid})
                        st.rerun()
                    elif s.get("status")=="failed":
                        ph.empty(); sp.empty()
                        st.error(f"Failed: {s.get('error','Unknown')}")
                        st.session_state["analyzing"]=False; st.stop()
                    time.sleep(3)
                else:
                    st.error("Timed out."); st.session_state["analyzing"]=False; st.stop()
            except Exception as e:
                ph.empty(); sp.empty()
                st.error(f"Upload failed: {e}")
                st.session_state["analyzing"]=False; st.stop()

        elif st.session_state.get("done") and st.session_state.get("last_sid"):
            try:
                res = _sess.get(f"{BACKEND_URL}/api/results/{st.session_state['last_sid']}", timeout=15).json()
                render_analysis(res, sid=st.session_state["last_sid"])
            except Exception as e:
                st.error(f"Could not load results: {e}")
        else:
            st.markdown("""
            <div style="padding:60px 20px;text-align:center;">
              <div style="font-size:32px;opacity:.08;margin-bottom:14px;">◆</div>
              <div style="font-size:14px;font-weight:700;color:#27272a;margin-bottom:8px;">Results appear here</div>
              <div style="font-size:12.5px;color:#1f1f23;line-height:1.6;">Upload a clip and hit<br>Run Analysis to get started.</div>
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# FULL VOD
# ═══════════════════════════════════════════════════════════════════
with tab_v:
    vc, _ = st.columns([4,3])
    with vc:
        st.markdown("## Analyze Full VOD")
        st.markdown('<p style="color:#52525b;font-size:13px;margin:0 0 20px;">Upload a full match. Gemini detects round boundaries and queues each round for analysis automatically.</p>', unsafe_allow_html=True)

        vod = st.file_uploader("Upload VOD", type=["mp4","mkv","mov"],
                               label_visibility="collapsed", key="vod_up")
        if vod:
            sz = len(vod.getvalue())/1048576
            st.markdown(f'<p style="color:#34d399;font-size:12px;margin:4px 0 12px;">✓ {vod.name} · {sz:.1f} MB</p>', unsafe_allow_html=True)

        vg = st.selectbox("Game", GAME_OPTIONS, format_func=lambda x: GAME_NAMES[x], key="vg")
        vla, vlb = GAME_TEAMS.get(vg, ("Team A","Team B"))
        va, vb = st.columns(2)
        vatk = va.text_input(vla, placeholder="Team A", key="vatk")
        vdef = vb.text_input(vlb, placeholder="Team B", key="vdef")

        if st.button("Detect Rounds & Queue Analysis", type="primary",
                     use_container_width=True, disabled=(vod is None), key="vod_go"):
            with st.status("Detecting rounds…", expanded=True) as vs:
                try:
                    st.write("Uploading and running Gemini round detection…")
                    r = _sess.post(f"{BACKEND_URL}/api/segment-vod",
                        files={"vod":(vod.name, vod.getvalue(), "video/mp4")},
                        data={"game":vg,"attacking_team":vatk or "Attackers",
                              "defending_team":vdef or "Defenders"},
                        timeout=300)
                    r.raise_for_status()
                    segs = r.json().get("segments",[])
                    vs.update(label=f"Found {len(segs)} round(s) — analysis queued", state="complete")
                    for seg in segs:
                        sm,ss = seg['start_s']//60, seg['start_s']%60
                        em,es = seg['end_s']//60,   seg['end_s']%60
                        dur   = seg['end_s']-seg['start_s']
                        st.markdown(f"""
                        <div class="seg">
                          <div><div class="seg-n">Round {seg['round_number']}</div>
                          <div class="seg-m">{sm:02d}:{ss:02d} → {em:02d}:{es:02d} · {dur}s · Session {seg['session_id']}</div></div>
                          <span class="badge b-v">Queued</span>
                        </div>""", unsafe_allow_html=True)
                    st.info("Go to the **History** tab to monitor each round.")
                except Exception as e:
                    vs.update(label="Detection failed", state="error")
                    st.error(f"{e}")


# ═══════════════════════════════════════════════════════════════════
# HISTORY
# ═══════════════════════════════════════════════════════════════════
with tab_h:
    st.markdown("## History")
    st.markdown('<p style="color:#52525b;font-size:13px;margin:0 0 20px;">Past sessions and semantic mistake search.</p>', unsafe_allow_html=True)

    # Search
    sq_c, sg_c, sb_c = st.columns([5, 2, 1])
    sq = sq_c.text_input("Search mistakes", placeholder='"bad rotation when outnumbered"',
                         label_visibility="collapsed", key="sq")
    sg = sg_c.selectbox("Game", ["All"]+GAME_OPTIONS[1:-1],
                        label_visibility="collapsed", key="sg")
    do_search = sb_c.button("Search", type="primary", use_container_width=True, key="sb")

    if do_search and sq.strip():
        try:
            gf = None if sg=="All" else sg
            sr = _sess.get(f"{BACKEND_URL}/api/search",
                           params={"q":sq.strip(),"game":gf,"limit":8}, timeout=10).json()
            hits = sr.get("results",[])
            if hits:
                st.markdown(f'<div style="font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#7c3aed;margin:12px 0 8px;">{len(hits)} semantic matches</div>', unsafe_allow_html=True)
                for h in hits:
                    sev  = h.get("severity","minor").lower()
                    cat  = (h.get("category") or "").replace("-"," ").title()
                    desc = h.get("description","")[:110]
                    sim  = int(h.get("_similarity",0)*100)
                    rn2  = h.get("round_number","?")
                    gn   = GAME_NAMES.get(h.get("game",""),"")
                    st.markdown(f"""
                    <div class="card-sm" style="margin-bottom:6px;">
                      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
                        {sev_badge(sev)} <span class="badge b-g">{cat}</span>
                        <span style="font-size:10px;color:#3f3f46;margin-left:auto;">{sim}% · R{rn2} · {gn}</span>
                      </div>
                      <p style="font-size:12.5px;color:#71717a;margin:0;line-height:1.55;">{desc}</p>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("No similar mistakes found.")
        except Exception as e:
            st.error(f"Search failed: {e}")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    try:
        sessions = _sess.get(f"{BACKEND_URL}/api/sessions?limit=100", timeout=5).json().get("sessions",[])
    except Exception as e:
        st.error(f"Cannot reach backend: {e}"); st.stop()

    if not sessions:
        st.markdown('<div class="empty"><div class="empty-icon">◈</div><div class="empty-title">No analyses yet</div><div class="empty-sub">Upload a clip on the Analyze tab.</div></div>', unsafe_allow_html=True)
        st.stop()

    SDOT  = {"complete":"#34d399","failed":"#f87171","analysing":"#fbbf24","uploading":"#fbbf24"}
    SLBL  = {"complete":"Done","failed":"Failed","analysing":"Live","uploading":"Upload"}

    lc, dc = st.columns([1,2], gap="large")

    with lc:
        st.markdown("### Sessions")
        if "sel_sid" not in st.session_state:
            st.session_state.sel_sid = sessions[0]["id"] if sessions else None

        for s in sessions:
            dot    = SDOT.get(s["status"],"#52525b")
            slbl   = SLBL.get(s["status"],s["status"])
            fname  = (s.get("clip_filename") or "—")[:22]
            rn2    = s.get("round_number","?")
            gn     = GAME_NAMES.get(s.get("game",""),"")[:12]
            is_sel = st.session_state.sel_sid == s["id"]
            sc     = " sel" if is_sel else ""
            gl     = f"box-shadow:0 0 5px {dot};" if s["status"]=="analysing" else ""
            st.markdown(f"""
            <div class="sr{sc}">
              <div style="width:6px;height:6px;border-radius:50%;background:{dot};flex-shrink:0;{gl}"></div>
              <div style="flex:1;min-width:0;">
                <div class="sr-name">R{rn2} — {fname}</div>
                <div class="sr-meta">{slbl} · {gn}</div>
              </div>
            </div>""", unsafe_allow_html=True)
            if st.button("Open →", key=f"o_{s['id']}", use_container_width=True):
                st.session_state.sel_sid = s["id"]; st.rerun()

    with dc:
        sid = st.session_state.get("sel_sid")
        if not sid:
            st.markdown('<div class="empty"><div class="empty-icon">◇</div><div class="empty-title">Select a session</div></div>', unsafe_allow_html=True)
        else:
            sel = next((s for s in sessions if s["id"]==sid), None)
            if sel and sel["status"] in ("analysing","uploading"):
                pp,sp2 = st.empty(), st.empty()
                try:
                    lr = _sess.get(f"{BACKEND_URL}/api/log/{sid}", timeout=5).json()
                    ll = lr.get("log",[])
                    render_pipeline(_step(ll), ll, pp)
                    sp2.caption(f"Status: {sel['status']} — in progress.")
                except Exception:
                    st.info(f"Status: **{sel['status']}**")
            elif sel and sel["status"]=="failed":
                st.error(f"Failed: {sel.get('error_message','Unknown')}")
            else:
                try:
                    res = _sess.get(f"{BACKEND_URL}/api/results/{sid}", timeout=12).json()
                    fn  = res.get("clip_filename","") or f"Session {sid}"
                    gn  = GAME_NAMES.get(res.get("game",""),"")
                    rn2 = res.get("round_number","?")
                    st.markdown(f"""
                    <div style="margin-bottom:20px;">
                      <div style="font-size:16px;font-weight:700;color:#fafafa;letter-spacing:-.3px;margin-bottom:3px;">R{rn2} — {fn[:40]}</div>
                      <div style="font-size:12px;color:#52525b;">{gn} · {res.get("attacking_team","")} vs {res.get("defending_team","")} · {res.get("winner","")} won</div>
                    </div>""", unsafe_allow_html=True)
                    render_analysis(res, sid=sid)
                except Exception as e:
                    st.error(f"Could not load results: {e}")

st.markdown('</div>', unsafe_allow_html=True)
