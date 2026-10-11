---
title: Reality Checkpoint — The Game That Asks You to Put Your Phone Away
published: false
tags: devchallenge, hf26challenge, ai, opensource
cover_image: https://raw.githubusercontent.com/devrelay/reality-checkpoint/main/assets/cover.png
description: An AI-powered real-world adventure game running on open-weight models that turns ordinary surroundings into quests. Screen is dormant; reality is the game.
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

---

## 1. What I Built

Most modern apps and mobile games treat human attention as oil to be extracted: endless notification loops, algorithmic feeds, visual dopamine slots, and continuous screen gaze. When games try to take people outside, they often double down on screen fixation—requiring you to stare at a GPS map, hold an AR viewfinder in front of your face, or upload surveillance photos of every tree you pass.

**Reality Checkpoint** flips that paradigm completely upside down:

> **The screen is a portal, not the destination.**

Reality Checkpoint is an AI-powered real-world adventure game that turns your everyday physical surroundings into branching narrative quests. You open the app, choose your available time budget (5, 10, 15, or 30 minutes), pick a sensory focus, and receive a bespoke, grounded mission. 

Then, **the screen goes dormant**. 

The app enters an ambient, low-power quest mode featuring a gentle breathing ring and an unobtrusive timer. No feeds, no ads, no popups. You put your phone in your pocket and step into the physical world: noticing light and shadow, mapping urban flora, isolating sonic frequencies, or examining the micro-physics of entropy on physical materials.

When you return, you describe what you genuinely experienced. An open-weight AI model on your machine evaluates the quality of your reflection, awards observational XP, adapts future missions, and indexes what you noticed into your persistent **Field Journal**.

```
[30s Setup] ──> [Bespoke Quest] ──> [Phone in Pocket / Screen Dormant] ──> [Return & Reflect] ──> [Reality Memory™ compounds]
```

---

## 2. The Core Mechanics

Reality Checkpoint is built around five distinctive mechanics:

1. **The Dormant Screen**: During quests, the screen minimizes visual noise. It acts as an ambient pocket timer that plays an organic chime (via Web Audio API) only when your time window completes.
2. **Reality Memory™ (Signature Mechanic)**: The game doesn't just record scores and generic streaks; it builds an episodic memory of what you have noticed about the physical world. If you observe lichens on a north-facing stone wall on Day 1, future quests recall that specific observation to explore moisture gradients or weathering.
3. **Five Reactive Storylines**:
   - 🌓 **The Architecture of Shadows**: Sunlight geometry, casting edges, and optical shifts.
   - 🌿 **Urban Biomecartography**: Flora colonizing pavement cracks, micro-climates, and mosses.
   - 🔊 **The Acoustic Commons**: Distant traffic hum, wind resonance, bird calls, and reverberation.
   - 🔬 **The Micro-Physics of Daily Life**: Rust, friction, surface wear, weathering, and thermal mass.
   - 🧭 **Ephemeral Encounters**: Fleeting atmospheric moments, human movement, and serendipity.
4. **Attention Over Surveillance**: We intentionally reject GPS geofencing, step-counting trackers, and forced camera uploads. The open-weight model rewards *depth of sensory attention* and *perceptual nuance*. Socratic follow-up questions verify mindfulness organically.
5. **Safety Guardrails**: Strict multi-layer safety filters guarantee missions never ask players to trespass, enter private property, touch hazardous objects, approach strangers, or look at a screen while crossing roads.

---

## 3. Demo

Below is the gameplay walkthrough of a 10-minute observation quest in "The Architecture of Shadows":

1. **Mission Generation**: The open-weight model creates *"The Long Shadow"*, asking the player to observe the contrast boundary where sunlight and iron railing meet.
2. **Dormant Mode**: The user locks their phone or lets the screen sleep while observing outdoors.
3. **Return & Reflection**: The player submits:
   > *"I observed a jagged cast shadow from an iron balcony railing. The shadow shifted across the pavement by roughly two inches over ten minutes, softening along the penumbra as high clouds passed."*
4. **AI Socratic Synthesis**: The model evaluates the perceptual quality, awards 46 XP, and logs a permanent memory node tagged `[visual, kinetic, light]`.
5. **Field Journal & Markdown Export**: The player views their living chronicle of real-world phenomena.

---

## 4. Code & Architecture

- **GitHub Repository**: [devrelay/reality-checkpoint](https://github.com/devrelay/reality-checkpoint) *(Open Source under MIT License)*
- **Architecture Overview**:

```mermaid
flowchart TD
    Client["📱 Responsive Web App & PWA<br/>(React + Tailwind + Web Audio)"]
    API["⚡ FastAPI Engine<br/>(Python 3.11+)"]
    LLM["🧠 Open-Weight LLM<br/>(Ollama / glm-4.7-flash)"]
    DB[("💾 Local SQLite DB<br/>(reality_checkpoint.db)")]
    Memory["🌿 Reality Memory™ Engine<br/>(Episodic Knowledge Graph)"]

    Client -->|1. Request Quest (Time, Focus)| API
    API -->|Fetch Past Observations| Memory
    Memory -->|Contextual Memories| DB
    API -->|Prompt + Memories| LLM
    LLM -->|Structured JSON Quest| API
    API -->|Render Mission & Dormant Mode| Client

    Client -->|2. Submit Reflection| API
    API -->|Evaluate Depth & Attention| LLM
    LLM -->|Feedback, XP, Extracted Memory| API
    API -->|Persist Observation| Memory
    API -->|Update Progress & Narrative Tree| DB
    API -->|Return Socratic Follow-up| Client
```

### Full-Stack Architecture
- **Backend**: FastAPI (Python 3.11+), Uvicorn, SQLite3 (WAL mode), Pydantic v2 schemas.
- **Frontend**: Vite, React 18, Tailwind CSS, Lucide icons, synthesized Web Audio chime synthesizer.
- **Test Suite**: 37 automated tests passing in Pytest covering safety guardrails, schema validation, and narrative progression.

---

## 5. How I Built It & Open-Source AI at the Core

Reality Checkpoint is built natively on top of **Ollama** running open-weight models (`glm-4.7-flash` or open-weight models like Gemma 2 and Llama 3.2). 

Unlike decorative chatbots, the open-weight model serves two deterministic system roles:
1. **The Dynamic Quest Generator**: Injects the player's past Reality Memories, time budget, and storyline progress into a constrained prompt, enforcing strict JSON output for safe, actionable physical directives.
2. **The Socratic Reflection Evaluator**: Analyzes free-form user reflections, evaluates qualitative mindfulness, extracts structured episodic memories, and invents a contextual Socratic follow-up question.

### Zero-Crash Heuristic Fallback
If Ollama is stopped, cold, or running on low-resource hardware, the backend automatically transitions to an intelligent deterministic heuristic engine. Players are never blocked from completing an outdoor quest due to an unavailable server.

---

## 6. Why Does Open Innovation Matter?

1. **Absolute Privacy of Personal Reflections**: Players record intimate, contemplative observations about their physical homes, walking routes, and daily habits. Sending those real-world journals to closed corporate AI APIs would violate the sacredness of personal space. Open-weight models running on local hardware ensure your thoughts never leave your machine.
2. **Offline-First Resilience**: Nature doesn't have 5G. A game designed to "Touch Grass" must work in remote woods, state parks, basements, or flight mode. Local open-weight models allow the entire experience to operate without internet connectivity.
3. **No Per-Token Financial Friction**: Gamifying daily habits shouldn't cost the user a metered API fee. Open-source models turn what would be a costly subscription service into an immortal, free utility.

---

## 7. Prize Categories

- **Primary Category**: **Hacktoberfest Open-Source AI Challenge: Week 1 ("Touch Grass")**
- **Partner Categories**:
  - *Best Use of Gemma / Open-Weight Models* (Runs open-weight models locally via Ollama with structured JSON schemas)
  - *Best Use of Entire / DevRelay* (Integrated DevRelay developer tooling and automated test harness)

---

## 8. Summary

Your next level is not inside another algorithmic feed. It's waiting on the texture of a tree bark, the angle of the afternoon sun, and the sound of the wind through autumn leaves.

Step through the portal. Lock your phone. Go touch grass.
