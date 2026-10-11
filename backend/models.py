"""
Reality Checkpoint — Pydantic data contracts.

Every payload crossing the API boundary is validated here. The AI engine is
*required* to conform to these shapes, which is what makes quest generation
deterministic even when a local open-weight model drifts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

TimeBudget = Literal[5, 10, 15, 30]
SensoryMode = Literal["visual", "auditory", "tactile", "olfactory", "kinetic", "open"]

STORYLINE_IDS = [
    "architecture-of-shadows",
    "urban-biomecartography",
    "acoustic-commons",
    "micro-physics",
    "ephemeral-encounters",
]

SAFE_BOUNDARY_DEFAULT = (
    "Stay on public ground. Never trespass, never enter private property, "
    "never cross a road while looking at your phone, and never approach a "
    "stranger. Keep your phone in your pocket."
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class QuestRequest(BaseModel):
    """Parameters the player sets in the ~30 second Portal interaction."""

    time_minutes: TimeBudget = 10
    theme: str = Field(default="open", description="Sensory mode or storyline slug.")
    mood: str = Field(default="curious", max_length=80)
    player_id: str = Field(default="local-player", max_length=80)
    storyline_id: Optional[str] = None
    location_hint: Optional[str] = Field(default=None, max_length=160)

    @field_validator("theme")
    @classmethod
    def _normalise_theme(cls, v: str) -> str:
        return (v or "open").strip().lower()

    @field_validator("mood")
    @classmethod
    def _normalise_mood(cls, v: str) -> str:
        return (v or "curious").strip().lower()


class ReflectionInput(BaseModel):
    """What the player reports after returning from the physical world."""

    quest_id: str
    player_id: str = Field(default="local-player", max_length=80)
    reflection_text: str = Field(min_length=1, max_length=8000)
    sensory_rating: int = Field(default=3, ge=1, le=5)
    optional_image_base64: Optional[str] = None


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------


class Quest(BaseModel):
    id: str
    player_id: str = "local-player"
    title: str
    storyline_id: str
    storyline_title: str = ""
    duration_minutes: int
    mission_prompt: str
    sensory_focus: str
    safe_boundaries: str = SAFE_BOUNDARY_DEFAULT
    follow_up_prompt: str
    memory_anchor: Optional[str] = Field(
        default=None,
        description="The past Reality Memory this quest is built on, if any.",
    )
    generated_by: Literal["transformers", "ollama", "heuristic"] = "heuristic"
    model: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    status: Literal["active", "completed", "abandoned"] = "active"


class RealityMemoryItem(BaseModel):
    id: str
    player_id: str = "local-player"
    quest_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=utcnow)
    category: str = "Observation"
    observation: str
    tags: List[str] = Field(default_factory=list)
    continuity_anchor: Optional[str] = Field(
        default=None,
        description="A phrase future quests can reuse to create narrative continuity.",
    )
    intensity: int = Field(default=3, ge=1, le=5)


class EvaluationResult(BaseModel):
    quest_id: str
    xp_earned: int
    quality_score: int = Field(ge=0, le=100)
    feedback: str
    memory_extracted: Optional[RealityMemoryItem] = None
    unlocked_branch: Optional[str] = None
    socratic_question: str
    new_level: int
    total_xp: int
    leveled_up: bool = False
    evaluated_by: Literal["transformers", "ollama", "heuristic"] = "heuristic"
    model: Optional[str] = None


class PlayerProfile(BaseModel):
    id: str
    name: str = "Wanderer"
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    quests_completed: int = 0
    total_attention_minutes: int = 0
    streak_days: int = 0
    active_quest: Optional[Quest] = None
    created_at: datetime = Field(default_factory=utcnow)
    last_seen: datetime = Field(default_factory=utcnow)


class StorylineNode(BaseModel):
    id: str
    title: str
    chapter: int = 1
    state: Literal["locked", "available", "completed"] = "available"
    description: str = ""


class Storyline(BaseModel):
    id: str
    title: str
    theme: str
    description: str
    motif: str = ""
    unlocked: bool = True
    progress: float = 0.0
    quests_completed: int = 0
    branches: List[StorylineNode] = Field(default_factory=list)


class SystemStatus(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "Reality Checkpoint"
    version: str = "1.0.0"
    theme: str = "Hacktoberfest 2026 — Week 1: Touch Grass"
    hf_available: bool = False
    hf_model: Optional[str] = None
    hf_latency_ms: Optional[float] = None
    ollama_reachable: bool = False
    ollama_model: Optional[str] = None
    ollama_latency_ms: Optional[float] = None
    available_models: List[str] = Field(default_factory=list)
    database: str = "ok"
    ai_mode: Literal["transformers", "ollama", "heuristic"] = "heuristic"
    uptime_seconds: float = 0.0
    time: datetime = Field(default_factory=utcnow)


class JournalExport(BaseModel):
    player_id: str
    generated_at: datetime = Field(default_factory=utcnow)
    markdown: str
    memory_count: int = 0


# ---------------------------------------------------------------------------
# Lenient AI-facing schemas
# ---------------------------------------------------------------------------


class AIQuestDraft(BaseModel):
    """Loose shape used to repair whatever the model returns."""

    title: str = "Untitled Checkpoint"
    mission_prompt: str = ""
    sensory_focus: str = "open attention"
    follow_up_prompt: str = "What surprised you?"
    storyline_id: Optional[str] = None
    memory_anchor: Optional[str] = None
    safe_boundaries: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class AIEvaluationDraft(BaseModel):
    xp_earned: int = 25
    quality_score: int = 55
    feedback: str = "You showed up, and that is the whole game."
    observation: Optional[str] = None
    category: str = "Observation"
    tags: List[str] = Field(default_factory=list)
    continuity_anchor: Optional[str] = None
    socratic_question: str = "What did your body notice before your mind did?"
    unlocked_branch: Optional[str] = None
