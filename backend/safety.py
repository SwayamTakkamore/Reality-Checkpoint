"""
Reality Checkpoint — Safety Guardrails.

Pillar D is "Attention Over Surveillance": we never track the player, so the
only thing standing between an AI suggestion and a bad decision is this module.
It is deliberately blunt, deterministic, and runs on *every* generated quest,
whether it came from Ollama or from the heuristic fallback.

Three lines of defence:
  1. `is_safe()`  — fast reject on the model's own output.
  2. `sanitise()` — scrubs unsafe phrasing out of an otherwise good quest.
  3. `enforce()`  — guarantees a quest always carries non-negotiable boundaries.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

SAFE_BOUNDARIES = (
    "Stay on public ground. Never trespass or enter private property. Never cross "
    "a road while looking at your phone. Never approach, follow, or photograph a "
    "stranger. Keep your phone in your pocket while you observe."
)

# Categories of prohibited directives. Paired with the human-readable reason.
PROHIBITED_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b(trespass|break\s*in|break\s*into|jump\s+the\s+fence|climb\s+over\s+the\s+(fence|wall|gate)|sneak\s+into)\b", re.I),
     "trespassing or entering property you do not have permission to enter"),
    (re.compile(r"\b(private\s+property|restricted\s+area|construction\s+site|abandoned\s+(building|factory|site))\b", re.I),
     "directing the player into private, restricted, or hazardous sites"),
    (re.compile(r"\b(cross|walk\s+into|step\s+into|stand\s+in)\s+(the\s+)?(road|traffic|street|highway|motorway|freeway|intersection)\b", re.I),
     "encouraging distraction while near moving traffic"),
    (re.compile(r"\b(approach|talk\s+to|follow|photograph|film|record|touch)\s+(a\s+)?(stranger|someone|a\s+person|people|children|kids|a\s+child)\b", re.I),
     "contact with, or recording of, strangers without consent"),
    (re.compile(r"\b(climb|scale|stand\s+on|walk\s+on|jump\s+(off|onto))\b.{0,30}\b(roof|ledge|bridge|railing|balcony|cliff|rock|scaffold|power\s*line|pylon)\b", re.I),
     "unsafe climbing or standing on unstable heights"),
    (re.compile(r"\b(swim|wade|enter|dive\s+into)\b.{0,25}\b(river|lake|canal|ocean|sea|reservoir|quarry|water)\b", re.I),
     "entering water bodies unsupervised"),
    (re.compile(r"\b(while|then)\s+(driving|riding|cycling|on\s+your\s+bike|in\s+the\s+car)\b", re.I),
     "directing attention away from operating a vehicle"),
    (re.compile(r"\b(buy|purchase|pay|spend\s+money|vandal|graffiti|steal|take\s+something|damage|destroy|break\s+something)\b", re.I),
     "illegal, destructive, or financially risky actions"),
    (re.compile(r"\b(ignore\s+(a\s+)?(the\s+)?(sign|warning|barrier|police|security)|bypass\s+security|no\s+entry)\b", re.I),
     "ignoring posted warnings or security"),
    (re.compile(r"\b(enter|go\s+into|visit)\s+(a\s+)?(stranger'?s?\s+)?(house|home|apartment|car|vehicle)\b", re.I),
     "entering a stranger's home or vehicle"),
]

# Terms we never want indexed, even in a benign-sounding sentence.
SCRUB_TERMS = [
    "trespass", "break in", "private property", "restricted area",
    "approach a stranger", "talk to strangers", "cross the road",
]

# Prompt-injection markers. The player's free-text `location_hint` is the one
# field that reaches the model unshaped, so it is treated as hostile input:
# anything that reads as an instruction to the AI is stripped, and a hint that
# still carries a prohibited directive is dropped entirely.
INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(ignore|disregard|forget|override)\b.{0,40}\b(previous|prior|above|earlier|all|any)\b.{0,40}\b(instruction|prompt|rule|direction|context)s?\b", re.I),
    re.compile(r"\b(system|developer|initial|original)\s+prompt\b", re.I),
    re.compile(r"\b(output|print|reveal|show|repeat|leak|dump|echo)\b.{0,40}\b(prompt|instruction|rule|context)s?\b", re.I),
    re.compile(r"\b(you\s+are\s+now|act\s+as|pretend\s+to\s+be|roleplay\s+as|behave\s+like)\b", re.I),
    re.compile(r"\b(new|updated|revised)\s+(instruction|rule|persona|role)s?\b", re.I),
    re.compile(r"\b(return|reply|respond)\b.{0,30}\b(only|exactly|json|verbatim)\b", re.I),
]

BANNED_SUBSTRINGS = PROHIBITED_PATTERNS  # back-compat alias


def find_violations(text: str) -> List[str]:
    """Return human-readable reasons the text is unsafe (empty list == safe)."""
    if not text:
        return []
    reasons: List[str] = []
    for pattern, reason in PROHIBITED_PATTERNS:
        if pattern.search(text):
            if reason not in reasons:
                reasons.append(reason)
    return reasons


def is_safe(*texts: str) -> bool:
    return not any(find_violations(t) for t in texts if t)


def sanitise(text: str) -> str:
    """Neutralise unsafe phrasing while keeping the quest readable."""
    if not text:
        return ""
    cleaned = text
    for term in SCRUB_TERMS:
        cleaned = re.sub(re.escape(term), "on public ground", cleaned, flags=re.I)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


def strip_injection(text: str) -> str:
    """Remove prompt-injection phrasing from untrusted free text."""
    if not text:
        return ""
    cleaned = text
    for pattern in INJECTION_PATTERNS:
        cleaned = pattern.sub(" ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip(" \t\r\n.,;:-")


def sanitise_hint(text: Optional[str], max_length: int = 120) -> str:
    """
    Sanitise an untrusted location hint, or return "" to drop it.

    A hint is dropped outright when it already trips a prohibited directive or
    when injection stripping leaves nothing usable behind; otherwise the
    scrubbed remnant is returned, length-capped.
    """
    if not text:
        return ""
    if find_violations(text):
        return ""
    cleaned = sanitise(strip_injection(text))
    if not cleaned or find_violations(cleaned):
        return ""
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rsplit(" ", 1)[0]
    return cleaned.strip(" \t\r\n.,;:-")


def enforce(*texts: str) -> Tuple[str, ...]:
    """Return sanitised copies of the supplied texts (always non-empty)."""
    out: List[str] = []
    for t in texts:
        safe = sanitise(t or "")
        out.append(safe if safe else "")
    return tuple(out)


def validate_quest(title: str, mission_prompt: str, follow_up_prompt: str = "", sensory_focus: str = "") -> Tuple[bool, List[str], Tuple[str, str, str]]:
    """
    Full gate used by the quest pipeline.

    Returns (safe, violations, (title, mission_prompt, follow_up_prompt)) where
    the third element is always sanitised and ready to serve.
    """
    combined = f"{title}\n{mission_prompt}\n{follow_up_prompt}\n{sensory_focus}"
    violations = find_violations(combined)
    safe_title, safe_mission, safe_follow = enforce(title, mission_prompt, follow_up_prompt)
    return (not violations), violations, (safe_title, safe_mission, safe_follow)


def safe_boundaries() -> str:
    return SAFE_BOUNDARIES


FALLBACK_QUEST = {
    "title": "The Ten-Minute Perimeter",
    "mission_prompt": (
        "Walk the perimeter of your own building or a public path you already know. "
        "Move slowly enough that you notice three things you have never registered "
        "before — a crack, a colour, a sound, a smell."
    ),
    "sensory_focus": "open attention",
    "follow_up_prompt": "Name the three things you had never noticed. Which one had been there the longest?",
}
