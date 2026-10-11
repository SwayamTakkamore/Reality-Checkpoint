import { useState } from 'react'
import {
  ArrowLeft,
  Brain,
  GitBranch,
  Quote,
  Send,
  Sparkles,
  Star,
  TrendingUp,
  Zap,
} from 'lucide-react'

import { storylineLabel } from '../lib/api.js'

const RATINGS = [1, 2, 3, 4, 5]

function OutcomeCard({ quest, outcome, onFinish }) {
  const memory = outcome?.memory_extracted

  return (
    <div className="animate-riseIn space-y-6">
      <section className="panel p-6 shadow-glow sm:p-8">
        <p className="label">Reflection evaluated</p>
        <h2 className="mt-1.5 font-serif text-2xl text-ink sm:text-3xl">
          {quest?.title}
        </h2>
        <p className="mt-1 text-xs text-ink-3">
          {storylineLabel(quest?.storyline_id)} · evaluated by {outcome?.evaluated_by}
          {outcome?.model ? ` (${outcome.model})` : ''}
        </p>

        {outcome?.leveled_up ? (
          <div className="mt-5 inline-flex items-center gap-2 rounded-xl border border-sage/40 bg-moss/10 px-4 py-3 text-sm text-ink">
            <TrendingUp className="h-4 w-4 text-sage" aria-hidden="true" />
            Level up — you are now level {outcome.new_level}.
          </div>
        ) : null}

        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <div className="panel-quiet p-4">
            <p className="label">XP earned</p>
            <div className="mt-2 stat-value text-sage">+{outcome?.xp_earned ?? 0}</div>
          </div>
          <div className="panel-quiet p-4">
            <p className="label">Depth</p>
            <div className="mt-2 stat-value">{outcome?.quality_score ?? 0}</div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-track">
              <div
                className="h-full rounded-full bg-sage"
                style={{ width: `${outcome?.quality_score ?? 0}%` }}
              />
            </div>
          </div>
          <div className="panel-quiet p-4">
            <p className="label">Level</p>
            <div className="mt-2 stat-value">{outcome?.new_level ?? 1}</div>
            <p className="mt-2 text-[11px] text-ink-3">
              {outcome?.total_xp ?? 0} xp toward the next
            </p>
          </div>
        </div>

        <div className="mt-6 panel-quiet p-4">
          <p className="label inline-flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
            The checkpoint says
          </p>
          <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-ink-2">
            {outcome?.feedback}
          </p>
        </div>

        {outcome?.socratic_question ? (
          <div className="mt-4 panel-quiet border-sage/20 p-4">
            <p className="label inline-flex items-center gap-1.5">
              <Quote className="h-3.5 w-3.5" aria-hidden="true" />
              Carry this outward
            </p>
            <p className="mt-2 font-serif text-lg leading-snug text-ink">
              {outcome.socratic_question}
            </p>
          </div>
        ) : null}

        {memory ? (
          <div className="mt-4 panel-quiet p-4">
            <p className="label inline-flex items-center gap-1.5">
              <Brain className="h-3.5 w-3.5" aria-hidden="true" />
              Reality memory written
            </p>
            <p className="mt-2 text-sm text-ink-2">{memory.observation}</p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="chip">{memory.category}</span>
              {memory.tags?.map((tag) => (
                <span key={tag} className="chip">
                  #{tag}
                </span>
              ))}
              {memory.continuity_anchor ? (
                <span className="text-[11px] text-ink-3">
                  anchor: {memory.continuity_anchor}
                </span>
              ) : null}
            </div>
          </div>
        ) : null}

        {outcome?.unlocked_branch ? (
          <div className="mt-4 inline-flex items-center gap-2 rounded-xl border border-sage/30 bg-moss/12 px-4 py-3 text-sm text-ink">
            <GitBranch className="h-4 w-4 text-sage" aria-hidden="true" />
            New chapter unlocked: {outcome.unlocked_branch.replace(/-/g, ' ')}
          </div>
        ) : null}

        <div className="mt-7">
          <button type="button" className="btn-primary" onClick={onFinish}>
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Return to the portal
          </button>
        </div>
      </section>
    </div>
  )
}

export default function ReflectionChamber({ quest, outcome, busy, error, onSubmit, onFinish }) {
  const [text, setText] = useState('')
  const [rating, setRating] = useState(3)

  if (outcome) {
    return <OutcomeCard quest={quest} outcome={outcome} onFinish={onFinish} />
  }

  const tooShort = text.trim().length < 1

  const handleSubmit = (e) => {
    e.preventDefault()
    if (tooShort || busy) return
    onSubmit({
      quest_id: quest.id,
      reflection_text: text.trim(),
      sensory_rating: rating,
    })
  }

  return (
    <div className="animate-riseIn space-y-6">
      <section className="panel p-6 sm:p-8">
        <p className="label">Reflection chamber</p>
        <h2 className="mt-1.5 font-serif text-2xl text-ink sm:text-3xl">
          What actually happened out there?
        </h2>
        <p className="mt-1 text-xs text-ink-3">
          {quest?.title} · {storylineLabel(quest?.storyline_id)}
        </p>

        <div className="mt-6 panel-quiet border-sage/20 p-4">
          <p className="label inline-flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5" aria-hidden="true" />
            The checkpoint asked
          </p>
          <p className="mt-2 font-serif text-lg leading-snug text-ink">
            {quest?.follow_up_prompt}
          </p>
        </div>

        <form className="mt-6 space-y-6" onSubmit={handleSubmit}>
          <div>
            <label className="label" htmlFor="reflection">
              Your account
            </label>
            <textarea
              id="reflection"
              className="field mt-2.5 min-h-[11rem] resize-y leading-relaxed"
              maxLength={8000}
              placeholder="Write it the way you would tell a friend: what you noticed, what surprised you, what resisted you…"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <div className="mt-1.5 flex justify-between text-[11px] text-ink-3">
              <span>Detail beats polish. Specifics are what the story remembers.</span>
              <span className="font-mono">{text.length}/8000</span>
            </div>
          </div>

          <div>
            <p className="label">Sensory intensity</p>
            <div className="mt-2.5 flex items-center gap-2">
              {RATINGS.map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setRating(n)}
                  aria-label={`Intensity ${n} of 5`}
                  aria-pressed={rating === n}
                  className={`grid h-10 w-10 place-items-center rounded-xl border transition-colors ${
                    rating >= n
                      ? 'border-sage/60 bg-moss/15 text-sage'
                      : 'border-line-strong bg-surface-2 text-ink-3 hover:border-sage/40'
                  }`}
                >
                  <Star
                    className="h-4 w-4"
                    fill={rating >= n ? 'currentColor' : 'none'}
                    aria-hidden="true"
                  />
                </button>
              ))}
              <span className="ml-2 text-[11px] text-ink-3">
                how much the world pressed back
              </span>
            </div>
          </div>

          {error ? (
            <p className="alert">
              {error}
            </p>
          ) : null}

          <div className="flex flex-wrap items-center gap-3">
            <button type="submit" className="btn-primary" disabled={busy || tooShort}>
              <Send className="h-4 w-4" aria-hidden="true" />
              {busy ? 'Weighing your words…' : 'Submit reflection'}
            </button>
            <button type="button" className="btn-ghost" onClick={onFinish} disabled={busy}>
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Abandon checkpoint
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}
