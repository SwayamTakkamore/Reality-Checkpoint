import { useEffect, useState } from 'react'
import { Check, GitBranch, Loader2, Lock, Unlock } from 'lucide-react'

import { api } from '../lib/api.js'

const STATE_TONE = {
  completed: {
    icon: Check,
    badge: 'border-forest-500/50 bg-forest-500/15 text-forest-400',
    label: 'completed',
  },
  available: {
    icon: Unlock,
    badge: 'border-forest-400/35 bg-forest-900/40 text-paper-100',
    label: 'available',
  },
  locked: {
    icon: Lock,
    badge: 'border-white/[0.08] bg-white/[0.02] text-paper-500',
    label: 'locked',
  },
}

function NodeRow({ node }) {
  const tone = STATE_TONE[node?.state] || STATE_TONE.locked
  const Icon = tone.icon

  return (
    <li className="flex gap-3 rounded-xl border border-white/[0.05] bg-white/[0.015] p-3">
      <span
        className={`mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg border ${tone.badge}`}
      >
        <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      </span>
      <div className="min-w-0">
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
          <p className="text-sm text-paper-100">{node.title}</p>
          <span className="font-mono text-[10px] uppercase tracking-wide text-paper-500">
            ch. {node.chapter ?? 1} · {tone.label}
          </span>
        </div>
        {node.description ? (
          <p className="mt-1 text-xs leading-relaxed text-paper-400">
            {node.description}
          </p>
        ) : null}
      </div>
    </li>
  )
}

export default function StorylineTree({ playerId }) {
  const [storylines, setStorylines] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    ;(async () => {
      setLoading(true)
      try {
        const data = await api.storylines(playerId)
        if (!alive) return
        setStorylines(data?.storylines || data || [])
        setError('')
      } catch (err) {
        if (!alive) return
        setError(err?.message || 'The storylines could not be read.')
        setStorylines([])
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [playerId])

  return (
    <div className="animate-riseIn space-y-6">
      <section className="panel p-6 sm:p-8">
        <p className="label">Storyline tree</p>
        <h2 className="mt-1.5 font-serif text-2xl text-paper-50 sm:text-3xl">
          The arcs your checkpoints are growing
        </h2>
        <p className="mt-1 text-xs text-paper-400">
          Each checkpoint advances a storyline and opens the next chapter.
        </p>
      </section>

      {error ? (
        <p className="rounded-xl border border-amber-400/25 bg-amber-400/[0.06] px-3.5 py-2.5 text-xs text-amber-200">
          {error}
        </p>
      ) : null}

      {loading ? (
        <section className="panel flex items-center justify-center gap-2 py-16 text-sm text-paper-400">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          Mapping the storylines…
        </section>
      ) : storylines.length === 0 ? (
        <section className="panel py-14 text-center">
          <GitBranch
            className="mx-auto h-7 w-7 text-paper-500"
            aria-hidden="true"
          />
          <p className="mt-3 font-serif text-lg text-paper-100">
            No storylines recorded yet.
          </p>
          <p className="mt-1.5 text-sm text-paper-400">
            Begin a checkpoint from the portal to plant the first arc.
          </p>
        </section>
      ) : (
        storylines.map((storyline) => {
          const progressPct = Math.round((storyline.progress || 0) * 100)
          return (
            <section key={storyline.id} className="panel p-6 sm:p-8">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0">
                  <h3 className="font-serif text-xl text-paper-50">
                    {storyline.title}
                  </h3>
                  {storyline.motif ? (
                    <p className="mt-1 text-xs italic text-forest-400">
                      {storyline.motif}
                    </p>
                  ) : null}
                </div>
                <span className="chip">
                  {storyline.quests_completed ?? 0} completed
                </span>
              </div>

              {storyline.description ? (
                <p className="mt-3 text-sm leading-relaxed text-paper-300">
                  {storyline.description}
                </p>
              ) : null}

              <div className="mt-5">
                <div className="flex items-center justify-between font-mono text-[11px] text-paper-500">
                  <span>progress</span>
                  <span>{progressPct}%</span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-obsidian-700">
                  <div
                    className="h-full rounded-full bg-forest-500 transition-[width] duration-500"
                    style={{ width: `${progressPct}%` }}
                  />
                </div>
              </div>

              {storyline.branches?.length ? (
                <ul className="mt-5 space-y-2.5">
                  {storyline.branches.map((node) => (
                    <NodeRow key={node.id} node={node} />
                  ))}
                </ul>
              ) : null}
            </section>
          )
        })
      )}
    </div>
  )
}
