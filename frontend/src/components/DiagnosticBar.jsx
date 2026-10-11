import { Activity, Cpu, Database, RefreshCw, WifiOff } from 'lucide-react'
import { formatDuration } from '../lib/api.js'

export default function DiagnosticBar({ status, error, onRefresh, playerId }) {
  const reachable = Boolean(status?.ollama_reachable)
  const mode = status?.ai_mode
  const offline = Boolean(error) || (!status && !error)

  const tone = error
    ? 'text-paper-400'
    : reachable
      ? 'text-forest-400'
      : 'text-paper-300'

  const dot = error
    ? 'bg-paper-500'
    : reachable
      ? 'bg-forest-400'
      : 'bg-amber-400'

  return (
    <div className="border-b border-white/[0.06] bg-obsidian-950/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center gap-x-5 gap-y-2 px-5 py-2.5 font-mono text-[11px] text-paper-400">
        <span className="inline-flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span
              className={`absolute inline-flex h-full w-full rounded-full ${dot} opacity-60 animate-breathe`}
            />
            <span className={`relative inline-flex h-2 w-2 rounded-full ${dot}`} />
          </span>
          <span className={tone}>
            {error
              ? 'backend unreachable'
              : mode === 'ollama'
                ? 'local model live'
                : 'heuristic mode'}
          </span>
        </span>

        <span className="inline-flex items-center gap-1.5">
          <Cpu className="h-3.5 w-3.5" aria-hidden="true" />
          {status?.ollama_model || 'no model'}
        </span>

        <span className="inline-flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5" aria-hidden="true" />
          {status?.ollama_latency_ms != null
            ? `${Math.round(status.ollama_latency_ms)} ms`
            : '— ms'}
        </span>

        <span className="inline-flex items-center gap-1.5">
          <Database className="h-3.5 w-3.5" aria-hidden="true" />
          db {status?.database || '—'}
        </span>

        <span className="hidden items-center gap-1.5 sm:inline-flex">
          up {status ? formatDuration(status.uptime_seconds) : '—'}
        </span>

        <span className="hidden items-center gap-1.5 lg:inline-flex">
          {playerId}
        </span>

        {status?.available_models?.length ? (
          <span className="hidden items-center gap-1.5 xl:inline-flex">
            {status.available_models.length} model
            {status.available_models.length === 1 ? '' : 's'} installed
          </span>
        ) : null}

        <button
          type="button"
          onClick={onRefresh}
          className="ml-auto inline-flex items-center gap-1.5 rounded-lg border border-white/[0.08] px-2 py-1 text-[11px] text-paper-300 transition-colors hover:border-forest-500/40 hover:text-paper-50"
        >
          {offline ? (
            <WifiOff className="h-3.5 w-3.5" aria-hidden="true" />
          ) : (
            <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
          )}
          probe
        </button>
      </div>

      {error && (
        <div className="mx-auto w-full max-w-6xl px-5 pb-2 font-mono text-[11px] text-amber-300/80">
          {error}
        </div>
      )}
    </div>
  )
}
