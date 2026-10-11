import { Activity, Cpu, Database, RefreshCw, WifiOff } from 'lucide-react'
import { formatDuration } from '../lib/api.js'

export default function DiagnosticBar({ status, error, onRefresh, playerId }) {
  const isHf = Boolean(status?.hf_available)
  const isOllama = Boolean(status?.ollama_reachable)
  const reachable = isHf || isOllama
  const mode = status?.ai_mode
  const offline = Boolean(error) || (!status && !error)

  const activeModel = status?.hf_model || status?.ollama_model || 'no model'
  const activeLatency = status?.hf_latency_ms ?? status?.ollama_latency_ms

  const tone = error
    ? 'text-ink-3'
    : reachable
      ? 'text-sage'
      : 'text-ink-2'

  const dot = error
    ? 'bg-ink-3'
    : reachable
      ? 'bg-sage'
      : 'bg-amber'

  return (
    <div className="border-b border-line bg-surface/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center gap-x-5 gap-y-2 px-5 py-2.5 font-mono text-[11px] text-ink-3">
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
              : mode === 'transformers'
                ? 'HuggingFace local'
                : mode === 'ollama'
                  ? 'Ollama local'
                  : 'heuristic mode'}
          </span>
        </span>

        <span className="inline-flex items-center gap-1.5">
          <Cpu className="h-3.5 w-3.5" aria-hidden="true" />
          {activeModel}
        </span>

        <span className="inline-flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5" aria-hidden="true" />
          {activeLatency != null
            ? `${Math.round(activeLatency)} ms`
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
            {status.available_models.length === 1 ? '' : 's'} loaded
          </span>
        ) : null}

        <button
          type="button"
          onClick={onRefresh}
          className="ml-auto inline-flex items-center gap-1.5 rounded-lg border border-line-strong px-2 py-1 text-[11px] text-ink-2 transition-colors hover:border-sage/50 hover:text-ink"
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
        <div className="mx-auto w-full max-w-6xl px-5 pb-2 font-mono text-[11px] text-amber-ink">
          {error}
        </div>
      )}
    </div>
  )
}
