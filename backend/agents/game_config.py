"""
Game/sport configuration for ASC.

Each config defines the coaching framework, phase labels, tactical knowledge,
and round-detection queries for a specific game or sport.

Supports: r6siege, valorant, cs2, apex, lol, dota2, overwatch2, football, custom
"""

# ── R6 Siege ──────────────────────────────────────────────────────────────────
_R6_MAP_KNOWLEDGE = """
RAINBOW SIX SIEGE — TACTICAL FRAMEWORK

OPERATOR ROLES:
- Hard breach (Thermite/Hibana): opens reinforced walls; unused when site is locked = tactical error
- Soft breach (Ash/Sledge): creates new lines of sight; underuse on a congested site is a mistake
- Intel (Drone/Lion/Jackal): pre-round intel is critical; entering site without droning is a recurring error
- Utility denial (Twitch/Thatcher/Bandit): attackers must clear defender gadgets before entry
- Roam (Jäger/Bandit/Vigil): defenders who roam and get caught out-of-position give free map control

COMMON ATTACKER ERRORS:
1. Blind peeks — pushing an angle without droning or utility support first
2. Split timing — part of the team commits to site while others haven't cleared flanks
3. Drone waste — using drones reactively instead of proactively holding angles during the push
4. Utility stacking — throwing multiple grenades at the same spot instead of spreading pressure
5. Late plant — leaving the defuser plant until <20s forces a desperate final push
6. Trading unfavourably — dying and taking the kill with you is only neutral when team is ahead

COMMON DEFENDER ERRORS:
1. Overaggressive roaming — leaving site too thin and getting caught without trading value
2. Anchoring too early — committing to site defence at 1:30+ leaves no map control
3. Unreinforced wall — leaving a reinforceable wall soft invites hard-breach denial
4. Gadget waste — using Nitro Cell or impact grenades too early without a real target
5. 1vX misplay — attempting an open retake against 3+ attackers instead of playing for time

CALLOUTS: Site = objective room. Soft wall = destructible drywall. Hard wall = reinforced.
Flank = lateral/rear approach bypassing main choke. Rotate = move to reinforce another site.
"""

# ── CS2 ───────────────────────────────────────────────────────────────────────
_CS2_MAP_KNOWLEDGE = """
COUNTER-STRIKE 2 — TACTICAL FRAMEWORK

ECONOMY SYSTEM (critical to analyse):
- Full buy: rifle + full utility (>4500 credits)
- Force buy: buying weapons despite losing the previous round
- Eco/save round: spending as little as possible to reset economy
- Bonus round: round following a pistol round win
- Economy misreads — buying when team should save = compounding losses over multiple rounds

T-SIDE CONCEPTS:
- Default: spread across map to gather information before committing
- Execute: coordinated utility dump onto a single site (A or B)
- Fake: creating pressure at one site to rotate CT defenders, then hitting the other
- Split: attacking a site from two angles simultaneously
- Late rotation: one T player lurks mid or B while team pressures A — punishes overrotating CTs

CT-SIDE CONCEPTS:
- Information play: gathering intel without dying (passive holds, AWP angles)
- Aggressive peek: taking early map control but high risk if caught without teammate cover
- Retake: reorganising 1-3 players to take back a planted bomb site
- Cross: covering the other angle on a site while a teammate peeks

UTILITY USAGE:
- Smoke: cuts off sightlines; smoking too early or wrong spots = failed execute
- Flash: blinds enemies before a peek; self-flash or teammate flash = error
- Molotov/HE: zone denial or damage; wasting on an empty site is economy loss
- Not trading utility: throwing a smoke then peeking alone before teammates follow

COMMON ERRORS:
1. Economy mismanagement — buying on a losing force and compounding the deficit
2. Single-file entry — players entering a site one at a time instead of simultaneously
3. Utility waste — smokes/flashes for no purpose, or peeking before utility lands
4. Lurk timing — lurking player commits too late and team is already dead
5. Retake positioning — stacking both players on same angle instead of crossfiring bomb
6. No info before commit — pushing a site without any smokes or flash support
"""

# ── Valorant ──────────────────────────────────────────────────────────────────
_VALORANT_MAP_KNOWLEDGE = """
VALORANT — TACTICAL FRAMEWORK

AGENT ROLES (generalised):
- Duelist (Jett/Reyna/Phoenix): expected to create space and win duels; entry fraggers
- Initiator (Sova/Breach/Skye): reveal and displace enemies before the push
- Sentinel (Killjoy/Cypher): lock down flanks and site post-plant
- Controller (Omen/Brimstone/Viper): smoke key angles for safe executes

COMMON ATTACKER ERRORS:
1. Executes without smokes — pushing a site without controller utility first
2. Post-plant positioning — clustering near the spike instead of spreading to cover all defuse angles
3. Utility dump at start — spending all abilities in the first 30s, leaving the execute dry
4. Lone-wolf entry — a single duelist entering site while teammates wait too long
5. Trading deaths — losing the entry fragger AND the trade kill when ahead in economy

COMMON DEFENDER ERRORS:
1. Over-peeking — going wide off-site and getting caught by multiple attackers
2. Retake timing — committing too late when spike is already planted near wall
3. Solo holding — splitting the site into 1v1 angles rather than cross-covering
4. Flank watch failure — forgetting to check for lurkers once the push begins
"""

# ── Apex Legends ──────────────────────────────────────────────────────────────
_APEX_MAP_KNOWLEDGE = """
APEX LEGENDS — TACTICAL FRAMEWORK

GAME STRUCTURE: Battle royale — 60 squads of 3, no rounds. Survival to final ring = win.

LEGEND ABILITIES:
- Tactical: short cooldown ability used frequently (Bloodhound scan, Wraith phase)
- Passive: always-active perk
- Ultimate: high-impact ability charged over time; hoarding ult charge = mistake

PHASE STRUCTURE:
- Drop: landing location dictates loot quality and early-game fight risk
- Loot phase: split looting vs grouped — splitting too far creates pick vulnerability
- Zone rotation: moving ahead of zone (proactive) vs running from zone (reactive = chip damage)
- Final ring: positioning before the final circles close is the biggest skill differentiator

ENGAGEMENT ERRORS:
1. Third-party vulnerability — fighting in the open while a third squad is nearby
2. Unfavourable positioning — engaging from low ground vs a high-ground opponent
3. No cover — shooting from out in the open rather than using hard cover
4. Ability hoarding — saving tactical/ultimate too long and dying without using it
5. Poor revive timing — attempting to revive while under fire instead of repositioning first
6. Split-squad — one player pushes while two are looting; or two die and leave the third alone
7. No knockdown follow-up — knocking a player but not immediately pushing to finish
8. Zone awareness — losing track of zone timer and taking chip damage while fighting

ROTATION PRINCIPLES:
- Third ring and beyond: always know the next safe zone before committing to a fight
- Rotate through buildings for cover; open rotations are punished at high level
- Drop positions that funnel enemies toward you are better than isolated high-ground
"""

# ── League of Legends ─────────────────────────────────────────────────────────
_LOL_MAP_KNOWLEDGE = """
LEAGUE OF LEGENDS — TACTICAL FRAMEWORK

GAME STRUCTURE: 5v5 MOBA on Summoner's Rift. Win by destroying the enemy Nexus.
No traditional rounds — analysis covers game phases and key decision moments.

ROLES: Top, Jungle, Mid, Bot (ADC), Support

PHASE STRUCTURE:
- Early game / laning (0–14 min): CSing, trading, level-up spikes, first blood, Rift Herald
- Mid game / objectives (14–25 min): dragon stacks, tower pressure, Baron setup, roaming
- Late game / teamfights (25+ min): Baron, Elder Dragon, Inhibitors, base siege

KEY CONCEPTS:
- CS (Creep Score): missing CS under tower, diving for CS = positioning errors
- Vision control: warding river/jungle before objectives; lack of vision before Baron/Dragon = critical mistake
- Resource trading: killing a dragon but losing 3 players in the process = net negative
- Wave management: letting waves crash into turrets, not slow-pushing before roaming
- Objective timing: not starting Baron/Dragon immediately when enemy is dead or recalled

COMMON ERRORS:
1. Overextending in lane without vision — dying to a jungle gank that was preventable with a ward
2. Taking an unfavourable teamfight — engaging 5v5 when a key ultimate is on cooldown
3. Not collapsing on an objective — letting the enemy start Baron/Dragon uncontested
4. Poor recall timing — recalling when the wave is pushed in, losing CS and wave pressure
5. Tunnelling on a fight — chasing a kill while enemy team takes Baron or Inhibitor
6. Flawed priority — winning a team fight but not converting it into a tower, inhibitor, or Nexus push
7. No vision before Dragon/Baron — attempting objective without vision of enemy jungler
"""

# ── Dota 2 ────────────────────────────────────────────────────────────────────
_DOTA2_MAP_KNOWLEDGE = """
DOTA 2 — TACTICAL FRAMEWORK

GAME STRUCTURE: 5v5 MOBA. Win by destroying the Ancient. Farm, itemise, and take objectives.

ROLES: Carry (1), Mid (2), Offlane (3), Soft Support (4), Hard Support (5)

PHASE STRUCTURE:
- Early game / laning (0–12 min): last hits, denies, pulling, roshan ward
- Mid game / farming/skirmishes (12–25 min): item timings, Roshan, towers, smoke ganks
- Late game / high-ground siege (25+ min): Buybacks, Aegis timing, Barracks, Ancient

KEY CONCEPTS:
- Last hits and denies: missing creep waves under tower is a gold disadvantage
- Item timing spikes: hero power spikes around key items (BKB, Aghanim's); delaying these = weak timing window missed
- Smoke ganks: five-man smoke to take an unaware kill; smoke wasted on a warded area = bad call
- Buyback: saving gold to instantly respawn after death; dying without buyback in late-game = loss condition
- High ground: attacking high-ground without Aegis or BKB = almost always a mistake

COMMON ERRORS:
1. Greedy farming — continuing to farm while team fights a disadvantageous 4v5
2. Bad Roshan timing — attempting Roshan without vision of all 5 enemy heroes
3. No buyback gold — dying at a critical moment without the option to immediately re-enter
4. Wasting BKB — using Black King Bar on a non-threatening spell, saving it means it was wasted
5. Overextending into high-ground — pushing without Aegis or overwhelming numbers
6. Poor vision — not having observer wards on key rune spots or enemy jungle routes
7. Ignoring lanes — winning a fight but not converting it into a Barracks push
"""

# ── Overwatch 2 ───────────────────────────────────────────────────────────────
_OW2_MAP_KNOWLEDGE = """
OVERWATCH 2 — TACTICAL FRAMEWORK

GAME STRUCTURE: 5v5 team-based. Push/Control/Escort/Hybrid modes. Win through objective control.

ROLES: Tank (1), DPS (2), Support (2)

PHASE STRUCTURE:
- Setup / approach: both teams positioning before main engagement
- Main fight: full team engagement on point or payload
- Post-fight / reset: losing team regroups and re-engages; winning team consolidates position

ULTIMATE ECONOMY:
- Ultimate tracking: knowing which enemy ultimates are ready changes when to engage
- Wasting ultimates: using a high-value ultimate on 1-2 enemies instead of saving for a 5-player fight
- Losing the ultimate race: engaging when enemies have more ready ultimates = likely wipe

COMMON ERRORS:
1. Feeding the enemy tank — DPS diving the tank instead of the vulnerable backline
2. No peel for supports — tank/DPS ignoring an enemy flanker killing supports
3. Splitting before a fight — one player pushed ahead of the team and gets picked first
4. Poor ultimate usage — using Earthshatter/Sound Barrier/Nano before a fight is fully committed
5. Ignoring high-ground — contesting a point from low ground against an enemy that holds high
6. Wrong focus target — killing the least threatening enemy instead of the support or squishiest DPS
7. No off-angle — whole team pushing the same narrow angle; no flanker applying cross-pressure
8. Over-chasing — chasing a low-health enemy out of position while losing the team fight
"""

# ── Mobile Legends: Bang Bang ─────────────────────────────────────────────────
_MLBB_MAP_KNOWLEDGE = """
MOBILE LEGENDS: BANG BANG — TACTICAL FRAMEWORK

ROLES:
- Roamer/Tank: creates vision, initiates fights, peels for carries — dying without absorbing pressure = wasted
- Fighter (Exp Lane): duel for solo lane, sidelane split-push, 1v1 matchup knowledge
- Assassin/Mage (Mid Lane): rotates to help both sides; staying mid too long after winning lane = slow
- Marksman (Gold Lane): farm-dependent carry; dying early = crippled scaling
- Support: heals, crowd control; playing too aggressively without a kill threat = feeding

OBJECTIVES (critical to analyse):
- Turtle (spawns 4 min, every 3 min after): grants gold bonus; conceding it without a fight = free gold lead
- Lord (spawns 15 min, every 3 min after): pushes a lane when escorted; not using Lord push after winning fight = wasted momentum
- Towers: destroying Outer → Inner → Base tower creates lane pressure; ignoring tower after a fight = lost advantage
- Lithowanderer (Crab): minor gold objectives in river — often ignored when a fight is available

PHASE STRUCTURE:
- Early (0–5 min): jungle invade risk, buff control, first Turtle contest, lane assignments
- Mid game (5–15 min): turtle stacking, rotation to help losing lanes, first Lord at 15 min
- Late game (15+ min): Lord rushes, 5-man push, base siege

COMMON ERRORS:
1. Not contesting Turtle — farming while enemy takes free Turtle = compounding gold deficit
2. Lord waste — killing Lord but no one escorts it; enemy clears it for free
3. Poor rotation — mid/roamer not helping a losing Gold Lane; marksman dies for free
4. Ult hoarding — saving ultimate until the team fight is already over
5. No vision before Lord — initiating Lord without knowing enemy positions = stolen
6. Overextension — split-pushing too deep without backup while Lord spawns
7. Bad engage — roamer initiates without CC chain set up; team can't follow
8. Ignoring objectives after a win — chasing kills instead of taking towers or Lord
"""

# ── Marvel Rivals ─────────────────────────────────────────────────────────────
_MARVEL_RIVALS_MAP_KNOWLEDGE = """
MARVEL RIVALS — TACTICAL FRAMEWORK

GAME STRUCTURE: 6v6 team-based hero shooter. Modes: Convoy (Escort), Convergence (Push), Domination (Control).

ROLES:
- Vanguard (Tank): creates space, absorbs damage, enables team to push or hold; over-extending alone = wasted
- Duelist (DPS): eliminates priority targets; focusing the tank instead of the support = inefficient
- Strategist (Support): sustains the team; standing still in the open = easy pick

TEAM-UP ABILITIES:
- Certain hero combinations unlock bonus team-up skills — not using a team-up that's available = free power wasted
- Switching heroes mid-match to activate a team-up can swing a fight

ULTIMATE ECONOMY:
- Ultimate charge builds through damage dealt and received — trading ults evenly is neutral, using fewer ults to win a fight = advantage
- Holding ultimate too long into a lost fight = wasted charge
- Using an ultimate on 1-2 enemies when the full team is grouped = low value

COMMON ERRORS:
1. Focus-fire failure — team shooting different targets instead of collapsing on one
2. Feeding the Vanguard — DPS diving the tank who has max HP and sustain, ignoring the backline
3. No peel for Strategist — support dies to a flanker while tank/DPS ignore it
4. Splitting before a fight — one player pushes ahead, gets picked, and team fights 5v6
5. Ult into a lost fight — using high-value ultimates when already losing the teamfight instead of saving for next
6. Wrong mode priority — killing enemies instead of pushing/contesting the objective
7. Ignoring team-ups — playing heroes that have a team-up together but not positioning to activate it
8. No off-angle — whole team attacking from one direction; no flanker applying cross-pressure
"""


def _build_custom_config(description: str) -> dict:
    """Generic coaching config for user-described games."""
    desc = description.strip() or "a competitive team-based game"
    return {
        "name":                 "Custom Game",
        "min_round_seconds":    30,
        "max_round_seconds":    900,
        "min_gap_between_rounds": 15,
        "round_start_queries":  ["match start round begin game start"],
        "round_end_queries":    ["match end round over game over"],
        "key_event_queries":    {},
        "map_knowledge":        "",
        "team_role_a":          "Team A",
        "team_role_b":          "Team B",
        "phase_labels": {
            "setup":     "Opening Phase",
            "mid_round": "Mid-Game",
            "endgame":   "Final Phase",
        },
        "coaching_prompt": (
            f"You are an expert coach analysing {desc}.\n"
            "Analyse the clip for tactical mistakes based on this game's objectives and mechanics. "
            "Focus on: team coordination, positioning relative to objectives, decision-making under pressure, "
            "resource usage, timing of key actions, and failure to capitalise on advantages. "
            "Be specific to the game's mechanics when identifying mistakes and alternatives."
        ),
    }


GAME_CONFIGS = {
    "r6siege": {
        "name": "Rainbow Six Siege",
        "min_round_seconds": 60,
        "max_round_seconds": 280,
        "min_gap_between_rounds": 120,
        "round_start_queries": [
            "rainbow six siege score overlay HUD top of screen round number",
            "R6 siege preparation phase 45 second countdown timer blue",
        ],
        "round_end_queries": [
            "rainbow six siege score changed round won team victory",
            "rainbow six siege VICTORY DEFEAT round result screen",
        ],
        "key_event_queries": {
            "first_kill": "operator eliminated kill feed first blood rainbow six siege",
            "flank_kill": "operator flanked from behind surprised kill rainbow six siege",
            "clutch":     "one vs one clutch last player alive rainbow six siege",
            "trade":      "trade kill immediate revenge elimination rainbow six siege",
        },
        "map_knowledge": _R6_MAP_KNOWLEDGE,
        "team_role_a":  "Attackers",
        "team_role_b":  "Defenders",
        "phase_labels": {
            "setup":     "Prep Phase / Drone Phase",
            "mid_round": "Mid-Round / Flanks & Rotations",
            "endgame":   "Site Execute / Plant / Retake / Clutch",
        },
        "coaching_prompt": (
            "You are an expert Rainbow Six Siege esports coach. "
            "You understand operator abilities, site setups, rotation timings, "
            "defuser plants, eco rounds, and team coordination. "
            "Focus on KILL AND DEATH analysis: "
            "First kill of the round sets the tempo — analyse who died first and why. "
            "Flank kills indicate a failure to check or cover flanks. "
            "Traded kills mean a player took a bad duel that cost the team numbers advantage. "
            "Clutch situations (1vX) arise from poor team coordination earlier in the round. "
            "Untraded deaths (opponent gets a kill with no punishment) are critical errors. "
            "Always name the specific type of mistake: bad peek, unchecked flank, "
            "unpunished push, bad trade, drone misuse, no utility before peeking."
        ),
    },

    "valorant": {
        "name": "Valorant",
        "min_round_seconds": 60,
        "max_round_seconds": 200,
        "min_gap_between_rounds": 100,
        "round_start_queries": [
            "valorant buy phase round start shopping timer",
            "valorant round number scoreboard top center",
        ],
        "round_end_queries": [
            "valorant round over victory defeat spike exploded defused",
            "valorant score changed round won",
        ],
        "key_event_queries": {
            "first_kill": "player eliminated first blood kill feed valorant",
            "flank_kill": "player flanked from behind surprised valorant",
            "clutch":     "one vs one clutch last player alive valorant",
            "trade":      "trade kill immediate revenge elimination valorant",
        },
        "map_knowledge": _VALORANT_MAP_KNOWLEDGE,
        "team_role_a":  "Attackers",
        "team_role_b":  "Defenders",
        "phase_labels": {
            "setup":     "Buy Phase / Early Positioning",
            "mid_round": "Mid-Round / Information & Duels",
            "endgame":   "Site Execute / Post-plant / Clutch",
        },
        "coaching_prompt": (
            "You are an expert Valorant esports coach. "
            "You understand agent abilities, site execution, retake timing, "
            "spike plants and defuses, economy management, and team composition. "
            "Give specific, actionable coaching advice."
        ),
    },

    "cs2": {
        "name": "Counter-Strike 2",
        "min_round_seconds": 60,
        "max_round_seconds": 115,
        "min_gap_between_rounds": 25,
        "round_start_queries": [
            "counter-strike round start freeze time buy menu",
            "CS2 round timer top of screen buy phase",
        ],
        "round_end_queries": [
            "counter-strike round over bomb defused bomb exploded all eliminated",
            "CS2 round win screen T CT victory",
        ],
        "key_event_queries": {
            "first_kill":  "first blood kill feed counter-strike player eliminated",
            "bomb_plant":  "bomb planted counter-strike site A B",
            "clutch":      "one vs one clutch CS2 last player alive",
            "economy":     "buy menu weapon purchase counter-strike eco force buy",
        },
        "map_knowledge": _CS2_MAP_KNOWLEDGE,
        "team_role_a":  "T Side",
        "team_role_b":  "CT Side",
        "phase_labels": {
            "setup":     "Buy Phase / Early Info & Mid Control",
            "mid_round": "Default / Map Control / Information",
            "endgame":   "Execute / Retake / Post-plant / Clutch",
        },
        "coaching_prompt": (
            "You are an expert Counter-Strike 2 coach. "
            "You understand economy management (full-buy, force-buy, eco, bonus rounds), "
            "utility usage (smokes, flashes, molotovs), map control, execute timing, "
            "retake coordination, and individual duel decisions. "
            "Always comment on economy state when relevant — a bad force-buy compounds over rounds. "
            "Flag utility waste, trading failures, single-file entries, and peeking without support. "
            "Identify whether the round was won or lost in the economy phase, the info phase, or the execute."
        ),
    },

    "apex": {
        "name": "Apex Legends",
        "min_round_seconds": 300,
        "max_round_seconds": 1800,
        "min_gap_between_rounds": 60,
        "round_start_queries": [
            "apex legends match start jump ship banner select character",
            "apex legends dropping from ship legend select",
        ],
        "round_end_queries": [
            "apex legends champion squad victory screen",
            "apex legends you were eliminated knocked down match over",
        ],
        "key_event_queries": {
            "knock":    "player knocked down apex legends",
            "third_party": "third party squad ambush apex legends",
            "zone":     "zone circle closing ring damage apex legends",
            "rotation": "squad rotating moving position apex legends",
        },
        "map_knowledge": _APEX_MAP_KNOWLEDGE,
        "team_role_a":  "Squad",
        "team_role_b":  "Opponents",
        "phase_labels": {
            "setup":     "Drop / Landing / Early Loot",
            "mid_round": "Mid-game / Zone Rotation / Fights",
            "endgame":   "Final Rings / Last Squads",
        },
        "coaching_prompt": (
            "You are an expert Apex Legends coach. "
            "You understand battle royale positioning, zone rotation timing, "
            "legend ability usage, third-party awareness, engagement decision-making, "
            "revive prioritisation, and squad coordination. "
            "Focus on: when to engage vs disengage, cover usage, rotation proactivity vs reactivity, "
            "ability timing, and split-squad vulnerability. "
            "Always consider whether the engagement was favourable given zone position, third-party risk, and ability states."
        ),
    },

    "lol": {
        "name": "League of Legends",
        "min_round_seconds": 1200,
        "max_round_seconds": 4800,
        "min_gap_between_rounds": 0,
        "round_start_queries": [
            "league of legends game start minions spawn nexus",
            "lol loading screen summoner's rift champions",
        ],
        "round_end_queries": [
            "league of legends victory defeat nexus destroyed",
            "gg wp game over league of legends",
        ],
        "key_event_queries": {
            "first_blood": "first blood kill league of legends",
            "dragon":      "dragon slain objective league of legends",
            "baron":       "baron nashor slain objective league of legends",
            "teamfight":   "team fight multiple kills league of legends",
        },
        "map_knowledge": _LOL_MAP_KNOWLEDGE,
        "team_role_a":  "Blue Side",
        "team_role_b":  "Red Side",
        "phase_labels": {
            "setup":     "Early Game / Laning Phase (0–14 min)",
            "mid_round": "Mid Game / Objectives & Rotations (14–25 min)",
            "endgame":   "Late Game / High-stakes Teamfights & Base Siege (25+ min)",
        },
        "coaching_prompt": (
            "You are an expert League of Legends coach. "
            "You understand laning fundamentals (CS, trading, wave management), "
            "jungle pathing and objective control (Dragon, Baron, Rift Herald), "
            "vision control (warding, sweeping), teamfight positioning, "
            "item timing spikes, and macro decision-making. "
            "Focus on: resource conversion (did a fight lead to an objective?), "
            "vision before objectives, overextension without vision, "
            "ultimates used prematurely, and missed objective windows. "
            "Always explain WHY a decision was wrong in the context of the game state."
        ),
    },

    "dota2": {
        "name": "Dota 2",
        "min_round_seconds": 1200,
        "max_round_seconds": 6000,
        "min_gap_between_rounds": 0,
        "round_start_queries": [
            "dota 2 game start radiant dire ancient",
            "dota 2 loading screen hero selection",
        ],
        "round_end_queries": [
            "dota 2 victory radiant dire ancient destroyed gg",
            "dota 2 game over defeat screen",
        ],
        "key_event_queries": {
            "first_blood": "first blood kill dota 2",
            "roshan":      "roshan killed aegis dota 2",
            "teamfight":   "team fight multiple deaths dota 2",
            "buyback":     "buyback gold hero respawned dota 2",
        },
        "map_knowledge": _DOTA2_MAP_KNOWLEDGE,
        "team_role_a":  "Radiant",
        "team_role_b":  "Dire",
        "phase_labels": {
            "setup":     "Early Game / Laning (0–12 min)",
            "mid_round": "Mid Game / Item Timings & Skirmishes (12–25 min)",
            "endgame":   "Late Game / Roshan, Buybacks & Base (25+ min)",
        },
        "coaching_prompt": (
            "You are an expert Dota 2 coach. "
            "You understand laning (last hits, denies, pulling, trilane vs dual lane), "
            "item timing spikes (BKB, Aghanim's, Refresher), smoke ganks, "
            "Roshan decision-making, buyback economy, "
            "high-ground siege timing, and courier management. "
            "Focus on: was Roshan attempted safely? Did a team fight lead to barracks? "
            "Were buybacks available at critical moments? Was BKB used correctly? "
            "Did a smoke gank succeed or reveal poor ward coverage?"
        ),
    },

    "overwatch2": {
        "name": "Overwatch 2",
        "min_round_seconds": 60,
        "max_round_seconds": 600,
        "min_gap_between_rounds": 30,
        "round_start_queries": [
            "overwatch 2 round start objective point payload assault",
            "overwatch 2 control point attack defend",
        ],
        "round_end_queries": [
            "overwatch 2 victory defeat round over team won",
            "overwatch 2 objective captured payload delivered",
        ],
        "key_event_queries": {
            "teamfight": "team fight multiple kills overwatch",
            "ult":       "ultimate used overwatch ability hero",
            "spawn":     "team wiped respawning overwatch",
        },
        "map_knowledge": _OW2_MAP_KNOWLEDGE,
        "team_role_a":  "Attack",
        "team_role_b":  "Defense",
        "phase_labels": {
            "setup":     "Approach / High-ground Contest",
            "mid_round": "Main Fight / Point Contest",
            "endgame":   "Post-fight / Overtime / Last Stand",
        },
        "coaching_prompt": (
            "You are an expert Overwatch 2 coach. "
            "You understand tank/DPS/support synergy, ultimate economy and tracking, "
            "high-ground advantage, focus-fire target priority, "
            "support peel and survivability, and objective conversion. "
            "Focus on: ultimate timing (used too early/late?), focus-fire consistency, "
            "whether the tank created space or fed, and whether supports had enough peel. "
            "Always consider the mode — Push, Control, Escort, and Hybrid have different priorities."
        ),
    },

    "mlbb": {
        "name": "Mobile Legends: Bang Bang",
        "min_round_seconds": 600,
        "max_round_seconds": 2400,
        "min_gap_between_rounds": 0,
        "round_start_queries": [
            "mobile legends bang bang match start minions spawn loading",
            "mlbb game start battle begin nexus",
        ],
        "round_end_queries": [
            "mobile legends victory defeat base destroyed gg",
            "mlbb game over winner screen",
        ],
        "key_event_queries": {
            "turtle":    "turtle killed objective mlbb mobile legends",
            "lord":      "lord killed objective mlbb mobile legends",
            "teamfight": "team fight multiple kills mobile legends",
            "tower":     "tower destroyed mobile legends",
        },
        "map_knowledge": _MLBB_MAP_KNOWLEDGE,
        "team_role_a":  "Blue Side",
        "team_role_b":  "Red Side",
        "phase_labels": {
            "setup":     "Early Game / Laning & Buff Control (0–5 min)",
            "mid_round": "Mid Game / Turtle Stacking & Rotations (5–15 min)",
            "endgame":   "Late Game / Lord Rush & Base Siege (15+ min)",
        },
        "coaching_prompt": (
            "You are an expert Mobile Legends: Bang Bang coach. "
            "You understand role assignments (Roamer, Fighter, Mid, Gold Lane, Support), "
            "objective priority (Turtle, Lord, towers), rotation timing, "
            "ultimate economy, and team-fight initiation. "
            "Focus on: was Turtle/Lord contested? Did the team convert kills into objectives? "
            "Was the roamer in the right place? Were ultimates used at the right moment? "
            "Did the gold laner survive lane phase safely? "
            "Always tie mistakes back to objective control — killing the enemy matters less than taking Lord."
        ),
    },

    "marvelrivals": {
        "name": "Marvel Rivals",
        "min_round_seconds": 60,
        "max_round_seconds": 600,
        "min_gap_between_rounds": 20,
        "round_start_queries": [
            "marvel rivals round start match begin hero select",
            "marvel rivals objective convoy convergence domination start",
        ],
        "round_end_queries": [
            "marvel rivals victory defeat round over team won",
            "marvel rivals objective captured payload delivered",
        ],
        "key_event_queries": {
            "teamfight": "team fight multiple eliminations marvel rivals",
            "ult":       "ultimate ability used marvel rivals hero power",
            "objective": "objective captured payload pushed marvel rivals",
        },
        "map_knowledge": _MARVEL_RIVALS_MAP_KNOWLEDGE,
        "team_role_a":  "Team A",
        "team_role_b":  "Team B",
        "phase_labels": {
            "setup":     "Approach / Composition Setup",
            "mid_round": "Main Fight / Objective Contest",
            "endgame":   "Post-fight / Overtime / Final Push",
        },
        "coaching_prompt": (
            "You are an expert Marvel Rivals coach. "
            "You understand Vanguard/Duelist/Strategist roles, ultimate economy, "
            "team-up ability activation, focus-fire discipline, support peel, "
            "and objective mode priorities (Convoy, Convergence, Domination). "
            "Focus on: did the team focus the right target? Were ultimates used efficiently? "
            "Was the Strategist protected? Did the team activate available team-ups? "
            "Was the objective prioritised over chasing kills? "
            "Always consider the game mode — pushing payload vs contesting a point require different positioning."
        ),
    },
}

# Slug → display name mapping (for UI and auto-detection)
GAME_DISPLAY_NAMES = {k: v["name"] for k, v in GAME_CONFIGS.items()}
GAME_DISPLAY_NAMES["auto"]   = "Auto-detect"
GAME_DISPLAY_NAMES["custom"] = "Other / Custom"

# Slug → (team_a_label, team_b_label) for UI
GAME_TEAM_LABELS = {k: (v.get("team_role_a", "Team A"), v.get("team_role_b", "Team B"))
                    for k, v in GAME_CONFIGS.items()}
GAME_TEAM_LABELS["auto"]   = ("Team A", "Team B")
GAME_TEAM_LABELS["custom"] = ("Team A", "Team B")


def get_config(game: str, custom_description: str = "") -> dict:
    if game in GAME_CONFIGS:
        return GAME_CONFIGS[game]
    # "custom" or unrecognised slug
    return _build_custom_config(custom_description)


def detect_game(vod_filename: str) -> str:
    """Infer game from VOD filename. Falls back to r6siege."""
    name = vod_filename.lower()
    if any(k in name for k in ["valorant", "valo"]):
        return "valorant"
    if any(k in name for k in ["csgo", "cs2", "counter"]):
        return "cs2"
    if any(k in name for k in ["marvel", "rivals", "marvelrivals"]):
        return "marvelrivals"
    if any(k in name for k in ["mlbb", "mobilelegends", "mobile_legends"]):
        return "mlbb"
    if any(k in name for k in ["apex"]):
        return "apex"
    if any(k in name for k in ["league", "leagueoflegends"]):
        return "lol"
    if any(k in name for k in ["dota", "dota2"]):
        return "dota2"
    if any(k in name for k in ["overwatch", "ow2"]):
        return "overwatch2"
    return "r6siege"
