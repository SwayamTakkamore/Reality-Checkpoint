---
title: Reality Checkpoint — The AI Game That Asks You to Put Your Phone Away
published: true
tags: devchallenge, hf26challenge, ai, opensource
cover_image: https://raw.githubusercontent.com/SwayamTakkamore/Reality-Checkpoint/main/assets/cover.png
description: An AI-powered real-world adventure game running on Google Gemma 4 locally that turns ordinary surroundings into quests. Screen is dormant; reality is the game.
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

## What I Built

Most modern apps and games treat human attention as oil to be drilled: infinite notification loops, engagement algorithms, red notification badges, and continuous screen gaze. Even outdoor and fitness games frequently double down on screen fixation—requiring players to stare into an augmented-reality viewfinder, check a real-time GPS map at street corners, or snap mandatory surveillance photos of every waypoint.

**Reality Checkpoint** flips the paradigm completely upside down:

> **The phone is the portal, not the destination.**

Reality Checkpoint is an AI-powered, real-world adventure game that turns everyday physical surroundings into personalized quests. You spend 30 seconds choosing your available time window (5, 10, 15, or 30 minutes), select a sensory focus (optics/shadows, urban flora, soundscapes, micro-physics, or fleeting encounters), and receive a bespoke, grounded mission.

Then, **the screen goes dormant**.

The app enters an ambient, low-power dormant mode with a subtle breathing ring and a quiet countdown. There are no feeds, no popups, and no ads. You put the phone in your pocket, step outside, and experience physical reality with your own senses. When your time window is up, an organic audio chime sounds via the Web Audio API. 

When you return, you describe what you noticed. A local open-weight AI model evaluates your reflection, rewards genuine sensory attention, poses Socratic follow-up questions, and files what you discovered into a persistent, evolving **Field Journal** using **Reality Memory™**.

```
[30s Setup] ──> [Bespoke Quest] ──> [Phone in Pocket / Screen Dormant] ──> [Return & Reflect] ──> [Reality Memory™ Compounds]
```

### Who It Is For
- **Digital workers & developers** suffering from screen fatigue who need a tangible, rewarding reason to step away from their desk for 10 minutes.
- **Urban explorers & flâneurs** who want to rediscover familiar neighborhoods through fresh sensory lenses.
- **Mindfulness & curiosity seekers** who prefer playful exploration over structured meditation timers or invasive fitness trackers.

---

## Demo

- **Live Deployed App (Vercel)**: [reality-checkpoint-mauve.vercel.app](https://reality-checkpoint-mauve.vercel.app)
- **GitHub Repository**: [github.com/SwayamTakkamore/Reality-Checkpoint](https://github.com/SwayamTakkamore/Reality-Checkpoint)

### Running Locally with Google Gemma 4 (Step-by-Step)

Because true open-innovation outdoor gaming prioritizes personal privacy, zero cloud dependence, and zero metered API fees, the recommended way to experience the full AI engine with **Google Gemma 4 (`google/gemma-4-E2B-it`)** is running it locally on your computer:

```bash
# 1. Clone the repository
git clone https://github.com/SwayamTakkamore/Reality-Checkpoint.git
cd Reality-Checkpoint

# 2. Run the one-command launcher
./start.sh
```

**What the launcher handles automatically:**
1. Verifies your Python 3.11+ environment and backend requirements (`fastapi`, `transformers`, `torch`, `accelerate`).
2. Loads **Google Gemma 4 (`google/gemma-4-E2B-it`)** natively through Hugging Face Transformers.
3. **Hardware Adaptation**: Automatically checks for GPU acceleration (NVIDIA CUDA with `float16`/`bfloat16`) for rapid inference, and transparently falls back to CPU if a dedicated GPU is absent.
4. Serves the prebuilt nature-friendly UI unified with the API at **`http://localhost:8000`**.

### Local Gameplay Walkthrough:
1. **Open the Portal**: Navigate to `http://localhost:8000`. The minimal nature aesthetic greets you in warm parchment (`#fbfaf7`), botanical pine and sage accents, and editorial *Newsreader* serif typography (with an instant dark mode toggle).
2. **Select Parameters**: Choose a 10-minute budget with the theme *"The Architecture of Shadows"*.
3. **Receive Quest**: Gemma 4 generates *"The Long Shadow"*, directing you to observe how sunlight and cast iron meet at a physical railing.
4. **Dormant Mode**: The screen dims into a minimalist breathing timer with ambient Web Audio chime indicators. Put the phone in your pocket and step outside.
5. **Return & Socratic Reflection**: You return and input your observation:
   > *"I observed a jagged cast shadow from an iron balcony railing. The sunlight shifted by roughly two inches over ten minutes, softening along the penumbra as high clouds passed."*
6. **Evaluation & Reality Memory™**: Gemma 4 evaluates observational depth on-device, awards XP, and records an episodic memory node (`Category: Light, Tags: [visual, kinetic]`) into your persistent local Field Journal.

---

## Code

The entire codebase is open source under the MIT License:

{% github SwayamTakkamore/Reality-Checkpoint %}


### Project Architecture

```mermaid
flowchart TD
    Client["📱 Responsive PWA / Web UI<br/>(React 18 + Tailwind + Web Audio)"]
    API["⚡ FastAPI Backend Engine<br/>(Python 3.11+)"]
    LLM["🧠 Local Open-Weight LLM<br/>(Hugging Face Transformers: Google Gemma 4)"]
    GPU["🎮 GPU Acceleration (CUDA)<br/>Auto-Fallback to CPU"]
    DB[("💾 Local SQLite3 Database<br/>(WAL Mode: reality_checkpoint.db)")]
    Memory["🌿 Reality Memory™ Engine<br/>(Episodic Knowledge Graph)"]

    Client -->|1. Request Quest (Time, Focus)| API
    API -->|Fetch Past Memories| Memory
    Memory -->|Contextual Memories| DB
    API -->|Prompt + Memories| LLM
    LLM --> GPU
    LLM -->|Structured JSON Quest| API
    API -->|Render Mission & Dormant Mode| Client

    Client -->|2. Submit Reflection| API
    API -->|Evaluate Depth & Attention| LLM
    LLM -->|Feedback, XP, Extracted Memory| API
    API -->|Persist Observation| Memory
    API -->|Update Progress & Narrative Tree| DB
    API -->|Return Socratic Follow-up| Client
```

- **Frontend (`frontend/`)**: React 18, Tailwind CSS, Lucide icons, synthesized Web Audio chime, and Screen WakeLock API. Features a minimalist nature-friendly light mode default with smooth dark mode.
- **Backend (`backend/`)**: FastAPI, Pydantic v2 schemas, SQLite3 persistence, and multi-layer safety guardrails.
- **Test Suite (`backend/test_backend.py`)**: 37 automated tests passing in Pytest verifying schema resilience, safety enforcement, and progression mechanics.

---

## How I Built It

Reality Checkpoint is built natively around **Google's Gemma 4 (`google/gemma-4-E2B-it`)** running locally on-device through **Hugging Face Transformers** and PyTorch.

Instead of treating AI as an open-ended chatbot, the engine uses Gemma 4 for structured, deterministic game mechanics:

1. **Hardware-Adaptive Inference (GPU-First with Seamless CPU Fallback)**:
   The backend inspects available compute at startup. When CUDA is available, it leverages GPU acceleration (`device_map="auto"`, `bfloat16`/`float16`). If running on machines without a dedicated GPU, or if GPU VRAM is constrained, the runtime automatically and transparently falls back to CPU execution with zero downtime or crashed requests.

2. **Dynamic Quest Generation with Schema Enforcement**:
   Injects the player's past Reality Memories, time constraints, and narrative arc into a structured prompt, enforcing strict Pydantic JSON schemas.

3. **Qualitative Reflection Evaluation & Socratic Probing**:
   Reads free-form text reflections, evaluates observational specificity, scores attention depth, extracts structured memory nodes, and poses an organic follow-up question.

4. **Deterministic Heuristic Floor**:
   If the model is cold or offline, the backend automatically falls back to an intelligent rule-based engine. The player is never stranded outside because an AI process stalled.

5. **Multi-Tier Safety Guardrails (`backend/safety.py`)**:
   Hardcoded regex and semantic filters enforce that generated quests never advise trespassing, private property access, hazardous terrain, touching unknown plants or animals, approaching strangers, or using phones near active traffic.

---

## Why Does Open Innovation Matter?

1. **Absolute Privacy for Contemplative Reflections**:
   Personal observations about your neighborhood, daily walks, and quiet thoughts should never be ingested into proprietary training datasets or corporate cloud logs. Running Google Gemma 4 locally ensures your private reflections never leave your machine.

2. **True Offline Resilience (Nature Doesn't Have 5G)**:
   The entire point of "Touch Grass" is going outside. A hiking trail, state park, basement workshop, or remote shoreline often has zero cellular signal. Because the model, runtime, and SQLite database run locally on-device, Reality Checkpoint works completely offline.

3. **Zero Financial Metering**:
   Habit-forming outdoor exploration shouldn't incur metered API bills or monthly paywalls. Open-weight models like Gemma 4 make contemplative technology accessible to anyone with standard personal hardware.

---

## My Agent Session

The complete architecture, PRD, and test harness were orchestrated and validated using T3 Code and DevRelay agent workflows:

{% agent_session 857d8d69-1694-4ea0-8751-e215c9e90382 %}

---

## Prize Categories

- **Primary Track**: **Hacktoberfest Open-Source AI Challenge: Week 1 ("Touch Grass")**
- **Partner Categories**:
  - **Best Use of Gemma**: Integrates Google's **Gemma 4 (`google/gemma-4-E2B-it`)** locally via Hugging Face Transformers. Utilizes GPU-first execution with seamless CPU fallback, strict JSON schema parsing, and on-device private inference to generate real-world sensory quests and evaluate outdoor reflections.
  - **Best Use of Entire / DevRelay**: Full agent orchestration, automated session documentation, and test-driven verification.
