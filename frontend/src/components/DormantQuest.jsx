import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Bell,
  Compass,
  Eye,
  EyeOff,
  Pause,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

import { formatClock } from '../lib/api.js'

const RADIUS = 116
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

function playChime() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext
    if (!AudioCtx) return
    const ctx = new AudioCtx()
    const now = ctx.currentTime
    const notes = [528, 660, 792]
    notes.forEach((freq, index) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.value = freq
      const start = now + index * 0.18
      gain.gain.setValueAtTime(0.0001, start)
      gain.gain.exponentialRampToValueAtTime(0.16, start + 0.08)
      gain.gain.exponentialRampToValueAtTime(0.0001, start + 3.4)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(start)
      osc.stop(start + 3.6)
    })
    window.setTimeout(() => {
      ctx.close().catch(() => {})
    }, 4200)
  } catch {
    /* audio is a courtesy, never a requirement */
  }
}

export default function DormantQuest({ quest, onReturn }) {
  const total = Math.max(1, (quest?.duration_minutes ?? 10) * 60)

  const [remaining, setRemaining] = useState(total)
  const [running, setRunning] = useState(false)
  const [dimmed, setDimmed] = useState(true)
  const chimed = useRef(false)
  const chime = useRef(playChime)

  useEffect(() => {
    setRemaining(total)
    setRunning(false)
    chimed.current = false
  }, [quest?.id, total])

  useEffect(() => {
    if (!running) return undefined
    const id = window.setInterval(() => {
      setRemaining((value) => (value <= 1 ? 0 : value - 1))
    }, 1000)
    return () => window.clearInterval(id)
  }, [running])

  useEffect(() => {
    if (remaining > 0) return
    setRunning(false)
    if (chimed.current) return
    chimed.current = true
    chime.current()
  }, [remaining])

  const progress = useMemo(() => {
    const done = (total - remaining) / total
    return Math.min(1, Math.max(0, done))
  }, [remaining, total])

  const finished = remaining === 0
  const offset = CIRCUMFERENCE * (1 - progress)

  if (!quest) {
    return (
      <section className="mx-auto w-full max-w-3xl animate-riseIn">
        <div className="panel p-8 text-center">
          <Compass className="mx-auto h-8 w-8 text-ink-3" />
          <p className="mt-4 text-sm text-ink-2">No checkpoint is currently open.</p>
          <button type="button" className="btn-primary mt-6" onClick={onReturn}>
            Back to the portal
          </button>
        </div>
      </section>
    )
  }

  return (
    <section
      className={`mx-auto w-full max-w-5xl animate-riseIn transition-opacity duration-700 ${
        dimmed ? 'opacity-80' : 'opacity-100'
      }`}
    >
      <div className="panel overflow-hidden p-8 sm:p-10">
        <div className="flex flex-col items-center gap-10 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex flex-col items-center">
            <div className="relative h-64 w-64">
              <span className="absolute inset-6 animate-ripple rounded-full border border-sage/25" />
              <span
                className="absolute inset-12 animate-ripple rounded-full border border-sage/15"
                style={{ animationDelay: '1.4s' }}
              />
              <svg viewBox="0 0 256 256" className="relative h-64 w-64 -rotate-90">
                <defs>
                  <linearGradient id="dormant-ring" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#4da97c" />
                    <stop offset="100%" stopColor="#2f6b4f" />
                  </linearGradient>
                </defs>
                <circle
                  cx="128"
                  cy="128"
                  r={RADIUS}
                  fill="none"
                  stroke="rgb(var(--line-strong))"
                  strokeWidth="10"
                />
                <circle
                  cx="128"
                  cy="128"
                  r={RADIUS}
                  fill="none"
                  stroke="url(#dormant-ring)"
                  strokeWidth="10"
                  strokeLinecap="round"
                  strokeDasharray={CIRCUMFERENCE}
                  strokeDashoffset={offset}
                  className="transition-[stroke-dashoffset] duration-1000 ease-linear"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="font-mono text-4xl tracking-tight text-ink">
                  {formatClock(remaining)}
                </span>
                <span className="mt-1 text-[11px] uppercase tracking-[0.25em] text-ink-3">
                  {finished ? 'interval complete' : running ? 'walking' : 'paused'}
                </span>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
              <button
                type="button"
                className="btn-primary"
                onClick={() => setRunning((value) => !value)}
                disabled={finished}
              >
                {running ? (
                  <>
                    <Pause className="h-4 w-4" /> Pause
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" /> {remaining === total ? 'Begin' : 'Resume'}
                  </>
                )}
              </button>
              <button
                type="button"
                className="btn-ghost"
                onClick={() => {
                  setRunning(false)
                  setRemaining(total)
                  chimed.current = false
                }}
              >
                <RotateCcw className="h-4 w-4" /> Reset
              </button>
              <button
                type="button"
                className="btn-ghost"
                onClick={() => setDimmed((value) => !value)}
                aria-pressed={dimmed}
              >
                {dimmed ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                {dimmed ? 'Brighten' : 'Dim'}
              </button>
            </div>

            {finished && (
              <p className="mt-5 flex items-center gap-2 text-sm text-sage">
                <Bell className="h-4 w-4" /> The bell rang. Take one more breath before you return.
              </p>
            )}
          </div>

          <div className="w-full max-w-xl space-y-4">
            <div>
              <span className="label">{quest.storyline_title || 'Field checkpoint'}</span>
              <h2 className="mt-2 font-serif text-2xl text-ink">{quest.title}</h2>
            </div>

            <div className="panel-quiet p-5">
              <span className="label flex items-center gap-2">
                <Sparkles className="h-3.5 w-3.5" /> The mission
              </span>
              <p className="mt-3 whitespace-pre-line text-[15px] leading-relaxed text-ink">
                {quest.mission_prompt}
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="panel-quiet p-5">
                <span className="label">Sensory focus</span>
                <p className="mt-2 text-sm text-ink-2">{quest.sensory_focus}</p>
              </div>
              <div className="panel-quiet p-5">
                <span className="label flex items-center gap-2">
                  <ShieldCheck className="h-3.5 w-3.5" /> Boundaries
                </span>
                <p className="mt-2 text-sm text-ink-2">{quest.safe_boundaries}</p>
              </div>
            </div>

            {quest.memory_anchor && (
              <div className="panel-quiet border-sage/30 p-5">
                <span className="label">Continuity anchor</span>
                <p className="mt-2 font-serif text-sm italic text-ink">
                  {quest.memory_anchor}
                </p>
              </div>
            )}

            <div className="panel-quiet p-5">
              <span className="label">Hold this question</span>
              <p className="mt-2 font-serif text-sm italic text-ink-2">
                {quest.follow_up_prompt}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-1">
              <button type="button" className="btn-primary shadow-glow" onClick={onReturn}>
                I have returned
              </button>
              <span className="text-xs text-ink-3">
                The screen sleeps now. The world does not.
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
