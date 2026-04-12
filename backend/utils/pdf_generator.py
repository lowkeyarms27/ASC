"""
PDF Report Generator — produces a clean printable coaching report.
Uses fpdf2 (pure Python, no system dependencies).
"""
from fpdf import FPDF
import datetime


SEV_COLORS = {
    "critical": (248, 113, 113),
    "major":    (251, 191,  36),
    "minor":    ( 52, 211, 153),
}


class _Report(FPDF):
    def __init__(self, session: dict):
        super().__init__()
        self._session = session
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 18, 18)

    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(30, 30, 30)
        self.cell(0, 8, "ASC — Agentic Strategic Coach", align="L")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 120)
        date = self._session.get("created_at", "")[:10]
        self.cell(0, 8, f"Generated {date}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(220, 220, 220)
        self.line(18, self.get_y(), self.w - 18, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(160, 160, 160)
        self.cell(0, 6, f"Page {self.page_no()} — Confidential coaching report", align="C")


def _section_title(pdf: FPDF, title: str):
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 30, 30)
    pdf.set_fill_color(245, 246, 248)
    pdf.cell(0, 8, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def _body(pdf: FPDF, text: str, color=(70, 70, 70)):
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*color)
    pdf.multi_cell(0, 5.5, text or "—")
    pdf.ln(1)


def _kpi_row(pdf: FPDF, kpis: list):
    """kpis: [(label, value, color_rgb)]"""
    col_w = (pdf.w - 36) / len(kpis)
    pdf.set_font("Helvetica", "B", 14)
    for label, value, color in kpis:
        x = pdf.get_x()
        y = pdf.get_y()
        pdf.set_fill_color(248, 249, 250)
        pdf.rect(x, y, col_w - 3, 18, "F")
        pdf.set_text_color(*color)
        pdf.set_xy(x, y + 1)
        pdf.cell(col_w - 3, 7, str(value), align="C")
        pdf.set_xy(x, y + 8)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(col_w - 3, 5, label, align="C")
        pdf.set_xy(x + col_w, y)
        pdf.set_font("Helvetica", "B", 14)
    pdf.ln(22)


def generate_pdf(session: dict, result: dict, mistakes: list) -> bytes:
    """
    Build a PDF coaching report.
    Returns raw bytes suitable for a streaming HTTP response.
    """
    pdf = _Report(session)
    pdf.add_page()

    game   = session.get("game", "r6siege").replace("r6siege", "R6 Siege").replace("valorant", "Valorant")
    atk    = session.get("attacking_team", "Attackers")
    defn   = session.get("defending_team", "Defenders")
    winner = session.get("winner", "Unknown")
    rnum   = session.get("round_number", 1)

    # ── Title ─────────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(15, 15, 15)
    pdf.cell(0, 10, f"{game} — Round {rnum} Analysis", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"{atk}  (ATK)  vs  {defn}  (DEF)  ·  Winner: {winner}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    critical = sum(1 for m in mistakes if m.get("severity") == "critical")
    major    = sum(1 for m in mistakes if m.get("severity") == "major")
    minor    = sum(1 for m in mistakes if m.get("severity") == "minor")
    agreed   = sum(1 for m in mistakes if m.get("confidence", 2) >= 3)
    _kpi_row(pdf, [
        ("Mistakes",        len(mistakes), (30, 30, 30)),
        ("Critical",        critical,      (220, 60, 60)),
        ("Major",           major,         (200, 140, 20)),
        ("Minor",           minor,         (30, 170, 100)),
        ("Dual Validated",  agreed,        (90, 90, 220)),
    ])

    # ── Summary ───────────────────────────────────────────────────────────────
    if result.get("summary"):
        _section_title(pdf, "Round Summary")
        _body(pdf, result["summary"])

    if result.get("key_takeaway"):
        pdf.set_font("Helvetica", "BI", 10)
        pdf.set_text_color(59, 130, 246)
        pdf.cell(0, 5, "Key Takeaway", new_x="LMARGIN", new_y="NEXT")
        _body(pdf, f'"{result["key_takeaway"]}"', color=(60, 90, 160))

    if result.get("loss_reason"):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(200, 60, 60)
        pdf.cell(0, 5, "Why They Lost", new_x="LMARGIN", new_y="NEXT")
        _body(pdf, result["loss_reason"], color=(180, 60, 60))

    # ── Phase Breakdown ───────────────────────────────────────────────────────
    phases = result.get("phase_breakdown") or {}
    if phases:
        _section_title(pdf, "Phase Breakdown")
        for label, key in [("Setup", "setup"), ("Mid-Round", "mid_round"), ("Endgame", "endgame")]:
            if phases.get(key):
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
                _body(pdf, phases[key])

    # ── Mistakes ──────────────────────────────────────────────────────────────
    if mistakes:
        _section_title(pdf, "Tactical Mistakes")
        sev_order = {"critical": 0, "major": 1, "minor": 2}
        for i, m in enumerate(sorted(mistakes, key=lambda x: sev_order.get(x.get("severity", "minor"), 2)), 1):
            ts  = int(m.get("timestamp", 0))
            mm, ss = ts // 60, ts % 60
            sev = m.get("severity", "minor")
            cat = m.get("category", "").replace("-", " ").title()
            col = SEV_COLORS.get(sev, (120, 120, 120))

            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*col)
            pdf.cell(0, 6, f"{i}. [{mm:02d}:{ss:02d}]  {sev.upper()}  —  {cat}", new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(14)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, "What went wrong:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 5, m.get("description", ""), padding=(0, 0, 0, 8))

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(30, 140, 90)
            pdf.cell(0, 5, "Better alternative:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(40, 120, 80)
            pdf.multi_cell(0, 5, m.get("better_alternative", ""), padding=(0, 0, 0, 8))

            if m.get("scenario"):
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(90, 90, 200)
                pdf.cell(0, 5, "If corrected (predicted outcome):", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(100, 100, 180)
                pdf.multi_cell(0, 5, m["scenario"], padding=(0, 0, 0, 8))

            pdf.ln(3)

    # ── Strengths ─────────────────────────────────────────────────────────────
    strengths = result.get("strengths") or []
    if strengths:
        _section_title(pdf, "What They Did Well")
        for s in strengths:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 140, 90)
            pdf.multi_cell(0, 5.5, f"✓  {s}")
            pdf.ln(1)

    # ── Next Round Plan ───────────────────────────────────────────────────────
    plan = result.get("next_round_plan") or {}
    if plan:
        pdf.add_page()
        _section_title(pdf, "Next Round Plan")

        if plan.get("priority_fix"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(180, 120, 20)
            pdf.cell(0, 5, "Priority Fix", new_x="LMARGIN", new_y="NEXT")
            _body(pdf, plan["priority_fix"], color=(160, 100, 20))

        for section, label, color in [
            ("setup_adjustments",  "Setup Adjustments",   (60, 60, 60)),
            ("utility_plan",       "Utility Plan",        (60, 60, 60)),
            ("positions_to_avoid", "Positions to Avoid",  (200, 60, 60)),
            ("coordinated_plays",  "Coordinated Plays",   (30, 140, 90)),
        ]:
            items = plan.get(section, [])
            if items:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(*color)
                pdf.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(*[min(c + 30, 255) for c in color])
                for item in items:
                    pdf.multi_cell(0, 5, f"→  {item}", padding=(0, 0, 0, 6))
                pdf.ln(2)

        if plan.get("if_losing_again"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(180, 120, 20)
            pdf.cell(0, 5, "If Same Mistake Repeats", new_x="LMARGIN", new_y="NEXT")
            _body(pdf, plan["if_losing_again"], color=(160, 100, 20))

    # ── Trend Report ─────────────────────────────────────────────────────────
    trend = result.get("trend_report") or {}
    if trend:
        _section_title(pdf, "Performance Trends")
        traj = trend.get("overall_trajectory", "unknown")
        traj_col = {"improving": (30, 140, 90), "declining": (200, 60, 60)}.get(traj, (150, 120, 30))
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*traj_col)
        pdf.cell(0, 6, f"Trajectory: {traj.title()}  |  Sessions analysed: {trend.get('sessions_analysed', 0)}", new_x="LMARGIN", new_y="NEXT")
        if trend.get("coaching_priority"):
            _body(pdf, trend["coaching_priority"])
        if trend.get("top_recurring_mistakes"):
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(0, 5, "Recurring Patterns:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            for m in trend["top_recurring_mistakes"]:
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(0, 5, f"• {m.get('category','').title()} ({m.get('frequency',0)}×): {m.get('insight','')}", padding=(0, 0, 0, 4))
            pdf.ln(1)

    return bytes(pdf.output())
