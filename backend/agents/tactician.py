"""
Tactician Agent — interprets the Observer's event log tactically.
Uses Gemini function calling to examine specific timestamps when uncertain.
Uses the context cache when available so video tokens are only charged once.
"""
import json
import logging
from google.genai import types
from backend.agents.game_config import get_config
from backend.agents.tools import examine_clip_at_timestamp
from backend.utils.gemini_client import _extract_json

logger = logging.getLogger(__name__)

_TOOLS = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="examine_timestamp",
        description=(
            "Examine a specific timestamp in the clip to verify a potential mistake "
            "before flagging it. Use this when you are uncertain whether something "
            "actually happened or want to confirm what you think you saw."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "timestamp": types.Schema(
                    type=types.Type.INTEGER,
                    description="The second in the clip to examine"
                ),
                "question": types.Schema(
                    type=types.Type.STRING,
                    description="Specific factual question about what to look for at this timestamp"
                ),
            },
            required=["timestamp", "question"]
        )
    )
])


class TacticianAgent:
    MAX_TOOL_CALLS = 5

    def __init__(self, client, model="gemini-2.5-flash"):
        self.client = client
        self.model  = model

    def run(self, uploaded_file, event_log: dict, context: dict,
            cache_name: str | None = None) -> dict:
        """
        Analyze tactics grounded in the Observer's event log.
        Uses cache_name for video access when available to reduce token cost.
        """
        atk    = context.get("attacking_team", "Attackers")
        defn   = context.get("defending_team", "Defenders")
        winner = context.get("winner", "Unknown")
        rnum   = context.get("round_number", "?")
        game        = context.get("game", "r6siege")
        custom_desc = context.get("custom_game_description", "")
        cfg         = get_config(game, custom_desc)
        phase_labels = cfg.get("phase_labels", {})
        setup_label  = phase_labels.get("setup",     "Setup Phase")
        mid_label    = phase_labels.get("mid_round", "Mid-Round")
        end_label    = phase_labels.get("endgame",   "Endgame")
        role_a       = cfg.get("team_role_a", "Team A")
        role_b       = cfg.get("team_role_b", "Team B")

        map_knowledge    = cfg.get("map_knowledge", "")
        gemini_log         = event_log.get("gemini_log", "")
        pegasus_summary    = event_log.get("pegasus_summary", "")
        pegasus_mistakes   = event_log.get("pegasus_mistakes", [])
        spatial_log        = event_log.get("spatial_log", "")
        yolo_summary       = event_log.get("yolo_summary", "")
        whisper_transcript = event_log.get("whisper_transcript", "")
        ocr_summary        = event_log.get("ocr_summary", "")
        ocr_kills          = event_log.get("ocr_kills", [])
        tracker_summary    = event_log.get("tracker_summary", "")
        tracker_events     = event_log.get("tracker_events", [])
        audio_summary      = event_log.get("audio_summary", "")
        audio_events       = event_log.get("audio_events", [])
        clip_summary       = event_log.get("clip_summary", "")
        clip_concepts      = event_log.get("clip_concepts", [])

        prompt = f"""{cfg['coaching_prompt']}

{map_knowledge}

{atk} ({role_a}) vs {defn} ({role_b}). Segment/round {rnum}. {winner} won.
Refer to players as "{atk} {role_a}" or "{defn} {role_b}" only — no personal names.

━━━ OBSERVER EVENT LOG ━━━
{gemini_log}

━━━ PEGASUS CROSS-REFERENCE ━━━
{pegasus_summary}
{json.dumps(pegasus_mistakes, indent=2) if pegasus_mistakes else "(no Pegasus mistakes)"}

━━━ SPATIAL ANALYSIS (cosmos-reason2-8b) ━━━
{spatial_log if spatial_log else "(spatial analysis unavailable)"}

━━━ YOLO FRAME DETECTION (PyTorch/YOLOv8) ━━━
{yolo_summary if yolo_summary else "(no YOLO data)"}

━━━ PLAYER TRACKING (ByteTrack) ━━━
{tracker_summary if tracker_summary else "(tracking unavailable)"}
{json.dumps(tracker_events[:8], indent=2) if tracker_events else ""}

━━━ HUD OCR (EasyOCR) ━━━
{ocr_summary if ocr_summary else "(no HUD text detected)"}
{json.dumps(ocr_kills[:8], indent=2) if ocr_kills else ""}

━━━ AUDIO EVENT DETECTION (Librosa) ━━━
{audio_summary if audio_summary else "(no audio events)"}
{json.dumps(audio_events[:10], indent=2) if audio_events else ""}

━━━ CLIP VISUAL ANALYSIS (CLIP + Action Recognition) ━━━
{clip_summary if clip_summary else "(CLIP unavailable)"}
{json.dumps(clip_concepts[:6], indent=2) if clip_concepts else ""}

━━━ AUDIO TRANSCRIPT (Whisper) ━━━
{whisper_transcript if whisper_transcript else "(no audio/comms detected)"}

━━━ YOUR TASK ━━━
Identify tactical mistakes grounded in the event log above.
If you are uncertain whether a mistake actually happened, use the examine_timestamp tool to verify it before including it.
Only flag what you are confident occurred based on what you observed.

After using any tools you need, return ONLY valid JSON:
{{
  "summary": "2-3 sentences describing exactly what happened and why the round ended this way",
  "loss_reason": "one sentence — the specific observable event that decided the round",
  "phase_breakdown": {{
    "setup": "what happened in the {setup_label}",
    "mid_round": "the pivotal sequence of events in the {mid_label}",
    "endgame": "exactly how it ended — {end_label}"
  }},
  "mistakes": [
    {{
      "team": "{atk} ({role_a}) or {defn} ({role_b})",
      "category": "positioning|utility|timing|decision-making|rotation|communication",
      "severity": "critical|major|minor",
      "description": "At [X]s, I can see... [mistake and consequence]",
      "timestamp": <int seconds>,
      "confidence": <2=clearly visible, 3=unambiguous>,
      "better_alternative": "specific actionable alternative for this exact situation"
    }}
  ],
  "strengths": ["specific observable thing the winning team did well"],
  "key_takeaway": "the single most important coaching point from this round"
}}"""

        # Always use uploaded_file + tools for accuracy.
        # Gemini rejects tools= with cached_content= so we skip the cache here;
        # the cost saving isn't worth losing examine_timestamp verification.
        contents = [uploaded_file, prompt]
        base_config = types.GenerateContentConfig(
            tools=[_TOOLS],
            thinking_config=types.ThinkingConfig(thinking_budget=6000)
        )

        tool_calls_made = []
        logger.info("  [Tactician] Analyzing tactics with tool access...")

        for _ in range(self.MAX_TOOL_CALLS):
            response = self.client.models.generate_content(
                model=self.model, contents=contents, config=base_config
            )

            fcs = response.function_calls
            if not fcs:
                break

            fc   = fcs[0]
            args = dict(fc.args)
            logger.info(f"  [Tactician] Tool call: {fc.name}({args})")
            tool_calls_made.append({"tool": fc.name, "args": args})

            if fc.name == "examine_timestamp":
                tool_result = examine_clip_at_timestamp(
                    uploaded_file, int(args["timestamp"]), args["question"],
                    self.client, cache_name=cache_name
                )
            else:
                tool_result = "Unknown tool"

            contents = contents + [
                response.candidates[0].content,
                types.Content(role="user", parts=[
                    types.Part.from_function_response(
                        name=fc.name, response={"result": tool_result}
                    )
                ])
            ]
            # After first iteration, remove cached_content from config
            # (cached_content only applies to the initial video, not subsequent turns)
            base_config = types.GenerateContentConfig(
                tools=[_TOOLS],
                thinking_config=types.ThinkingConfig(thinking_budget=6000)
            )

        logger.info(f"  [Tactician] {len(tool_calls_made)} tool call(s). Parsing findings...")
        result = _extract_json(response.text)
        if not result or "mistakes" not in result:
            result = {
                "summary":        response.text[:300],
                "loss_reason":    "",
                "phase_breakdown": {},
                "mistakes":       [],
                "strengths":      [],
                "key_takeaway":   "",
            }

        result["mistakes"]   = [m for m in result.get("mistakes", []) if m.get("confidence", 2) >= 2]
        result["tool_calls"] = tool_calls_made
        return result
