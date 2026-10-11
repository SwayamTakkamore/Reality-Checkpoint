"""
Reality Checkpoint — SQLite persistence layer.

Privacy by design: everything lives in one local file (`reality_checkpoint.db`)
using WAL mode so reads never block the journal timeline. No network calls,
no telemetry, no third-party storage.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Iterator, List, Optional

from models import (
    EvaluationResult,
    PlayerProfile,
    Quest,
    RealityMemoryItem,
    SAFE_BOUNDARY_DEFAULT,
)

DEFAULT_DB_PATH = os.environ.get("REALITY_DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "reality_checkpoint.db"))

DEFAULT_PLAYER_ID = "local-player"

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT 'Wanderer',
    level INTEGER NOT NULL DEFAULT 1,
    xp INTEGER NOT NULL DEFAULT 0,
    quests_completed INTEGER NOT NULL DEFAULT 0,
    total_attention_minutes INTEGER NOT NULL DEFAULT 0,
    streak_days INTEGER NOT NULL DEFAULT 0,
    last_seen TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quests (
    id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL,
    title TEXT NOT NULL,
    storyline_id TEXT NOT NULL,
    storyline_title TEXT NOT NULL DEFAULT '',
    duration_minutes INTEGER NOT NULL,
    mission_prompt TEXT NOT NULL,
    sensory_focus TEXT NOT NULL,
    safe_boundaries TEXT NOT NULL,
    follow_up_prompt TEXT NOT NULL,
    memory_anchor TEXT,
    generated_by TEXT NOT NULL DEFAULT 'heuristic',
    model TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players (id)
);

CREATE TABLE IF NOT EXISTS reflections (
    id TEXT PRIMARY KEY,
    quest_id TEXT NOT NULL,
    player_id TEXT NOT NULL,
    reflection_text TEXT NOT NULL,
    sensory_rating INTEGER NOT NULL DEFAULT 3,
    quality_score INTEGER NOT NULL DEFAULT 0,
    xp_earned INTEGER NOT NULL DEFAULT 0,
    feedback TEXT,
    socratic_question TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reality_memories (
    id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL,
    quest_id TEXT,
    category TEXT NOT NULL DEFAULT 'Observation',
    observation TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    continuity_anchor TEXT,
    intensity INTEGER NOT NULL DEFAULT 3,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS storylines (
    id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL,
    storyline_id TEXT NOT NULL,
    quests_completed INTEGER NOT NULL DEFAULT 0,
    unlocked INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL,
    UNIQUE (player_id, storyline_id)
);

CREATE INDEX IF NOT EXISTS idx_memories_player ON reality_memories (player_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_quests_player ON quests (player_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reflections_quest ON reflections (quest_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def xp_for_level(level: int) -> int:
    """Quadratic-ish curve so later levels genuinely feel earned."""
    return 100 + (level - 1) * 75


class Database:
    """Thin, explicit SQLite wrapper. Connections are per-call and row-dict based."""

    def __init__(self, path: str = DEFAULT_DB_PATH, model_placeholder: Any = None) -> None:
        self.path = path
        self._ensure_schema()

    # -- plumbing ---------------------------------------------------------

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    # -- players ----------------------------------------------------------

    def ensure_player(self, player_id: str = DEFAULT_PLAYER_ID, name: str = "Wanderer") -> PlayerProfile:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO players (id, name, level, xp, created_at, last_seen) VALUES (?,?,?,?,?,?)",
                    (player_id, name, 1, 0, _now(), _now()),
                )
        return self.get_player(player_id)

    def get_player(self, player_id: str = DEFAULT_PLAYER_ID) -> PlayerProfile:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
        if row is None:
            return self.ensure_player(player_id)
        level = int(row["level"] or 1)
        xp = int(row["xp"] or 0)
        profile = PlayerProfile(
            id=row["id"],
            name=row["name"] or "Wanderer",
            level=level,
            xp=xp,
            xp_to_next=xp_for_level(level),
            quests_completed=int(row["quests_completed"] or 0),
            total_attention_minutes=int(row["total_attention_minutes"] or 0),
            streak_days=int(row["streak_days"] or 0),
            created_at=_parse(row["created_at"]),
            last_seen=_parse(row["last_seen"]),
        )
        profile.active_quest = self.get_active_quest(player_id)
        return profile

    def award_xp(self, player_id: str, xp: int, minutes: int = 0) -> Dict[str, Any]:
        """Add XP, roll levels, and return a report suitable for the API."""
        with self.connect() as conn:
            row = conn.execute("SELECT level, xp, quests_completed, total_attention_minutes FROM players WHERE id = ?", (player_id,)).fetchone()
            if row is None:
                raise KeyError(player_id)
            level = int(row["level"] or 1)
            total = int(row["xp"] or 0) + max(0, int(xp))
            completions = int(row["quests_completed"] or 0) + 1
            attention = int(row["total_attention_minutes"] or 0) + max(0, int(minutes))
            leveled = False
            while total >= xp_for_level(level):
                total -= xp_for_level(level)
                level += 1
                leveled = True
            conn.execute(
                "UPDATE players SET level=?, xp=?, quests_completed=?, total_attention_minutes=?, last_seen=? WHERE id=?",
                (level, total, completions, attention, _now(), player_id),
            )
        return {
            "level": level,
            "xp": total,
            "xp_to_next": xp_for_level(level),
            "total_xp": total,
            "leveled_up": leveled,
            "quests_completed": completions,
            "total_attention_minutes": attention,
        }

    # -- quests -----------------------------------------------------------

    def create_quest(self, quest: Quest) -> Quest:
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO quests (id, player_id, title, storyline_id, storyline_title,
                   duration_minutes, mission_prompt, sensory_focus, safe_boundaries,
                   follow_up_prompt, memory_anchor, generated_by, model, status, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    quest.id,
                    quest.player_id,
                    quest.title,
                    quest.storyline_id,
                    quest.storyline_title,
                    quest.duration_minutes,
                    quest.mission_prompt,
                    quest.sensory_focus,
                    quest.safe_boundaries,
                    quest.follow_up_prompt,
                    quest.memory_anchor,
                    quest.generated_by,
                    quest.model,
                    quest.status,
                    quest.created_at.isoformat(),
                ),
            )
            # Only one live checkpoint per player at a time.
            conn.execute(
                "UPDATE quests SET status='abandoned' WHERE player_id=? AND id != ? AND status='active'",
                (quest.player_id, quest.id),
            )
        return quest

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM quests WHERE id = ?", (quest_id,)).fetchone()
        return _row_to_quest(row) if row else None

    def get_active_quest(self, player_id: str = DEFAULT_PLAYER_ID) -> Optional[Quest]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM quests WHERE player_id=? AND status='active' ORDER BY created_at DESC LIMIT 1",
                (player_id,),
            ).fetchone()
        return _row_to_quest(row) if row else None

    def complete_quest(self, quest_id: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE quests SET status='completed' WHERE id=?", (quest_id,))

    def abandon_quest(self, quest_id: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE quests SET status='abandoned' WHERE id=?", (quest_id,))

    def list_quests(self, player_id: str = DEFAULT_PLAYER_ID, limit: int = 50) -> List[Quest]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM quests WHERE player_id=? ORDER BY created_at DESC LIMIT ?",
                (player_id, max(1, min(200, limit))),
            ).fetchall()
        return [_row_to_quest(r) for r in rows]

    # -- reflections & memories ------------------------------------------

    def save_reflection(
        self,
        quest_id: str,
        player_id: str,
        reflection_text: str,
        sensory_rating: int,
        evaluation: EvaluationResult,
        new_level: int,
    ) -> str:
        rid = _new_id("refl")
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO reflections (id, quest_id, player_id, reflection_text,
                   sensory_rating, quality_score, xp_earned, feedback, socratic_question, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    rid,
                    quest_id,
                    player_id,
                    reflection_text,
                    int(sensory_rating),
                    int(evaluation.quality_score),
                    int(evaluation.xp_earned),
                    evaluation.feedback,
                    evaluation.socratic_question,
                    _now(),
                ),
            )
        return rid

    def add_memory(self, memory: RealityMemoryItem) -> RealityMemoryItem:
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO reality_memories (id, player_id, quest_id, category, observation,
                   tags, continuity_anchor, intensity, created_at) VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    memory.id,
                    memory.player_id,
                    memory.quest_id,
                    memory.category,
                    memory.observation,
                    json.dumps(memory.tags),
                    memory.continuity_anchor,
                    int(memory.intensity),
                    memory.timestamp.isoformat(),
                ),
            )
        return memory

    def list_memories(
        self,
        player_id: str = DEFAULT_PLAYER_ID,
        limit: int = 100,
        search: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[RealityMemoryItem]:
        sql = "SELECT * FROM reality_memories WHERE player_id = ?"
        params: List[Any] = [player_id]
        if search:
            sql += " AND (observation LIKE ? OR tags LIKE ? OR category LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like, like])
        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(max(1, min(500, limit)))
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_row_to_memory(r) for r in rows]

    def memory_categories(self, player_id: str = DEFAULT_PLAYER_ID) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT category, COUNT(*) as count FROM reality_memories WHERE player_id=? GROUP BY category ORDER BY count DESC",
                (player_id,),
            ).fetchall()
        return [{"category": r["category"], "count": int(r["count"])} for r in rows]

    def recent_memory_anchors(self, player_id: str = DEFAULT_PLAYER_ID, limit: int = 4) -> List[str]:
        with self.connect() as conn:
            rows = conn.execute(
                """SELECT observation, continuity_anchor FROM reality_memories
                   WHERE player_id=? ORDER BY created_at DESC LIMIT ?""",
                (player_id, max(1, limit)),
            ).fetchall()
        anchors: List[str] = []
        for r in rows:
            anchor = r["continuity_anchor"] or r["observation"]
            if anchor:
                anchors.append(str(anchor))
        return anchors

    # -- storylines -------------------------------------------------------

    def record_storyline_progress(self, player_id: str, storyline_id: str, completed: bool = True) -> Dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM storylines WHERE player_id=? AND storyline_id=?",
                (player_id, storyline_id),
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO storylines (id, player_id, storyline_id, quests_completed, unlocked, updated_at) VALUES (?,?,?,?,?,?)",
                    (_new_id("sl"), player_id, storyline_id, 1 if completed else 0, 1, _now()),
                )
                count = 1 if completed else 0
            else:
                count = int(row["quests_completed"]) + (1 if completed else 0)
                conn.execute(
                    "UPDATE storylines SET quests_completed=?, updated_at=? WHERE player_id=? AND storyline_id=?",
                    (count, _now(), player_id, storyline_id),
                )
        return {"storyline_id": storyline_id, "quests_completed": count}

    def storyline_progress(self, player_id: str = DEFAULT_PLAYER_ID) -> Dict[str, Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM storylines WHERE player_id=?", (player_id,)).fetchall()
        return {
            r["storyline_id"]: {
                "quests_completed": int(r["quests_completed"]),
                "unlocked": bool(r["unlocked"]),
            }
            for r in rows
        }

    # -- journal ----------------------------------------------------------

    def journal_stats(self, player_id: str = DEFAULT_PLAYER_ID) -> Dict[str, int]:
        with self.connect() as conn:
            mem = conn.execute("SELECT COUNT(*) c FROM reality_memories WHERE player_id=?", (player_id,)).fetchone()["c"]
            q = conn.execute("SELECT COUNT(*) c FROM quests WHERE player_id=? AND status='completed'", (player_id,)).fetchone()["c"]
        return {"memories": int(mem), "quests_completed": int(q)}

    # -- housekeeping -----------------------------------------------------

    def reset(self) -> None:
        with self.connect() as conn:
            for table in ("reality_memories", "reflections", "quests", "storylines", "players"):
                conn.execute(f"DELETE FROM {table}")


# ---------------------------------------------------------------------------
# Row helpers
# ---------------------------------------------------------------------------


def _parse(value: Optional[str]) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _row_to_quest(row: sqlite3.Row) -> Quest:
    return Quest(
        id=row["id"],
        player_id=row["player_id"],
        title=row["title"],
        storyline_id=row["storyline_id"],
        storyline_title=row["storyline_title"] or "",
        duration_minutes=int(row["duration_minutes"]),
        mission_prompt=row["mission_prompt"],
        sensory_focus=row["sensory_focus"],
        safe_boundaries=row["safe_boundaries"] or SAFE_BOUNDARY_DEFAULT,
        follow_up_prompt=row["follow_up_prompt"],
        memory_anchor=row["memory_anchor"],
        generated_by=row["generated_by"] or "heuristic",
        model=row["model"],
        status=row["status"] or "active",
        created_at=_parse(row["created_at"]),
    )


def _row_to_memory(row: sqlite3.Row) -> RealityMemoryItem:
    try:
        tags = json.loads(row["tags"] or "[]")
    except (json.JSONDecodeError, TypeError):
        tags = []
    return RealityMemoryItem(
        id=row["id"],
        player_id=row["player_id"],
        quest_id=row["quest_id"],
        category=row["category"] or "Observation",
        observation=row["observation"],
        tags=tags if isinstance(tags, list) else [],
        continuity_anchor=row["continuity_anchor"],
        intensity=int(row["intensity"] or 3),
        timestamp=_parse(row["created_at"]),
    )


_SINGLETON: Optional[Database] = None


def get_database(path: Optional[str] = None) -> Database:
    """Shared instance (tests inject their own path instead)."""
    global _SINGLETON
    if path is not None:
        return Database(path)
    if _SINGLETON is None:
        _SINGLETON = Database(os.environ.get("REALITY_DB_PATH", DEFAULT_DB_PATH))
    return _SINGLETON
