# AnimeEdit AI — Product Requirements Document

**Status:** Draft v0.1  
**Date:** 2026-06-19  
**Product:** AnimeEdit AI — Adobe After Effects Plugin

---

## 1. Vision

AnimeEdit AI empowers anime editors to move from frame-by-frame manual labour to intent-driven workflows. Instead of cutting, keyframing, and syncing by hand, editors describe the result they want — and the plugin translates that description into a polished timeline, complete with beat-synced cuts, camera dynamics, and effects.

---

## 2. Problem Statement

Anime music video (AMV) and fan-editing workflows in After Effects are highly repetitive and formulaic:

| Pain Point | Impact |
|---|---|
| Manually cutting footage to music beats takes hours of waveform-scrubbing | Low productivity |
| Syncing zooms, shakes, and flashes to a track is tedious trial-and-error | High iteration cost |
| Editors repeatedly use the same patterns (cut on beat, zoom in, flash white) but have no automation layer | Redundant work |
| Novel editors lack a low-barrier way to produce polished results | Steep learning curve |

AnimeEdit AI solves these by providing an AI-native assistant that understands natural-language prompts, detects scenes and beats, and automates timeline construction inside After Effects.

---

## 3. Goals & Success Metrics

| Goal | Metric |
|---|---|
| Reduce edit creation time by ≥ 60 % | Time from import to first cut |
| Reduce beat-sync effort to zero | Manual beat-marker corrections per project |
| Increase editor throughput | Cuts / minute |
| Maintain full manual override | % of generated sequences that are accepted without change |

---

## 4. Target Users

- **Primary:** AMV creators, anime fan-editors (intermediate-to-advanced After Effects users)
- **Secondary:** Social-media clip editors, VTuber highlight editors
- **Tertiary:** Beginners who want templated anime edits

---

## 5. MVP Scope (v1.0)

### 5.1 Prompt-Based Editing

- Natural-language command bar inside the AE panel
- Examples: *"cut every 4 beats with a zoom-in on the downbeat"* or *"add a camera shake on every snare"*
- LLM parses intent → converts to AE timeline actions
- User reviews and approves/rejects generated sequence before commit

### 5.2 Scene Detection

- Per-frame histogram and motion-vector analysis to detect shot boundaries
- Visual timeline overlay showing detected cuts
- Manual add/remove/merge of detected scenes

### 5.3 Beat Detection

- Audio waveform analysis inside AE (or via backend)
- Multi-tap BPM detection + transient (onset) detection
- Beat markers placed automatically on the composition timeline
- Snap cuts / effects to nearest beat with configurable offset

### 5.4 Timeline Automation

- Auto-slice footage at scene boundaries or beat intervals
- Arrange slices on a single video track
- Apply configurable transitions (cut, dip-to-black, crossfade)
- Stretch / speed-ramp clips to fit beat grid

### 5.5 Zoom / Shake / Flash Effects

- **Zoom:** keyframed scale ramps (in/out/punch) on selected clips or beats
- **Shake:** procedural position + rotation wiggle at configurable intensity
- **Flash:** solid-white layer with opacity envelope, aligned to beat
- All effects are AE-native (transform, wiggle, opacity keyframes) — no rendering dependencies

### 5.6 BYOK API Support

- Users supply their own OpenAI / Anthropic / compatible API key
- Prompt parsing runs locally via the plugin panel; LLM calls go to the user‑configured endpoint
- Optional local-only mode using a bundled small model (e.g., Llama 3.2 1B via ONNX)

---

## 6. Architecture

```
┌──────────────────────────────────────────────────┐
│              Adobe After Effects                 │
│  ┌──────────────────────────────────────────┐   │
│  │        AnimeEdit Panel (CEF/CSXS)         │   │
│  │  ┌─────────┐  ┌──────────┐  ┌─────────┐  │   │
│  │  │  Prompt  │  │ Timeline  │  │  FX     │  │   │
│  │  │  Input   │  │ Preview   │  │  Palette│  │   │
│  │  └────┬────┘  └──────────┘  └─────────┘  │   │
│  │       │                                    │   │
│  │  ┌────▼────────────────────────────────┐   │   │
│  │  │      Host JSX (ExtendScript)        │   │   │
│  │  │  - comp access, keyframes, markers  │   │   │
│  │  └────────────────┬───────────────────┘   │   │
│  └───────────────────┼───────────────────────┘   │
└──────────────────────┼──────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────┐
│           Python Backend (FastAPI)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Scene   │  │  Beat    │  │  LLM Router  │  │
│  │  Detect  │  │  Detect  │  │  (BYOK)      │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
│                   │                              │
│  ┌────────────────▼──────────────────────────┐  │
│  │       Effect Parameter Generator           │  │
│  └───────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### Key Decisions

- **Panel (CEF):** HTML5/JS panel communicates with AE via the ExtendScript host bridge (CSXS). All UI lives here.
- **Host (JSX):** Thin proxy that translates API commands into AE DOM manipulations — never blocks the UI thread for > 1 s.
- **Backend (Python):** Runs locally or on LAN. Handles compute-heavy tasks (scene/beat detection) and LLM calls. Communicates with the panel over HTTP/WS.
- **LLM calls** are fully user‑keyed; no vendor lock-in.

---

## 7. Roadmap

| Phase | Milestone | Timeline |
|---|---|---|
| **P0** | Beat detection + auto-slice timeline | v0.1 |
| **P1** | Scene detection + timeline overlay | v0.2 |
| **P2** | Zoom / shake / flash effects | v0.3 |
| **P3** | Prompt parser (LLM integration, BYOK) | v0.4 |
| **P4** | Prompt → full sequence generation | v0.5 |
| **P5** | Transition library, speed ramping, easing presets | v0.6 |
| **P6** | Beta release; user testing | v1.0-rc |
| **P7** | Local‑only model fallback, performance pass | v1.0 |

---

## 8. Non-Goals

- **No video rendering:** The plugin operates entirely within AE; rendering is left to Adobe Media Encoder or AE Render Queue.
- **No generative video (text-to-video):** AnimeEdit AI cuts, arranges, and effects existing footage — it does not create new frames.
- **No audio mixing:** Beat detection informs timeline decisions; no multi-track audio editing or stem separation.
- **No cloud infrastructure:** Compute runs locally; no AnimeEdit AI servers. BYOK is the only external dependency.
- **No collaborative editing:** Single-user, single-composition workflow.
- **No subscription model:** One-time license or free. Monetisation is out of scope for v1.
- **No mobile / web client:** After Effects desktop only.

---

## 9. Open Questions

- Should the beat-detection backend run as an AE plugin (C++) or as a sidecar Python process? (Current choice: Python sidecar for faster iteration.)
- Which LLM provider should be the default onboarding suggestion? (Candidate: OpenAI GPT-4o-mini for cost/speed.)
- Should prompt templates ship bundled or be user-contributed? (v1: 10–15 bundled templates + custom prompt support.)
