export const GAME_OPTIONS = [
  'auto','r6siege','valorant','cs2','apex','lol','dota2','overwatch2','mlbb','marvelrivals','custom'
]

export const GAME_NAMES = {
  auto:'Auto-detect', r6siege:'Rainbow Six Siege', valorant:'Valorant',
  cs2:'Counter-Strike 2', apex:'Apex Legends', lol:'League of Legends',
  dota2:'Dota 2', overwatch2:'Overwatch 2', mlbb:'Mobile Legends',
  marvelrivals:'Marvel Rivals', custom:'Custom',
}

export const GAME_TEAMS = {
  auto:['Team A','Team B'], r6siege:['Attackers','Defenders'],
  valorant:['Attackers','Defenders'], cs2:['T Side','CT Side'],
  apex:['Squad','Opponents'], lol:['Blue Side','Red Side'],
  dota2:['Radiant','Dire'], overwatch2:['Attack','Defense'],
  mlbb:['Blue Side','Red Side'], marvelrivals:['Team A','Team B'],
  custom:['Team A','Team B'],
}

export const PIPELINE_STEPS = [
  { label: 'Observe',  desc: 'Observer builds a factual event log from the clip' },
  { label: 'Analyze',  desc: 'Tactician identifies tactical mistakes' },
  { label: 'Debate',   desc: 'Debater adversarially challenges each finding' },
  { label: 'Critic',   desc: 'Critic scores confidence and removes weak findings' },
  { label: 'Coach',    desc: 'Coach writes the final actionable report' },
  { label: 'Enrich',   desc: 'Statistician and Planner add trends and opponent data' },
  { label: 'Predict',  desc: 'Cosmos predicts what would have happened if corrected' },
]

export const AGENT_TO_STEP = {
  detector:0, observer:0, tactician:1, debater:2,
  critic:3, coach:4, statistician:5, planner:5, scenario:6,
}

export const SEV_ORDER = { critical:0, major:1, minor:2 }
