"""
Reality Checkpoint — FastAPI application.

Seven endpoints turn a phone-shaped interface into a reason to walk outside:
status, player, storylines, quest generation, reflection evaluation, memory
recall, and a portable journal export.

The AI engine is treated as an *unreliable* dependency. Every path degrades to
the deterministic heuristic engine rather than failing, so the app is fully
playable with Ollama stopped.
"""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import storylines as slib
from ai_engine import AIEngine, get_engine
from database import DEFAULT_PLAYER_ID, Database, get_database
from models import (
    EvaluationResult,
    JournalExport,
    PlayerProfile,
    Quest,
    QuestRequest,
    ReflectionInput,
    Storyline,
    SystemStatus,
)

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
FRONTEND_DIST = os.path.join(PROJECT_DIR, "frontend", "dist")
FRONTEND_INDEX = os.path.join(FRONTEND_DIST, "index.html")


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------


def db() -> Database:
    return get_database()


def engine() -> AIEngine:
    return get_engine()


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.started_at = time.time()

    store = db()
    store.ensure_player(DEFAULT_PLAYER_ID)

    ai = engine()
    await ai.health(force=True)

    try:
        yield
    finally:
        await ai.aclose()


app = FastAPI(
    title="Reality Checkpoint",
    version="1.0.0",
    description="A local-first AI quest engine that sends you back into the physical world.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 1. System status
# ---------------------------------------------------------------------------


@app.get("/api/status", response_model=SystemStatus)
async def status() -> SystemStatus:
    ai = engine()
    health = await ai.health()
    hf_ok = bool(health.get("hf_available"))
    ollama_ok = bool(health.get("ollama_reachable"))
    
    if hf_ok:
        mode = "transformers"
    elif ollama_ok:
        mode = "ollama"
    else:
        mode = "heuristic"

    return SystemStatus(
        hf_available=hf_ok,
        hf_model=health.get("hf_model"),
        hf_latency_ms=health.get("hf_latency_ms"),
        hf_device=health.get("hf_device"),
        ollama_reachable=ollama_ok,
        ollama_model=health.get("ollama_model"),
        ollama_latency_ms=health.get("ollama_latency_ms"),
        available_models=list(health.get("models") or []),
        database="ok",
        ai_mode=mode,
        uptime_seconds=round(time.time() - getattr(app.state, "started_at", time.time()), 3),
    )


# ---------------------------------------------------------------------------
# 2. Player
# ---------------------------------------------------------------------------


@app.get("/api/player", response_model=PlayerProfile)
async def player(player_id: str = Query(default=DEFAULT_PLAYER_ID, max_length=80)) -> PlayerProfile:
    return db().get_player(player_id)


# ---------------------------------------------------------------------------
# 3. Storylines
# ---------------------------------------------------------------------------


@app.get("/api/storylines", response_model=List[Storyline])
async def storylines(
    player_id: str = Query(default=DEFAULT_PLAYER_ID, max_length=80),
) -> List[Storyline]:
    progress = db().storyline_progress(player_id)
    return slib.build_storyline_models(progress)


# ---------------------------------------------------------------------------
# 4. Quest generation
# ---------------------------------------------------------------------------


@app.post("/api/quests/generate", response_model=Quest)
async def generate_quest(request: QuestRequest) -> Quest:
    store = db()
    store.ensure_player(request.player_id)

    memories = store.list_memories(request.player_id, limit=8)
    progress = store.storyline_progress(request.player_id)

    quest = await engine().generate_quest(request, memories, progress)
    return store.create_quest(quest)


@app.get("/api/quests", response_model=List[Quest])
async def quest_history(
    player_id: str = Query(default=DEFAULT_PLAYER_ID, max_length=80),
    limit: int = Query(default=50, ge=1, le=200),
) -> List[Quest]:
    return db().list_quests(player_id, limit)


# ---------------------------------------------------------------------------
# 5. Reflection evaluation
# ---------------------------------------------------------------------------


@app.post("/api/quests/reflect", response_model=EvaluationResult)
async def reflect(payload: ReflectionInput) -> EvaluationResult:
    store = db()

    quest = store.get_quest(payload.quest_id)
    if quest is None:
        raise HTTPException(status_code=404, detail=f"Unknown checkpoint: {payload.quest_id}")

    evaluation = await engine().evaluate_reflection(quest, payload)

    report = store.award_xp(
        payload.player_id,
        xp=evaluation.xp_earned,
        minutes=quest.duration_minutes,
    )
    evaluation.new_level = int(report["level"])
    evaluation.total_xp = int(report["total_xp"])
    evaluation.leveled_up = bool(report["leveled_up"])

    store.save_reflection(
        quest_id=quest.id,
        player_id=payload.player_id,
        reflection_text=payload.reflection_text,
        sensory_rating=payload.sensory_rating,
        evaluation=evaluation,
        new_level=int(report["level"]),
    )

    if evaluation.memory_extracted is not None:
        store.add_memory(evaluation.memory_extracted)

    store.record_storyline_progress(payload.player_id, quest.storyline_id, completed=True)
    store.complete_quest(quest.id)

    return evaluation


# ---------------------------------------------------------------------------
# 6. Memory recall
# ---------------------------------------------------------------------------


@app.get("/api/memories")
async def memories(
    player_id: str = Query(default=DEFAULT_PLAYER_ID, max_length=80),
    search: Optional[str] = Query(default=None, max_length=120),
    category: Optional[str] = Query(default=None, max_length=60),
    limit: int = Query(default=100, ge=1, le=500),
) -> Dict[str, Any]:
    store = db()
    items = store.list_memories(player_id, limit=limit, search=search, category=category)
    return {
        "player_id": player_id,
        "count": len(items),
        "categories": store.memory_categories(player_id),
        "items": [item.model_dump(mode="json") for item in items],
    }


# ---------------------------------------------------------------------------
# 7. Journal export
# ---------------------------------------------------------------------------


def _render_journal(profile: PlayerProfile, store: Database) -> str:
    memories = store.list_memories(profile.id, limit=500)
    quests = store.list_quests(profile.id, limit=200)
    progress = store.storyline_progress(profile.id)
    stats = store.journal_stats(profile.id)

    lines: List[str] = []
    lines.append("# Reality Checkpoint — Field Journal")
    lines.append("")
    lines.append(f"**Explorer:** {profile.name}  ")
    lines.append(f"**Level:** {profile.level}  ")
    lines.append(
        f"**XP:** {profile.xp} / {profile.xp_to_next}  "
    )
    lines.append(f"**Checkpoints completed:** {stats['quests_completed']}  ")
    lines.append(f"**Attention logged:** {profile.total_attention_minutes} minutes  ")
    lines.append(f"**Reality memories:** {stats['memories']}  ")
    lines.append("")

    lines.append("## Storyline progress")
    lines.append("")
    if not progress:
        lines.append("_No arcs started yet._")
    else:
        for sl in slib.SEED_STORYLINES:
            stats_sl = progress.get(sl["id"])
            if not stats_sl:
                continue
            total = len(sl["chapters"])
            done = min(total, int(stats_sl.get("quests_completed", 0)))
            lines.append(f"- **{sl['title']}** — {done}/{total} chapters ({sl['theme']})")
    lines.append("")

    lines.append("## Reality memories")
    lines.append("")
    if not memories:
        lines.append("_Nothing observed yet. Go outside._")
    else:
        current: Optional[str] = None
        for memory in memories:
            if memory.category != current:
                current = memory.category
                lines.append(f"### {current}")
                lines.append("")
            stamp = memory.timestamp.strftime("%Y-%m-%d %H:%M")
            tag_text = f" `#{'` `#'.join(memory.tags)}`" if memory.tags else ""
            lines.append(f"- {memory.observation}{tag_text}  ")
            lines.append(f"  <sub>{stamp} · intensity {memory.intensity}/5</sub>")
        lines.append("")

    lines.append("## Checkpoint log")
    lines.append("")
    completed = [q for q in quests if q.status == "completed"]
    if not completed:
        lines.append("_No completed checkpoints._")
    else:
        for quest in completed:
            lines.append(f"- **{quest.title}** — {quest.storyline_title or quest.storyline_id} · {quest.duration_minutes} min")
            lines.append(f"  <sub>{quest.created_at.strftime('%Y-%m-%d %H:%M')} · via {quest.generated_by}</sub>")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_Generated by Reality Checkpoint. The journal is yours: it never leaves this machine._")
    return "\n".join(lines)


@app.get("/api/journal/export", response_model=JournalExport)
async def journal_export(
    player_id: str = Query(default=DEFAULT_PLAYER_ID, max_length=80),
) -> JournalExport:
    store = db()
    profile = store.get_player(player_id)
    markdown = _render_journal(profile, store)
    return JournalExport(
        player_id=player_id,
        markdown=markdown,
        memory_count=len(store.list_memories(player_id, limit=500)),
    )


# ---------------------------------------------------------------------------
# Static frontend (single-page app)
# ---------------------------------------------------------------------------

if os.path.isdir(FRONTEND_DIST):
    assets = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets):
        app.mount("/assets", StaticFiles(directory=assets), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str):
    """Serve the built SPA; API routes are matched above this catch-all."""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Unknown endpoint")

    if os.path.isfile(FRONTEND_INDEX):
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(FRONTEND_INDEX)

    return JSONResponse(
        status_code=404,
        content={
            "detail": "Frontend build not found. Run ./start.sh or `cd frontend && npm run build`.",
            "api": "/docs",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.environ.get("REALITY_HOST", "0.0.0.0"),
        port=int(os.environ.get("REALITY_PORT", "8000")),
        reload=os.environ.get("REALITY_RELOAD") == "1",
    )
