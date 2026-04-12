"""
Orchestrator — coordinates the multi-agent analysis pipeline.

Pipeline:
  1. ObserverAgent  → factual event log (Gemini + Pegasus in parallel) + context cache
  2. TacticianAgent → tactical analysis with tool use (examine_timestamp)
  3. DebaterAgent   → adversarially challenges each finding
  4. CriticAgent    → validates findings, scores confidence, flags weak points
     └── if confidence < threshold and iterations remain → re-examine flags → repeat 2-4
  5. CoachAgent     → final report enriched with historical context
  6. StatisticianAgent + PlannerAgent (parallel)
  7. ScenarioAgent  → alternative outcome predictions

Agents communicate via structured state. The Orchestrator decides when
confidence is sufficient to proceed, making this a genuine agent loop.
"""
import os
import json
import logging
import time
from dataclasses import dataclass, field
from google import genai

from backend.agents.observer import ObserverAgent
from backend.agents.tactician import TacticianAgent
from backend.agents.debater import DebaterAgent
from backend.agents.critic import CriticAgent
from backend.agents.coach import CoachAgent
from backend.agents.statistician import StatisticianAgent
from backend.agents.planner import PlannerAgent
from backend.agents.scenario import ScenarioAgent
from backend.agents.tools import examine_clip_at_timestamp

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 2


@dataclass
class AnalysisState:
    context:            dict
    uploaded_file:      object        = None
    cache_name:         str | None    = None
    event_log:          dict          = field(default_factory=dict)
    tactical_findings:  dict          = field(default_factory=dict)
    critic_output:      dict          = field(default_factory=dict)
    final_result:       dict          = field(default_factory=dict)
    iterations:         int           = 0
    agent_log:          list          = field(default_factory=list)

    def record(self, agent: str, action: str, detail: str = ""):
        entry = {
            "agent":     agent,
            "action":    action,
            "detail":    detail,
            "iteration": self.iterations,
            "ts":        time.time(),
        }
        self.agent_log.append(entry)
        logger.info(f"  [{agent.upper()}] {action}" + (f" — {detail}" if detail else ""))
        return entry


class Orchestrator:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        self.client       = genai.Client(api_key=api_key)
        self.observer     = ObserverAgent(self.client)
        self.tactician    = TacticianAgent(self.client)
        self.debater      = DebaterAgent(self.client)
        self.critic       = CriticAgent(self.client)
        self.coach        = CoachAgent(self.client)
        self.statistician = StatisticianAgent(self.client)
        self.planner      = PlannerAgent(self.client)
        self.scenario     = ScenarioAgent(self.client)

    def run(self, clip_path: str, context: dict, examples: list = None,
            log_callback=None, confidence_threshold: float = 0.75) -> dict:
        """
        Run the full multi-agent pipeline.
        log_callback(log: list) is called after each agent step with the current log.
        confidence_threshold controls how strict the Critic is (0.0–1.0).
        """
        self._clip_path = clip_path
        state = AnalysisState(context=context)
        game  = context.get("game", "r6siege")
        atk   = context.get("attacking_team", "Attackers")
        defn  = context.get("defending_team", "Defenders")
        logger.info(f"[Orchestrator] Starting — {game} | {atk} vs {defn} | threshold={confidence_threshold:.0%}")

        def _notify(agent, action, detail=""):
            entry = state.record(agent, action, detail)
            if log_callback:
                try:
                    log_callback(state.agent_log)
                except Exception:
                    pass
            return entry

        # ── Phase 1: Observe ──────────────────────────────────────────────────
        _notify("orchestrator", "dispatch", "ObserverAgent — building event log + context cache")
        obs = self.observer.run(clip_path, context)
        state.uploaded_file = obs["uploaded_file"]
        state.cache_name    = obs.get("cache_name")
        state.event_log     = obs["event_log"]
        _notify("observer", "complete",
                f"Gemini log: {len(state.event_log['gemini_log'])} chars | "
                f"Pegasus: {len(state.event_log['pegasus_mistakes'])} events | "
                f"Cache: {'active' if state.cache_name else 'none'}")

        # ── Phase 2: Analyze → Critique loop ─────────────────────────────────
        for i in range(MAX_ITERATIONS):
            state.iterations = i + 1

            _notify("orchestrator", "dispatch",
                    f"TacticianAgent — iteration {state.iterations}")
            state.tactical_findings = self.tactician.run(
                state.uploaded_file, state.event_log, context,
                cache_name=state.cache_name
            )
            tool_calls = len(state.tactical_findings.get("tool_calls", []))
            n_mistakes = len(state.tactical_findings.get("mistakes", []))
            _notify("tactician", "complete",
                    f"{n_mistakes} mistakes found | {tool_calls} tool call(s)")

            _notify("orchestrator", "dispatch", "DebaterAgent — challenging findings")
            state.tactical_findings = self.debater.run(
                state.tactical_findings, state.event_log, context
            )
            post_debate = len(state.tactical_findings.get("mistakes", []))
            _notify("debater", "complete",
                    f"{post_debate} survived debate (dropped {n_mistakes - post_debate})")

            _notify("orchestrator", "dispatch", "CriticAgent — validating findings")
            state.critic_output = self.critic.run(
                state.tactical_findings, state.event_log, context,
                clip_path=clip_path, confidence_threshold=confidence_threshold
            )
            confidence = state.critic_output.get("confidence", 0.7)
            flags      = state.critic_output.get("flags", [])
            removed    = state.critic_output.get("removed_count", 0)
            _notify("critic", "complete",
                    f"confidence={confidence:.0%} | removed={removed} | flags={len(flags)}")

            if confidence >= confidence_threshold or i == MAX_ITERATIONS - 1:
                logger.info(f"[Orchestrator] Confidence {confidence:.0%} — proceeding to Coach")
                break

            if flags:
                logger.info(f"[Orchestrator] Re-examining {len(flags)} flag(s)...")
                _notify("orchestrator", "re-examine", f"{len(flags)} flag(s)")
                extra_obs = self._re_examine_flags(state.uploaded_file, flags, state.cache_name)
                state.event_log["gemini_log"] = (
                    state.event_log.get("gemini_log", "") +
                    "\n\nRE-EXAMINATION (requested by Critic):\n" + extra_obs
                )

        # ── Phase 3: Coach ────────────────────────────────────────────────────
        validated = state.critic_output.get("revised_findings", state.tactical_findings)
        _notify("orchestrator", "dispatch", "CoachAgent — producing final report")
        state.final_result = self.coach.run(validated, context, examples or [])
        _notify("coach", "complete",
                f"{len(state.final_result.get('mistakes', []))} mistakes in final report")

        self._apply_confidence(state)

        # ── Phase 4: Statistician + Planner (parallel) ───────────────────────
        from concurrent.futures import ThreadPoolExecutor
        _notify("orchestrator", "dispatch", "StatisticianAgent + PlannerAgent (parallel)")
        with ThreadPoolExecutor(max_workers=2) as executor:
            f_stat = executor.submit(self.statistician.run, context, state.final_result)
            f_plan = executor.submit(self.planner.run, state.final_result, None, context)

            trend_report = next_round_plan = None
            try:
                trend_report = f_stat.result(timeout=60)
                _notify("statistician", "complete",
                        trend_report.get("overall_trajectory", "?") if trend_report else "insufficient history")
            except Exception as e:
                logger.warning(f"[Orchestrator] Statistician failed: {e}")

            try:
                next_round_plan = f_plan.result(timeout=60)
                _notify("planner", "complete",
                        next_round_plan.get("priority_fix", "")[:80] if next_round_plan else "failed")
            except Exception as e:
                logger.warning(f"[Orchestrator] Planner failed: {e}")

        if trend_report and next_round_plan is not None:
            try:
                next_round_plan = self.planner.run(state.final_result, trend_report, context)
                _notify("planner", "enriched", "re-ran with trend + opponent data")
            except Exception as e:
                logger.warning(f"[Orchestrator] Planner re-run failed: {e}")

        if trend_report:
            state.final_result["trend_report"] = trend_report
        if next_round_plan:
            state.final_result["next_round_plan"] = next_round_plan

        # ── Phase 5: Scenario Agent ───────────────────────────────────────────
        _notify("orchestrator", "dispatch", "ScenarioAgent — generating alternative scenarios")
        try:
            state.final_result = self.scenario.run(
                state.final_result, clip_path, state.event_log, context
            )
            scenarios = sum(1 for m in state.final_result.get("mistakes", []) if "scenario" in m)
            _notify("scenario", "complete", f"{scenarios} scenario(s) generated")
        except Exception as e:
            logger.warning(f"[Orchestrator] ScenarioAgent failed: {e}")

        # Cleanup Gemini uploaded file + cache
        if state.uploaded_file:
            try:
                self.client.files.delete(name=state.uploaded_file.name)
            except Exception:
                pass
        if state.cache_name:
            try:
                self.client.caches.delete(name=state.cache_name)
            except Exception:
                pass

        logger.info(f"[Orchestrator] Done — {state.iterations} iteration(s), "
                    f"{len(state.agent_log)} agent events")

        state.final_result["_agent_log"] = state.agent_log
        return state.final_result

    def _re_examine_flags(self, uploaded_file, flags: list,
                          cache_name: str | None) -> str:
        lines = []
        for flag in flags[:3]:
            ts = int(flag) if isinstance(flag, (int, float)) else 0
            if ts <= 0:
                continue
            question = (
                f"What exactly happened at {ts}s? "
                f"Describe player positions, actions, and any eliminations precisely."
            )
            try:
                obs = examine_clip_at_timestamp(
                    uploaded_file, ts, question, self.client, cache_name=cache_name
                )
                lines.append(f"[{ts}s re-examined]: {obs}")
            except Exception as e:
                lines.append(f"[{ts}s]: Could not re-examine — {e}")
        return "\n".join(lines)

    def _apply_confidence(self, state: AnalysisState):
        validated_descs = {
            m.get("description", "")[:60]
            for m in state.critic_output.get("validated_mistakes", [])
        }
        for m in state.final_result.get("mistakes", []):
            if m.get("description", "")[:60] in validated_descs:
                m["confidence"] = max(m.get("confidence", 2), 3)
