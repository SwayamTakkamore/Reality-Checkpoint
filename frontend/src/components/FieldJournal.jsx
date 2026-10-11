import { useCallback, useEffect, useRef, useState } from 'react'
import { BookOpen, Download, Loader2, Search, X } from 'lucide-react'

import { api, formatWhen } from '../lib/api.js'

function buildFilename() {
  const now = new Date()
  const stamp = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
  ].join('-')
  return `reality-checkpoint-journal-${stamp}.md`
}

export default function FieldJournal({ playerId }) {
  const [items, setItems] = useState([])
  const [categories, setCategories] = useState([])
  const [count, setCount] = useState(0)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState(false)
  const timer = useRef(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.memories({
        playerId,
        search: search.trim() || undefined,
        category: category || undefined,
      })
      setItems(data?.items || [])
      setCategories(data?.categories || [])
      setCount(data?.count ?? (data?.items || []).length)
      setError('')
    } catch (err) {
      setError(err?.message || 'The journal could not be read.')
      setItems([])
      setCount(0)
    } finally {
      setLoading(false)
    }
  }, [playerId, search, category])

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(load, 220)
    return () => {
      if (timer.current) clearTimeout(timer.current)
    }
  }, [load])

  const exportJournal = async () => {
    setExporting(true)
    try {
      const data = await api.journal(playerId)
      const markdown = data?.markdown || ''
      const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = buildFilename()
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      setError('')
    } catch (err) {
      setError(err?.message || 'The journal could not be exported.')
    } finally {
      setExporting(false)
    }
  }

  const filtered = Boolean(search.trim() || category)

  return (
    <div className="animate-riseIn space-y-6">
      <section className="panel p-6 sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="label">Field journal</p>
            <h2 className="mt-1.5 font-serif text-2xl text-ink sm:text-3xl">
              What the world has told you
            </h2>
            <p className="mt-1 text-xs text-ink-3">
              {count} {count === 1 ? 'memory' : 'memories'} recorded
              {filtered ? ' matching this filter' : ' so far'}
            </p>
          </div>
          <button
            type="button"
            className="btn"
            onClick={exportJournal}
            disabled={exporting}
          >
            {exporting ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Download className="h-4 w-4" aria-hidden="true" />
            )}
            Export markdown
          </button>
        </div>

        <div className="mt-6 space-y-4">
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-3"
              aria-hidden="true"
            />
            <input
              type="search"
              className="field pl-10"
              placeholder="Search observations, tags, anchors…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search the field journal"
            />
            {search ? (
              <button
                type="button"
                onClick={() => setSearch('')}
                aria-label="Clear search"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-3 transition-colors hover:text-ink"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            ) : null}
          </div>

          {categories.length ? (
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => setCategory('')}
                className={`chip ${category === '' ? 'chip-active' : ''}`}
              >
                All
              </button>
              {categories.map((name) => (
                <button
                  key={name}
                  type="button"
                  onClick={() => setCategory(name === category ? '' : name)}
                  className={`chip ${category === name ? 'chip-active' : ''}`}
                >
                  {name}
                </button>
              ))}
            </div>
          ) : null}
        </div>

        {error ? <p className="alert mt-5">{error}</p> : null}
      </section>

      <section className="panel p-6 sm:p-8">
        {loading ? (
          <div className="flex items-center justify-center gap-2 py-16 text-sm text-ink-3">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            Reading the journal…
          </div>
        ) : items.length === 0 ? (
          <div className="py-14 text-center">
            <BookOpen
              className="mx-auto h-7 w-7 text-ink-3"
              aria-hidden="true"
            />
            <p className="mt-3 font-serif text-lg text-ink">
              {filtered ? 'Nothing matches that yet.' : 'The journal is still blank.'}
            </p>
            <p className="mt-1.5 text-sm text-ink-3">
              {filtered
                ? 'Try a different word or clear the filter.'
                : 'Complete a checkpoint and your observations will gather here.'}
            </p>
          </div>
        ) : (
          <ul className="space-y-3">
            {items.map((memory) => (
              <li key={memory.id} className="panel-quiet p-4 sm:p-5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="chip">{memory.category}</span>
                  {memory.tags?.map((tag) => (
                    <span key={tag} className="chip">
                      #{tag}
                    </span>
                  ))}
                  <span className="ml-auto font-mono text-[11px] text-ink-3">
                    {formatWhen(memory.timestamp)}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-relaxed text-ink-2">
                  {memory.observation}
                </p>
                {memory.continuity_anchor ? (
                  <p className="mt-3 border-l-2 border-sage/40 pl-3 text-[11px] italic text-sage">
                    anchor: {memory.continuity_anchor}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
