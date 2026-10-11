import { useState } from 'react'
import {
  Compass,
  Flame,
  Footprints,
  Hourglass,
  MapPin,
  Play,
  RotateCw,
  Sparkles,
  Zap,
} from 'lucide-react'

import { MOODS, SENSORY_MODES, TIME_BUDGETS, storylineLabel } from '../lib/api.js'

function Stat({ icon: Icon, label, value, hint }) {
  return (
    <div className="panel-quiet p-3.5">
      <div className="flex items-center gap-2 text-paper-400">
        <Icon className="h-3.5 w-3.5" aria-hidden="true" />
        <span className="label">{label}</span>
      </div>
      <div className="mt-2 stat-value">{value}</div>
      {hint ? <div className="mt-1 text-[11px] text-paper-500">{hint}</div> : null}
    </div>
  )
}

export default function PortalHome({ player, status, error, busy, onBegin, onResume }) {
  const [timeMinutes, setTimeMinutes] = useState(10)
  const [theme, setTheme] = useState('open')
  const [mood, setMood] = useState('curious')
  const [locationHint, setLocationHint] = useState('')

  const active = player?.active_quest
  const level = player?.level ?? 1
  const xp = player?.xp ?? 0
  const xpToNext = player?.xp_to_next ?? 100
  const pct = xpToNext > 0 ? Math.min(100, Math.round((xp / xpToNext) * 100)) : 0

  const handleBegin = () => {
    const payload = { time_minutes: timeMinutes, theme, mood }
    const hint = locationHint.trim()
    if (hint) payload.location_hint = hint
    onBegin(payload)
  }

  return (
    <div className="animate-riseIn space-y-6">
      <section className="panel overflow-hidden p-6 shadow-glow sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="max-w-xl">
            <p className="label">Level {level} · {player?.name || 'Wanderer'}</p>
            <h2 className="mt-2 font-serif text-3xl leading-snug text-paper-50 sm:text-4xl">
              Step through, then put the screen down.
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-paper-300">
              The checkpoint generates a single bespoke mission for the world
              outside your door. Minutes later you come back and describe what
              happened — and the story remembers.
            </p>
          </div>

          <div className="min-w-[15rem] flex-1 rounded-2xl border border-white/[0.06] bg-obsidian-900/60 p-4">
            <div className="flex items-baseline justify-between">
              <span className="label">Attention earned</span>
              <span className="font-mono text-xs text-paper-400">
                {xp} / {xpToNext} xp
              </span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-obsidian-700">
              <div
                className="h-full rounded-full bg-gradient-to-r from-forest-600 to-forest-400 transition-[width] duration-500"
                style={{ width: `${pct}%` }}
              />
            </div>
            <p className="mt-2 text-[11px] text-paper-500">
              {Math.max(0, xpToNext - xp)} xp to level {level + 1}
            </p>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat icon={Footprints} label="Checkpoints" value={player?.quests_completed ?? 0} />
          <Stat
            icon={Hourglass}
            label="Attention"
            value={`${player?.total_attention_minutes ?? 0}m`}
            hint="minutes in the real world"
          />
          <Stat icon={Flame} label="Streak" value={`${player?.streak_days ?? 0}d`} />
          <Stat
            icon={Sparkles}
            label="Mode"
            value={status?.ollama_reachable ? 'Live' : 'Fallback'}
            hint={status?.ollama_model || 'deterministic heuristics'}
          />
        </div>
      </section>

      {active ? (
        <section className="panel flex flex-wrap items-center justify-between gap-4 p-5">
          <div>
            <p className="label">A checkpoint is still open</p>
            <p className="mt-1 font-serif text-lg text-paper-100">{active.title}</p>
            <p className="text-xs text-paper-400">
              {storylineLabel(active.storyline_id)} · {active.duration_minutes} min ·{' '}
              {active.generated_by}
            </p>
          </div>
          <button type="button" className="btn-primary" onClick={onResume}>
            <RotateCw className="h-4 w-4" aria-hidden="true" />
            Resume checkpoint
          </button>
        </section>
      ) : null}

      <section className="panel p-6 sm:p-7">
        <div className="flex items-center gap-2">
          <Compass className="h-4 w-4 text-forest-400" aria-hidden="true" />
          <h3 className="font-serif text-xl text-paper-50">Open a checkpoint</h3>
        </div>

        <div className="mt-6 space-y-6">
          <div>
            <p className="label">Time budget</p>
            <div className="mt-2.5 flex flex-wrap gap-2">
              {TIME_BUDGETS.map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setTimeMinutes(m)}
                  aria-pressed={timeMinutes === m}
                  className={`chip ${timeMinutes === m ? 'chip-active' : ''}`}
                >
                  <Hourglass className="h-3.5 w-3.5" aria-hidden="true" />
                  {m} min
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="label">Sensory focus</p>
            <div className="mt-2.5 flex flex-wrap gap-2">
              {SENSORY_MODES.map((mode) => (
                <button
                  key={mode.id}
                  type="button"
                  onClick={() => setTheme(mode.id)}
                  aria-pressed={theme === mode.id}
                  title={mode.hint}
                  className={`chip ${theme === mode.id ? 'chip-active' : ''}`}
                >
                  {mode.label}
                </button>
              ))}
            </div>
            <p className="mt-2 text-[11px] text-paper-500">
              {SENSORY_MODES.find((m) => m.id === theme)?.hint}
            </p>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="mood">
                Mood walking in
              </label>
              <select
                id="mood"
                className="field mt-2.5"
                value={mood}
                onChange={(e) => setMood(e.target.value)}
              >
                {MOODS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label" htmlFor="hint">
                Where you are (optional)
              </label>
              <div className="relative mt-2.5">
                <MapPin
                  className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-paper-500"
                  aria-hidden="true"
                />
                <input
                  id="hint"
                  className="field pl-9"
                  placeholder="a rooftop, a night market, a stairwell"
                  maxLength={160}
                  value={locationHint}
                  onChange={(e) => setLocationHint(e.target.value)}
                />
              </div>
            </div>
          </div>

          {error ? (
            <p className="rounded-xl border border-amber-400/25 bg-amber-400/[0.06] px-3.5 py-2.5 text-xs text-amber-200">
              {error}
            </p>
          ) : null}

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              className="btn-primary"
              onClick={handleBegin}
              disabled={busy}
            >
              {busy ? (
                <Zap className="h-4 w-4 animate-pulse" aria-hidden="true" />
              ) : (
                <Play className="h-4 w-4" aria-hidden="true" />
              )}
              {busy ? 'Composing your mission…' : 'Begin checkpoint'}
            </button>
            <span className="text-[11px] text-paper-500">
              One mission. No feed. Come back and tell us everything.
            </span>
          </div>
        </div>
      </section>
    </div>
  )
}
