"""
Spatial Observer Agent — powered by NVIDIA cosmos-reason2-8b.

cosmos-reason2-8b is a vision-language model that excels at understanding
the physical world through structured reasoning on video/images.

This agent extracts evenly-spaced frames from the clip and uses cosmos to
analyse spatial positioning: where players are on the map, movement
trajectories, space control, and physical relationships between players.

This is complementary to Gemini (event log) and Pegasus (tactical summary) —
it adds a spatial/positional layer that neither of those focus on.
"""
import logging
from backend.utils.video_processor import extract_key_frames_b64
from backend.utils.nvidia_client import analyze_spatial

logger = logging.getLogger(__name__)

_GAME_SPATIAL_FOCUS = {
    "r6siege": (
        "Focus on: player positions relative to walls, doors, and windows; "
        "which angles are held vs exposed; spatial control of site vs non-site areas; "
        "distance between attackers and defenders at key moments; "
        "whether players are stacked or spread across the map."
    ),
    "valorant": (
        "Focus on: player spread across the map, site control percentages, "
        "which choke points are held vs open, vertical positioning "
        "(elevated vs ground), and distance gaps between teams."
    ),
    "football": (
        "Focus on: team shape compactness, space between defensive and midfield lines, "
        "width utilisation, pressing distances, and space behind the defensive line."
    ),
}


class SpatialObserverAgent:
    FRAME_COUNT = 6  # evenly-spaced frames across the clip

    def run(self, clip_path: str, context: dict) -> str | None:
        """
        Extract frames and run cosmos-reason2-8b spatial analysis.
        Returns: spatial analysis text, or None if NVIDIA unavailable.
        """
        game = context.get("game", "r6siege")
        atk  = context.get("attacking_team", "Attackers")
        defn = context.get("defending_team", "Defenders")
        spatial_focus = _GAME_SPATIAL_FOCUS.get(game, "")

        logger.info(f"  [SpatialObserver] Extracting {self.FRAME_COUNT} frames for cosmos-reason2-8b...")
        frames = extract_key_frames_b64(clip_path, count=self.FRAME_COUNT)
        if not frames:
            logger.warning("  [SpatialObserver] No frames extracted — skipping")
            return None

        prompt = (
            f"{atk} are attacking, {defn} are defending.\n\n"
            f"You are analysing {len(frames)} evenly-spaced frames from a competitive round clip.\n"
            f"Perform spatial/positional analysis only — describe WHERE players are, not what decisions they made.\n\n"
            f"{spatial_focus}\n\n"
            f"For each frame (label them Frame 1 through {len(frames)}):\n"
            f"- Describe the spatial layout: where are attackers, where are defenders?\n"
            f"- What space is controlled vs contested?\n"
            f"- Are there positional advantages or disadvantages visible?\n\n"
            f"End with a summary: what spatial pattern defined this round?"
        )

        logger.info("  [SpatialObserver] Sending frames to cosmos-reason2-8b...")
        result = analyze_spatial(frames, prompt)
        if result:
            logger.info(f"  [SpatialObserver] Spatial analysis: {len(result)} chars")
        else:
            logger.warning("  [SpatialObserver] cosmos-reason2-8b returned no result")
        return result
