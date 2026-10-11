import { useCallback, useEffect, useState } from 'react'
import { BookOpen, Compass, GitFork, Leaf } from 'lucide-react'

import { api, localPlayerId } from './lib/api.js'
import DiagnosticBar from './components/DiagnosticBar.jsx'
import PortalHome from './components/PortalHome.jsx'
import DormantQuest from './components/DormantQuest.jsx'
import ReflectionChamber from './components/ReflectionChamber.jsx'
import FieldJournal from './components/FieldJournal.jsx'
import StorylineTree from './components/StorylineTree.jsx'

const NAV = [
  { id: 'portal', label: 'Portal', icon: Compass },
  { id: 'journal', label: 'Field Journal', icon: BookOpen },
  { id: 'storylines', label: 'Storylines', icon: GitFork },
]

export default function App() {
  const [playerId] = useState(() => localPlayerId())
  const [status, setStatus] = useState(null)
  const [statusError, setStatusError] = useState(null)
  const [player, setPlayer] = useState(null)
  const [view, setView] = useState('portal')
  // idle -> dormant (out in the world) -> reflect (back at the portal)
  const [phase, setPhase] = useState('idle')
  const [quest, setQuest] = useState(null)
  const [outcome, setOutcome] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const loadStatus = useCallback(async () => {
    try {
      const s = await api.status()
      setStatus(s)
      setStatusError(null)
      return s
    } catch (err) {
      setStatusError(err.message)
      return null
    }
  }, [])

  const loadPlayer = useCallback(async () => {
    try {
      const p = await api.player(playerId)
      setPlayer(p)
      return p
    } catch (err) {
      setError(err.message)
      return null
    }
  }, [playerId])

  useEffect(() => {
    loadStatus()
    loadPlayer()
    const timer = setInterval(loadStatus, 30000)
    return () => clearInterval(timer)
  }, [loadStatus, loadPlayer])

  const beginQuest = useCallback(
    async (payload) => {
      setBusy(true)
      setError(null)
      try {
        const created = await api.generateQuest({ ...payload, player_id: playerId })
        setQuest(created)
        setOutcome(null)
        setPhase('dormant')
        setView('portal')
      } catch (err) {
        setError(err.message)
      } finally {
        setBusy(false)
      }
    },
    [playerId],
  )

  const resumeQuest = useCallback(() => {
    if (player?.active_quest) {
      setQuest(player.active_quest)
      setPhase('dormant')
      setView('portal')
    }
  }, [player])

  const backToPortal = useCallback(() => {
    setPhase('reflect')
    setView('portal')
  }, [])

  const submitReflection = useCallback(
    async (payload) => {
      setBusy(true)
      setError(null)
      try {
        const result = await api.reflect({ ...payload, player_id: playerId })
        setOutcome(result)
        await Promise.all([loadPlayer(), loadStatus()])
        return result
      } catch (err) {
        setError(err.message)
        throw err
      } finally {
        setBusy(false)
      }
    },
    [playerId, loadPlayer, loadStatus],
  )

  const finishReflection = useCallback(() => {
    setQuest(null)
    setOutcome(null)
    setPhase('idle')
    setView('portal')
    setError(null)
    loadPlayer()
  }, [loadPlayer])

  const dormant = phase === 'dormant' && quest

  return (
    <div className="flex min-h-full flex-col">
      <DiagnosticBar
        status={status}
        error={statusError}
        onRefresh={loadStatus}
        playerId={playerId}
      />

      <header className="mx-auto w-full max-w-6xl px-5 pt-8 sm:pt-12">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="grid h-11 w-11 place-items-center rounded-2xl border border-forest-500/30 bg-forest-900/40">
              <Leaf className="h-5 w-5 text-forest-400" aria-hidden="true" />
            </span>
            <div>
              <h1 className="font-serif text-2xl leading-tight text-paper-50 sm:text-3xl">
                Reality Checkpoint
              </h1>
              <p className="text-xs text-paper-400">
                A portal, not a destination. Touch grass, then report back.
              </p>
            </div>
          </div>

          <nav className="flex items-center gap-1 rounded-2xl border border-white/[0.06] bg-obsidian-900/60 p-1">
            {NAV.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => setView(id)}
                aria-current={view === id ? 'page' : undefined}
                className={
                  'inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition-colors ' +
                  (view === id
                    ? 'bg-forest-600/25 text-paper-50'
                    : 'text-paper-300 hover:bg-white/[0.04] hover:text-paper-100')
                }
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-5 pb-16 pt-8">
        {view === 'portal' && dormant && (
          <DormantQuest quest={quest} onReturn={backToPortal} />
        )}

        {view === 'portal' && phase === 'reflect' && quest && (
          <ReflectionChamber
            quest={quest}
            outcome={outcome}
            busy={busy}
            error={error}
            onSubmit={submitReflection}
            onFinish={finishReflection}
          />
        )}

        {view === 'portal' && phase === 'idle' && (
          <PortalHome
            player={player}
            status={status}
            error={error}
            busy={busy}
            onBegin={beginQuest}
            onResume={resumeQuest}
          />
        )}

        {view === 'journal' && <FieldJournal playerId={playerId} />}

        {view === 'storylines' && <StorylineTree playerId={playerId} />}
      </main>

      <footer className="mx-auto w-full max-w-6xl px-5 pb-8 text-xs text-paper-500">
        <p>
          Hacktoberfest 2026 · Week 1 — “Touch Grass”. Runs against a local
          open-weight model through Ollama; degrades to deterministic
          heuristics when the model is cold.
        </p>
      </footer>
    </div>
  )
}
