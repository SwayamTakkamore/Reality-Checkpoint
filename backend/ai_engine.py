"""
Reality Checkpoint — AI Engine.

Talks to a **local, open-weight model** (Ollama, default `glm-4.7-flash`) and
never to a cloud API. That is the whole point of Pillar C: the player's most
intimate descriptions — what they saw, smelled, felt on their own street —
never leave the machine.

Reliability contract
--------------------
1. Ask the model for strict JSON (`format: "json"` + a schema in the system prompt).
2. Repair the reply: strip fences, find the outermost object, coerce fields.
3. If *anything* goes wrong — timeout, bad JSON, unsafe content, missing model —
   fall back to a deterministic heuristic generator that uses the same inputs.
4. The caller never sees an exception. It only sees `generated_by`.

`heuristic` mode is therefore not a degraded mode; it is a guaranteed floor.
"""

from __future__ import annotations

import json
import os
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

import safety
import storylines as slib
from models import (
    AIEvaluationDraft,
    AIQuestDraft,
    EvaluationResult,
    Quest,
    QuestRequest,
    RealityMemoryItem,
    ReflectionInput,
)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "glm-4.7-flash")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "45"))

CATEGORY_VOCAB = [
    "Observation", "Sound", "Texture", "Light", "Movement", "Place",
    "Creature", "Material", "Weather", "People", "Memory", "Insight",
]

SENSORY_WORDS = {
    "visual": ["light", "shadow", "colour", "color", "bright", "dark", "glow", "shade", "reflection", "hue", "silhouette", "contrast"],
    "auditory": ["sound", "noise", "quiet", "hum", "echo", "rhythm", "silence", "tone", "chime", "drip", "rustle", "distant"],
    "tactile": ["texture", "rough", "smooth", "cold", "warm", "grain", "grit", "soft", "hard", "weight", "pressure", "touch"],
    "olfactory": ["smell", "scent", "odour", "odor", "fragrance", "musty", "fresh", "sharp", "sweet", "damp"],
    "kinetic": ["wind", "breeze", "motion", "sway", "drift", "movement", "moving", "swung", "shifted", "flow"],
}

SPECIFICITY_MARKERS = ["because", "noticed", "realised", "realized", "instead", "although", "then", "after", "before", "while", "which", "that"]

VAGUE_PHRASES = ["nothing much", "it was fine", "it was ok", "it was okay", "idk", "dunno", "nothing happened", "pretty cool", "pretty nice"]

INSIGHT_MARKERS = ["learned", "wonder", "question", "remember", "felt like", "reminded", "realised", "realized", "suddenly", "for the first time"]


def _clamp(value: Any, low: int, high: int, default: int) -> int:
    try:
        return max(low, min(high, int(float(value))))
    except (TypeError, ValueError):
        return default


def _clean_text(value: Any, default: str = "") -> str:
    if not isinstance(value, str):
        return default
    text = re.sub(r"\s{2,}", " ", value).strip()
    return text or default


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Pull the first JSON object out of a model reply, fences and all."""
    if not text:
        return None
    candidate = text.strip()
    candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
    candidate = re.sub(r"\s*```$", "", candidate)
    for attempt in (candidate, candidate[candidate.find("{"): candidate.rfind("}") + 1] if "{" in candidate else ""):
        if not attempt:
            continue
        try:
            parsed = json.loads(attempt)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return None


class AIEngine:
    """Local-model quest generator and reflection evaluator."""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        timeout: float = OLLAMA_TIMEOUT,
        enabled: bool = True,
        rng: Optional[random.Random] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.enabled = enabled and os.environ.get("REALITY_DISABLE_OLLAMA") != "1"
        self.rng = rng or random.Random()
        self._client: Optional[httpx.AsyncClient] = None
        self._health: Dict[str, Any] = {
            "reachable": False,
            "latency_ms": None,
            "models": [],
            "checked_at": 0.0,
        }

    # -- client -----------------------------------------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=3.0),
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    async def health(self, force: bool = False) -> Dict[str, Any]:
        """Cheap probe of the local daemon; cached for 15 seconds."""
        now = time.time()
        if not force and now - float(self._health.get("checked_at", 0)) < 15:
            return self._health
        if not self.enabled:
            self._health = {"reachable": False, "latency_ms": None, "models": [], "checked_at": now}
            return self._health
        started = time.perf_counter()
        try:
            client = await self._get_client()
            resp = await client.get("/api/tags")
            resp.raise_for_status()
            models = [m.get("name", "") for m in resp.json().get("models", [])]
            self._health = {
                "reachable": True,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "models": models,
                "checked_at": now,
            }
        except Exception:
            self._health = {"reachable": False, "latency_ms": None, "models": [], "checked_at": now}
        return self._health

    # -- low-level generation --------------------------------------------

    async def _chat_json(self, system: str, user: str, temperature: float = 0.85) -> Optional[Dict[str, Any]]:
        """One structured-JSON turn. Returns None on any failure (never raises)."""
        if not self.enabled:
            return None
        try:
            client = await self._get_client()
        except Exception:
            return None
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": temperature, "top_p": 0.9, "num_predict": 700},
        }
        for attempt in range(2):
            try:
                resp = await client.post("/api/chat", json=payload)
                if resp.status_code >= 400:
                    return None
                body = resp.json()
                content = (body.get("message") or {}).get("content") or ""
                parsed = extract_json(content)
                if parsed is not None:
                    return parsed
            except Exception:
                if attempt == 1:
                    return None
                continue
        return None

    # -- quest generation -------------------------------------------------

    def _quest_system_prompt(self) -> str:
        return (
            "You are the Quest Architect for Reality Checkpoint, a game that sends a person "
            "OUTSIDE and AWAY from their phone.\n\n"
            "Absolute rules:\n"
            "- The quest must be completable on PUBLIC ground, on foot, with no equipment.\n"
            "- Never suggest trespassing, private property, restricted or abandoned sites.\n"
            "- Never suggest crossing roads while distracted, approaching strangers, climbing "
            "heights, entering water, spending money, or doing anything illegal or destructive.\n"
            "- The player puts the phone away: the mission must be memorable, not checkable.\n"
            "- Reference and build on the player's past Reality Memories when supplied, so the "
            "world feels continuous rather than random.\n\n"
            "Reply with JSON only, using exactly these keys:\n"
            '{"title": "short evocative title", "mission_prompt": "2-4 sentences of concrete '
            'instruction", "sensory_focus": "the sense and phenomenon to attend to", '
            '"follow_up_prompt": "one question the player answers on return", '
            '"safe_boundaries": "one sentence of safety guidance"}'
        )

    def _quest_user_prompt(
        self,
        request: QuestRequest,
        storyline: Dict[str, Any],
        chapter: Dict[str, Any],
        memories: List[RealityMemoryItem],
        anchors: List[str],
    ) -> str:
        memory_block = "none yet — this is their first checkpoint"
        if memories:
            lines = [f"- [{m.category}] {m.observation}" for m in memories[:6]]
            memory_block = "\n".join(lines)
        anchor_block = "\n".join(f"- {a}" for a in anchors[:4]) if anchors else "none"
        return (
            f"Player mood: {request.mood}\n"
            f"Time budget: {request.time_minutes} minutes (do not exceed it)\n"
            f"Sensory focus requested: {request.theme}\n"
            f"Storyline: {storyline['title']} — {storyline['description']}\n"
            f"Storyline motif: {storyline['motif']}\n"
            f"Chapter: {chapter['title']} — {chapter['description']}\n"
            f"Chapter intent to honour: {chapter['prompt'].format(minutes=request.time_minutes)}\n"
            f"Location hint: {safety.sanitise_hint(request.location_hint) or 'unspecified urban environment'}\n\n"
            f"Player's Reality Memories (most recent first):\n{memory_block}\n\n"
            f"Continuity anchors to weave in if natural:\n{anchor_block}\n\n"
            "Write the next checkpoint. Make it feel like it was written for this player today."
        )

    async def generate_quest(
        self,
        request: QuestRequest,
        memories: Optional[List[RealityMemoryItem]] = None,
        progress: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Quest:
        memories = memories or []
        progress = progress or {}
        storyline = slib.pick_storyline(
            theme=request.theme,
            requested=request.storyline_id,
            progress=progress,
            seed=len(memories),
        )
        completed = int(progress.get(storyline["id"], {}).get("quests_completed", 0))
        chapter_id = slib.next_chapter(storyline["id"], completed)
        chapter = slib.get_chapter(chapter_id) or storyline["chapters"][0]
        anchors = [m.continuity_anchor for m in memories if m.continuity_anchor][:4]

        draft: Optional[AIQuestDraft] = None
        used_model: Optional[str] = None
        if self.enabled:
            raw = await self._chat_json(
                self._quest_system_prompt(),
                self._quest_user_prompt(request, storyline, chapter, memories, anchors),
            )
            if raw is not None:
                candidate = self._coerce_quest_draft(raw)
                if candidate is not None:
                    ok, violations, _ = safety.validate_quest(
                        candidate.title, candidate.mission_prompt, candidate.follow_up_prompt, candidate.sensory_focus
                    )
                    if ok and candidate.mission_prompt:
                        draft = candidate
                        used_model = self.model

        generated_by = "ollama"
        if draft is None:
            draft = self._heuristic_quest(request, storyline, chapter, anchors)
            generated_by = "heuristic"

        safe_title, safe_mission, safe_follow = safety.enforce(
            draft.title, draft.mission_prompt, draft.follow_up_prompt
        )
        anchor_used = draft.memory_anchor or (anchors[0] if anchors else None)

        return Quest(
            id=f"q_{int(time.time() * 1000)}_{self.rng.randrange(10_000):04d}",
            player_id=request.player_id,
            title=safe_title or chapter["title"],
            storyline_id=storyline["id"],
            storyline_title=storyline["title"],
            duration_minutes=int(request.time_minutes),
            mission_prompt=safe_mission or chapter["prompt"].format(minutes=request.time_minutes),
            sensory_focus=_clean_text(draft.sensory_focus, chapter.get("sensory_focus", "open attention")),
            safe_boundaries=_clean_text(draft.safe_boundaries, safety.safe_boundaries()),
            follow_up_prompt=safe_follow or chapter["follow_up_prompt"],
            memory_anchor=anchor_used,
            generated_by=generated_by,  # type: ignore[arg-type]
            model=used_model,
        )

    def _coerce_quest_draft(self, raw: Dict[str, Any]) -> Optional[AIQuestDraft]:
        try:
            return AIQuestDraft(
                title=_clean_text(raw.get("title"), "Untitled Checkpoint")[:120],
                mission_prompt=_clean_text(raw.get("mission_prompt")),
                sensory_focus=_clean_text(raw.get("sensory_focus"), "open attention")[:160],
                follow_up_prompt=_clean_text(raw.get("follow_up_prompt"), "What surprised you?")[:400],
                storyline_id=raw.get("storyline_id"),
                memory_anchor=_clean_text(raw.get("memory_anchor")) or None,
                safe_boundaries=_clean_text(raw.get("safe_boundaries")) or None,
            )
        except Exception:
            return None

    # -- heuristic quest generation ---------------------------------------

    QUEST_TITLE_FRAGMENTS = [
        "Field Note", "Quiet Interval", "Slow Census", "Unmapped Minute",
        "Close Reading", "Silent Inventory", "Peripheral Audit", "Still Watch",
    ]

    def _heuristic_quest(
        self,
        request: QuestRequest,
        storyline: Dict[str, Any],
        chapter: Dict[str, Any],
        anchors: List[str],
    ) -> AIQuestDraft:
        minutes = int(request.time_minutes)
        mission = chapter["prompt"].format(minutes=minutes)
        if anchors:
            anchor = anchors[0]
            mission += f" If it comes naturally, connect what you find to this earlier note of yours: \"{anchor}\"."
        if request.location_hint:
            safe_hint = safety.sanitise_hint(request.location_hint)
            if safe_hint:
                mission += f" Adapt it to where you are: {safe_hint}."
        title = self.rng.choice(self.QUEST_TITLE_FRAGMENTS) + f" — {chapter['title'].split('— ')[-1]}"
        return AIQuestDraft(
            title=title[:120],
            mission_prompt=mission,
            sensory_focus=chapter.get("sensory_focus", "open attention"),
            follow_up_prompt=chapter["follow_up_prompt"],
            storyline_id=storyline["id"],
            memory_anchor=anchors[0] if anchors else None,
            safe_boundaries=safety.safe_boundaries(),
        )

    # -- reflection evaluation --------------------------------------------

    def _eval_system_prompt(self) -> str:
        return (
            "You are the Reflection Evaluator for Reality Checkpoint. The player just came back "
            "from the physical world and described what happened. Your job is to reward real "
            "attention, never vocabulary.\n\n"
            "Score quality_score 0-100 on: sensory specificity, evidence of genuinely having "
            "been there, and a shift in understanding. Do NOT reward length or poetic phrasing "
            "on its own. A short, exact observation beats a long, vague one.\n"
            "Award xp_earned between 10 and 150 in proportion to quality.\n"
            "The feedback must be warm, specific to what they wrote, and never condescending. "
            "Two sentences maximum.\n"
            "Extract ONE durable Reality Memory worth carrying into future quests.\n\n"
            "Reply with JSON only:\n"
            '{"quality_score": 0-100, "xp_earned": 10-150, "feedback": "two warm sentences", '
            '"observation": "the single most interesting thing they noticed", '
            '"category": "one of Observation|Sound|Texture|Light|Movement|Place|Creature|Material|Weather|People|Memory|Insight", '
            '"tags": ["2-4 short lowercase tags"], "continuity_anchor": "a short phrase future quests can reference", '
            '"socratic_question": "one question that deepens their thinking", '
            '"unlocked_branch": "an optional short name for a new direction, or empty string"}'
        )

    def _eval_user_prompt(self, quest: Quest, reflection: ReflectionInput) -> str:
        return (
            f"Quest title: {quest.title}\n"
            f"Storyline: {quest.storyline_title} ({quest.storyline_id})\n"
            f"Original mission: {quest.mission_prompt}\n"
            f"Time spent: {quest.duration_minutes} minutes\n"
            f"Player's sensory-intensity self-rating: {reflection.sensory_rating}/5\n\n"
            f"Player's reflection:\n\"\"\"\n{reflection.reflection_text}\n\"\"\"\n\n"
            "Evaluate honestly. If the reflection is hollow, say so kindly and give a modest score."
        )

    async def evaluate_reflection(
        self,
        quest: Quest,
        reflection: ReflectionInput,
    ) -> EvaluationResult:
        heuristic = self._heuristic_evaluation(quest, reflection)
        draft = heuristic
        generated_by = "heuristic"
        used_model: Optional[str] = None

        if self.enabled:
            raw = await self._chat_json(
                self._eval_system_prompt(),
                self._eval_user_prompt(quest, reflection),
                temperature=0.6,
            )
            if raw is not None:
                candidate = self._coerce_evaluation_draft(raw)
                if candidate is not None:
                    draft = candidate
                    generated_by = "ollama"
                    used_model = self.model

        quality = _clamp(draft.quality_score, 0, 100, 55)
        xp = _clamp(draft.xp_earned, 10, 150, max(10, int(quality * 1.3)))
        feedback = _clean_text(draft.feedback, "You showed up, and that is the whole game.")
        question = _clean_text(draft.socratic_question, "What did your body notice before your mind did?")
        category = draft.category if draft.category in CATEGORY_VOCAB else "Observation"
        tags = [t.lower().strip()[:24] for t in (draft.tags or []) if isinstance(t, str) and t.strip()][:4]
        observation = _clean_text(draft.observation, "")

        memory: Optional[RealityMemoryItem] = None
        if observation:
            memory = RealityMemoryItem(
                id=f"mem_{int(time.time() * 1000)}_{self.rng.randrange(10_000):04d}",
                player_id=reflection.player_id,
                quest_id=quest.id,
                category=category,
                observation=observation[:600],
                tags=tags,
                continuity_anchor=_clean_text(draft.continuity_anchor) or observation[:120],
                intensity=max(1, min(5, reflection.sensory_rating)),
            )

        return EvaluationResult(
            quest_id=quest.id,
            xp_earned=xp,
            quality_score=quality,
            feedback=feedback,
            memory_extracted=memory,
            unlocked_branch=_clean_text(draft.unlocked_branch) or None,
            socratic_question=question,
            new_level=1,
            total_xp=0,
            evaluated_by=generated_by,  # type: ignore[arg-type]
            model=used_model,
        )

    def _coerce_evaluation_draft(self, raw: Dict[str, Any]) -> Optional[AIEvaluationDraft]:
        try:
            tags = raw.get("tags")
            if isinstance(tags, str):
                tags = [t.strip() for t in re.split(r"[,;]", tags) if t.strip()]
            return AIEvaluationDraft(
                xp_earned=_clamp(raw.get("xp_earned"), 10, 150, 25),
                quality_score=_clamp(raw.get("quality_score"), 0, 100, 55),
                feedback=_clean_text(raw.get("feedback"), "You showed up, and that is the whole game.")[:600],
                observation=_clean_text(raw.get("observation"))[:600],
                category=_clean_text(raw.get("category"), "Observation")[:32],
                tags=tags if isinstance(tags, list) else [],
                continuity_anchor=_clean_text(raw.get("continuity_anchor"))[:200] or None,
                socratic_question=_clean_text(raw.get("socratic_question"), "What did your body notice before your mind did?")[:300],
                unlocked_branch=_clean_text(raw.get("unlocked_branch"))[:80] or None,
            )
        except Exception:
            return None

    # -- heuristic evaluation ---------------------------------------------

    def _heuristic_evaluation(self, quest: Quest, reflection: ReflectionInput) -> AIEvaluationDraft:
        text = reflection.reflection_text or ""
        lowered = text.lower()
        words = re.findall(r"[a-zA-Z']+", lowered)
        word_count = len(words)

        # Depth: length with diminishing returns.
        if word_count >= 120:
            length_score = 42
        elif word_count >= 60:
            length_score = 34
        elif word_count >= 25:
            length_score = 24
        elif word_count >= 10:
            length_score = 14
        else:
            length_score = 6

        # Sensory specificity against the arc's own palette, plus a general sweep.
        palette = SENSORY_WORDS.get(quest.storyline_id and _theme_of(quest.storyline_id) or "visual", [])
        sensory_hits = sum(1 for w in SENSORY_WORDS["visual"] + SENSORY_WORDS["auditory"] + SENSORY_WORDS["tactile"] + SENSORY_WORDS["olfactory"] + SENSORY_WORDS["kinetic"] if w in lowered)
        palette_hits = sum(1 for w in palette if w in lowered)
        sensory_score = min(26, sensory_hits * 3 + palette_hits * 2)

        # Evidence of genuine attention: concrete specifics and connective reasoning.
        specificity = sum(1 for m in SPECIFICITY_MARKERS if m in lowered)
        numbers = len(re.findall(r"\b\d+\b", lowered))
        colours = len(re.findall(r"\b(red|orange|yellow|green|blue|violet|purple|grey|gray|brown|black|white|amber|ochre|teal|turquoise|mauve)\b", lowered))
        materials = len(re.findall(r"\b(metal|wood|stone|concrete|glass|plastic|brick|asphalt|paint|rust|fabric|leather|canvas|tile|sand|gravel|moss|lichen|clay)\b", lowered))
        specificity_score = min(18, specificity * 3 + numbers * 2 + colours * 2 + materials * 2)

        # Reflection: did attention turn into a shift?
        insight_score = min(14, sum(1 for m in INSIGHT_MARKERS if m in lowered) * 4)

        # Effort signal from the player's own intensity rating.
        rating_score = (reflection.sensory_rating - 3) * 3

        # Penalty for hollow filler.
        penalty = sum(8 for phrase in VAGUE_PHRASES if phrase in lowered)
        if word_count < 6:
            penalty += 12

        quality = length_score + sensory_score + specificity_score + insight_score + rating_score - penalty
        quality = int(max(5, min(100, quality)))
        xp = int(max(10, min(150, round(quality * 1.25))))

        if quality >= 85:
            feedback = (
                f"That is an unusually sharp record of ten minutes. The way you held on to a single "
                f"detail and let it change shape — that is exactly what {quest.storyline_title} is asking for."
            )
        elif quality >= 62:
            feedback = (
                f"Good, real attention here. You gave me the thing itself rather than a summary of it, "
                f"and that is the difference between looking and seeing."
            )
        elif quality >= 38:
            feedback = (
                "You were genuinely there — I can tell from the specifics. Next time try staying with "
                "one detail for longer and letting it surprise you before you move on."
            )
        else:
            feedback = (
                "You showed up, and that is the whole game. Keep it short next time if you like, but "
                "give me one exact thing: a sound, a colour, a texture — something only you could have noticed."
            )

        observation = self._extract_observation(text)
        tags = self._derive_tags(lowered)
        category = self._derive_category(lowered, quest)
        anchor = self._derive_anchor(observation, quest)

        return AIEvaluationDraft(
            xp_earned=xp,
            quality_score=quality,
            feedback=feedback,
            observation=observation,
            category=category,
            tags=tags,
            continuity_anchor=anchor,
            socratic_question=self._socratic(quality, quest),
            unlocked_branch=None,
        )

    def _extract_observation(self, text: str) -> str:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 18]
        if not sentences:
            return _clean_text(text)[:400]
        # Prefer the most sensory, specific sentence.
        def score(s: str) -> int:
            low = s.lower()
            return sum(2 for group in SENSORY_WORDS.values() for w in group if w in low) + len(re.findall(r"\b\d+\b", low))
        return max(sentences, key=score)[:400]

    def _derive_tags(self, lowered: str) -> List[str]:
        found: List[str] = []
        for group, words in SENSORY_WORDS.items():
            if any(w in lowered for w in words):
                found.append(group)
        for word in ("rain", "wind", "sleep", "walk", "quiet", "stranger", "animal", "plant", "water", "sky", "stone", "metal"):
            if word in lowered:
                found.append(word)
        deduped: List[str] = []
        for t in found:
            if t not in deduped:
                deduped.append(t)
        return deduped[:4]

    def _derive_category(self, lowered: str, quest: Quest) -> str:
        if any(w in lowered for w in SENSORY_WORDS["auditory"]):
            return "Sound"
        if any(w in lowered for w in SENSORY_WORDS["tactile"]):
            return "Texture"
        if any(w in lowered for w in SENSORY_WORDS["visual"]):
            return "Light"
        if any(w in lowered for w in SENSORY_WORDS["kinetic"]):
            return "Movement"
        if any(w in lowered for w in ("smell", "scent", "odour", "odor")):
            return "Weather"
        if any(w in lowered for w in ("bird", "insect", "ant", "spider", "dog", "cat", "fox")):
            return "Creature"
        if any(w in lowered for w in ("stone", "metal", "wood", "concrete", "brick", "glass")):
            return "Material"
        if any(w in lowered for w in ("remember", "memory", "used to", "childhood")):
            return "Memory"
        return "Observation"

    def _derive_anchor(self, observation: str, quest: Quest) -> str:
        if not observation:
            return f"Attention paid at {quest.storyline_title}"
        words = observation.split()
        return " ".join(words[:14]) + ("…" if len(words) > 14 else "")

    def _socratic(self, quality: int, quest: Quest) -> str:
        if quality >= 70:
            options = [
                "If you went back tomorrow at the same time, what would have to change for you to notice something new?",
                f"You found something real in {quest.storyline_title}. What does it suggest about what you usually walk past?",
                "What did you decide to stop looking at, and why did you decide that?",
            ]
        elif quality >= 40:
            options = [
                "What did your body notice before your mind did?",
                "Which detail would you have missed if you had been walking faster?",
                "What was true about that place that you had never said out loud before?",
            ]
        else:
            options = [
                "What is the one thing you would tell someone who was standing right there next to you?",
                "If you had to describe that place using only sound, what would you say?",
                "What stopped you from staying longer?",
            ]
        return self.rng.choice(options)


def _theme_of(storyline_id: str) -> str:
    sl = slib.get_storyline(storyline_id)
    return sl["theme"] if sl else "visual"


# Module-level default engine (tests build their own with Ollama disabled).
_ENGINE: Optional[AIEngine] = None


def get_engine() -> AIEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = AIEngine()
    return _ENGINE
