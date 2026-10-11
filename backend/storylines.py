"""
Reality Checkpoint — Seed storylines with branching quest logic.

Five narrative arcs, each with chapters that unlock as the player completes
checkpoints inside the arc. The AI personalises the *surface* of a quest, but
the narrative skeleton lives here so the game still has shape when the local
model is offline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from models import Storyline, StorylineNode

SEED_STORYLINES: List[Dict[str, Any]] = [
    {
        "id": "architecture-of-shadows",
        "title": "The Architecture of Shadows",
        "theme": "visual",
        "description": (
            "Every surface is a clock. You are learning to read buildings, sun angles "
            "and the geometry of light as a living instrument."
        ),
        "motif": "Light is a structure you can stand inside.",
        "chapters": [
            {
                "id": "shadow-1",
                "title": "Chapter I — The Long Shadow",
                "description": "Establish a baseline: where light falls right now.",
                "prompt": (
                    "Find a place where light meets shadow on a wall, a step, or a fence. "
                    "Stand so you can see the edge of that meeting. Watch it for {minutes} "
                    "minutes without moving. Trace the boundary with your eyes only."
                ),
                "sensory_focus": "visual · light and geometry",
                "follow_up_prompt": (
                    "Describe the edge you watched. Was it soft or sharp? Did it move, "
                    "and in which direction? What was on the dark side that you could "
                    "not see from where you started?"
                ),
                "unlocks": ["shadow-2", "micro-physics"],
            },
            {
                "id": "shadow-2",
                "title": "Chapter II — Reflected Counting",
                "description": "Notice that light arrives more than once.",
                "prompt": (
                    "Spend {minutes} minutes finding every way light reaches you from a "
                    "second bounce — a window, a car roof, a wet stone, a painted sill. "
                    "Count the reflections. Note the colour each one carries."
                ),
                "sensory_focus": "visual · reflection and colour temperature",
                "follow_up_prompt": (
                    "How many reflections did you find, and which carried the strangest "
                    "colour? What material was it bouncing from?"
                ),
                "unlocks": ["shadow-3"],
            },
            {
                "id": "shadow-3",
                "title": "Chapter III — The Invisible Hour",
                "description": "Design a shadow of your own.",
                "prompt": (
                    "For {minutes} minutes, use only your body and objects already within "
                    "arm's reach on public ground to cast a shadow you find interesting. "
                    "Choose where it lands deliberately. Then draw it into your reflection."
                ),
                "sensory_focus": "visual · casting and composition",
                "follow_up_prompt": (
                    "What shadow did you make and why did you choose that surface? "
                    "What did you learn by becoming the thing that blocks light?"
                ),
                "unlocks": [],
            },
        ],
    },
    {
        "id": "urban-biomecartography",
        "title": "Urban Biomecartography",
        "theme": "open",
        "description": (
            "You are mapping the wildness that survives inside what humans built. "
            "Weeds, moss, lichen and insects are the true cartographers here."
        ),
        "motif": "Nothing was ever only pavement.",
        "chapters": [
            {
                "id": "biome-1",
                "title": "Chapter I — The Seam Survey",
                "description": "Life lives in the cracks between things.",
                "prompt": (
                    "Walk for {minutes} minutes looking only at seams: the line where a "
                    "kerb meets a wall, where tiles meet soil, where metal meets stone. "
                    "Find the most unlikely piece of living green in those seams."
                ),
                "sensory_focus": "open · edges and microhabitats",
                "follow_up_prompt": (
                    "Where did you find life in the seams? What made that spot survivable? "
                    "Estimate how long it took to get there."
                ),
                "unlocks": ["biome-2", "ephemeral-encounters"],
            },
            {
                "id": "biome-2",
                "title": "Chapter II — The Wind Map",
                "description": "Track a force you cannot see by what it moves.",
                "prompt": (
                    "Choose one plant on public ground. For {minutes} minutes, watch only "
                    "that plant. Map the wind by its movement — direction, bursts, pauses. "
                    "Where is that air coming from?"
                ),
                "sensory_focus": "kinetic · wind and respiration",
                "follow_up_prompt": (
                    "Describe the wind's rhythm. Was it steady or pulsing? What in the "
                    "surroundings are you now certain is causing it?"
                ),
                "unlocks": ["biome-3"],
            },
            {
                "id": "biome-3",
                "title": "Chapter III — The Uninvited Grid",
                "description": "Draw a map of a place humans did not plan.",
                "prompt": (
                    "Spend {minutes} minutes mentally mapping a patch of unplanned growth "
                    "about ten paces wide. Where are its densest points? Where does it "
                    "stop, and what stops it? Describe the borders in your reflection."
                ),
                "sensory_focus": "open · territory and borders",
                "follow_up_prompt": (
                    "What held the growth back? How did the border of the patch compare "
                    "with the borders humans built around it?"
                ),
                "unlocks": [],
            },
        ],
    },
    {
        "id": "acoustic-commons",
        "title": "The Acoustic Commons",
        "theme": "auditory",
        "description": (
            "Sound is shared infrastructure. You have been listening to a city that "
            "never stops modulating, and you are about to notice its architecture."
        ),
        "motif": "The commons you cannot fence is made of air.",
        "chapters": [
            {
                "id": "acoustic-1",
                "title": "Chapter I — The Sixty Second Silence",
                "description": "Establish what quiet actually sounds like where you are.",
                "prompt": (
                    "Stand still on public ground for {minutes} minutes. Do not speak. "
                    "List every distinct sound in the order you notice it, from loudest "
                    "to most faint. Do not judge any of them."
                ),
                "sensory_focus": "auditory · layering and distance",
                "follow_up_prompt": (
                    "What was the quietest sound you could hear, and what made it hard "
                    "to find? Which sound had been there the whole time?"
                ),
                "unlocks": ["acoustic-2"],
            },
            {
                "id": "acoustic-2",
                "title": "Chapter II — Room Tone of a Stranger",
                "description": "Listen to how a space shapes a sound.",
                "prompt": (
                    "Find two outdoor places on public ground that sound different — an "
                    "open stretch and an enclosed one. For {minutes} minutes, alternate. "
                    "Clap once, or hum a single note, in each. Notice what the space does "
                    "with your sound."
                ),
                "sensory_focus": "auditory · resonance and enclosure",
                "follow_up_prompt": (
                    "How did each place change your sound? What does that tell you about "
                    "the shape of the space — even if you could not see it?"
                ),
                "unlocks": ["acoustic-3"],
            },
            {
                "id": "acoustic-3",
                "title": "Chapter III — The Borrowed Rhythm",
                "description": "Find the pulse of the place.",
                "prompt": (
                    "For {minutes} minutes you are a metronome, not a listener. Find a "
                    "repeating sound — a drip, a footstep pattern, a machine, a distant "
                    "beat — and tap it out gently on your leg. Let it set your pace."
                ),
                "sensory_focus": "auditory · rhythm and entrainment",
                "follow_up_prompt": (
                    "What rhythm did you borrow, and how did tapping it change how you "
                    "felt about the place?"
                ),
                "unlocks": [],
            },
        ],
    },
    {
        "id": "micro-physics",
        "title": "The Micro-Physics of Daily Life",
        "theme": "tactile",
        "description": (
            "Entropy, friction, corrosion and wear are physics you can touch. You are "
            "reading the material history of the ordinary."
        ),
        "motif": "Wear is evidence. Evidence is a story.",
        "chapters": [
            {
                "id": "micro-1",
                "title": "Chapter I — The Witness Marks",
                "description": "Find the places where the world has been touched.",
                "prompt": (
                    "For {minutes} minutes, look for wear: a hand-worn rail, a polished "
                    "step, scuffed paint, a dented bollard. Find three. Decide what act "
                    "of repetition caused each one."
                ),
                "sensory_focus": "tactile · erosion and repetition",
                "follow_up_prompt": (
                    "Describe your three witness marks. Which act of repetition surprised "
                    "you most, and how many people must it have taken?"
                ),
                "unlocks": ["micro-2", "architecture-of-shadows"],
            },
            {
                "id": "micro-2",
                "title": "Chapter II — The Thermodynamic Cup",
                "description": "Follow heat out of a thing.",
                "prompt": (
                    "Take a warm drink outside. For {minutes} minutes, hold it and watch it "
                    "cool. Notice where the heat goes — your hands, the air, the ground. "
                    "Describe the cooling as a journey, not a loss."
                ),
                "sensory_focus": "tactile · thermal transfer",
                "follow_up_prompt": (
                    "Where did the heat go? What did the cup feel like at the moment it "
                    "stopped feeling warm?"
                ),
                "unlocks": ["micro-3"],
            },
            {
                "id": "micro-3",
                "title": "Chapter III — The Weight of Small Things",
                "description": "Calibrate your hands.",
                "prompt": (
                    "For {minutes} minutes, pick up small public objects one at a time — a "
                    "leaf, a pebble, a twig, a bottle cap with your own waste, not others'. "
                    "Guess each weight in your hand before you lift it. Log your errors."
                ),
                "sensory_focus": "tactile · proprioception and estimation",
                "follow_up_prompt": (
                    "Which guess was furthest off, and what fooled your hand — size, shape, "
                    "or expectation?"
                ),
                "unlocks": [],
            },
        ],
    },
    {
        "id": "ephemeral-encounters",
        "title": "Curiosity & Ephemeral Encounters",
        "theme": "open",
        "description": (
            "The world is mostly event, not object. This arc is about catching things "
            "that will never happen in precisely that way again."
        ),
        "motif": "You are not looking for objects. You are looking for timings.",
        "chapters": [
            {
                "id": "ephemeral-1",
                "title": "Chapter I — The Almost-Gone",
                "description": "Catch something mid-transition.",
                "prompt": (
                    "For {minutes} minutes, look only for things caught in the middle: steam "
                    "dissolving, a puddle drying, a leaf mid-fall, condensation forming. "
                    "Find one and stay with it until it finishes."
                ),
                "sensory_focus": "open · process and timing",
                "follow_up_prompt": (
                    "What were you watching when it ended? Describe the exact moment it was "
                    "no longer the thing it had been."
                ),
                "unlocks": ["ephemeral-2"],
            },
            {
                "id": "ephemeral-2",
                "title": "Chapter II — The Smallest Event",
                "description": "Detect something almost too small to matter.",
                "prompt": (
                    "For {minutes} minutes, hunt for the smallest event in your field of "
                    "view — an ant rerouting, a spider shifting, a droplet falling from a "
                    "sign. You are not allowed to find anything big."
                ),
                "sensory_focus": "open · scale and patience",
                "follow_up_prompt": (
                    "What was the smallest event you found? What had to be true about your "
                    "attention for you to notice it at all?"
                ),
                "unlocks": ["ephemeral-3"],
            },
            {
                "id": "ephemeral-3",
                "title": "Chapter III — The Unrepeatable Minute",
                "description": "Record a minute that cannot recur.",
                "prompt": (
                    "Stop where you are on public ground. For {minutes} minutes, build a "
                    "complete inventory of everything currently happening around you. "
                    "Then write, in one sentence, why this exact minute can never return."
                ),
                "sensory_focus": "open · presence and irreversibility",
                "follow_up_prompt": (
                    "Write the sentence. What in the inventory would you most want to "
                    "describe to someone who was not there?"
                ),
                "unlocks": [],
            },
        ],
    },
]

STORYLINE_INDEX: Dict[str, Dict[str, Any]] = {s["id"]: s for s in SEED_STORYLINES}

# Chapter graph: chapter_id -> chapter dict
CHAPTER_INDEX: Dict[str, Dict[str, Any]] = {
    ch["id"]: {**ch, "storyline_id": sl["id"], "storyline_title": sl["title"]}
    for sl in SEED_STORYLINES
    for ch in sl["chapters"]
}

# Opening chapters of every arc are always available.
OPENING_CHAPTERS = [sl["chapters"][0]["id"] for sl in SEED_STORYLINES]

THEME_TO_STORYLINE = {
    "visual": "architecture-of-shadows",
    "auditory": "acoustic-commons",
    "tactile": "micro-physics",
    "kinetic": "urban-biomecartography",
    "olfactory": "ephemeral-encounters",
}


def get_storyline(storyline_id: str) -> Optional[Dict[str, Any]]:
    return STORYLINE_INDEX.get(storyline_id)


def get_chapter(chapter_id: str) -> Optional[Dict[str, Any]]:
    return CHAPTER_INDEX.get(chapter_id)


def chapter_ids_for(storyline_id: str) -> List[str]:
    sl = STORYLINE_INDEX.get(storyline_id)
    return [c["id"] for c in sl["chapters"]] if sl else []


def next_chapter(storyline_id: str, completed_count: int) -> str:
    """Linear progression inside an arc, clamped to the final chapter."""
    ids = chapter_ids_for(storyline_id)
    if not ids:
        return OPENING_CHAPTERS[0]
    idx = max(0, min(len(ids) - 1, completed_count))
    return ids[idx]


def unlocks_for(chapter_id: str) -> List[str]:
    ch = CHAPTER_INDEX.get(chapter_id)
    return list(ch.get("unlocks", [])) if ch else []


def pick_storyline(
    theme: str = "open",
    requested: Optional[str] = None,
    progress: Optional[Dict[str, Dict[str, Any]]] = None,
    seed: int = 0,
) -> Dict[str, Any]:
    """
    Choose an arc. Explicit request wins; then theme mapping; then the least
    visited arc, so the journal stays broad rather than tunnelling one motif.
    """
    if requested and requested in STORYLINE_INDEX:
        return STORYLINE_INDEX[requested]
    mapped = THEME_TO_STORYLINE.get((theme or "").strip().lower())
    if mapped:
        return STORYLINE_INDEX[mapped]
    progress = progress or {}
    ordered = sorted(
        SEED_STORYLINES,
        key=lambda s: (progress.get(s["id"], {}).get("quests_completed", 0), SEED_STORYLINES.index(s)),
    )
    return ordered[0]


def build_storyline_models(progress: Dict[str, Dict[str, Any]]) -> List[Storyline]:
    """Materialise API-facing storyline objects including branch/node states."""
    result: List[Storyline] = []
    for sl in SEED_STORYLINES:
        stats = progress.get(sl["id"], {})
        completed = int(stats.get("quests_completed", 0))
        total = len(sl["chapters"])
        nodes: List[StorylineNode] = []
        for i, ch in enumerate(sl["chapters"]):
            if i < completed:
                state = "completed"
            elif i == completed:
                state = "available"
            else:
                state = "locked"
            nodes.append(
                StorylineNode(
                    id=ch["id"],
                    title=ch["title"],
                    chapter=i + 1,
                    state=state,
                    description=ch["description"],
                )
            )
        unlocked = completed > 0 or sl["chapters"][0]["id"] in OPENING_CHAPTERS
        result.append(
            Storyline(
                id=sl["id"],
                title=sl["title"],
                theme=sl["theme"],
                description=sl["description"],
                motif=sl["motif"],
                unlocked=unlocked,
                progress=round(min(1.0, completed / total), 3) if total else 0.0,
                quests_completed=completed,
                branches=nodes,
            )
        )
    return result
