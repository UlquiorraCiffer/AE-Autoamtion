# AnimeEdit AI — MVP QA Checklist

> Target: Windows 10/11 · After Effects 2023+ · Python 3.11+
> Estimated time: 30–45 minutes

---

## Instructions

1. Go through each section **in order**.
2. Check every box that applies.
3. If a step fails, note the error and stop — do not proceed.
4. At the end, tally the result as **PASS** (all boxes checked) or **FAIL** (any box unchecked).

---

## 1. Environment Setup

### 1.1 System Requirements

- [ ] **Windows version**: Windows 10 22H2 or Windows 11
- [ ] **RAM**: 8 GB minimum (16 GB recommended)
- [ ] **Disk space**: 5 GB free (for Python + dependencies + media files)
- [ ] **Screen resolution**: 1280×720 minimum

### 1.2 Python Installation

- [ ] Open a **Command Prompt** (`cmd.exe`) and run:

      python --version

  Expected: `Python 3.11.x` or `3.12.x`

- [ ] If Python is missing, download from https://www.python.org/downloads/
      **Important**: check "Add Python to PATH" during installation.

### 1.3 Git (optional, for updates)

- [ ] Run:

      git --version

  Expected: `git version 2.x`

- [ ] If missing, download from https://git-scm.com/download/win

### 1.4 FFmpeg (recommended for faster video processing)

- [ ] Download FFmpeg from https://ffmpeg.org/download.html (Windows builds)
- [ ] Extract the archive to `C:\ffmpeg`
- [ ] Add `C:\ffmpeg\bin` to your system PATH:
      1. Right-click **This PC** → **Properties** → **Advanced system settings**
      2. Click **Environment Variables**
      3. Under **System variables**, find **Path**, click **Edit**
      4. Click **New**, enter `C:\ffmpeg\bin`, click **OK** all the way
- [ ] Verify: open a **new** Command Prompt and run:

      ffmpeg -version

  Expected: prints FFmpeg version information (not "not recognized")

---

## 2. Project Setup

### 2.1 Clone or Extract the Project

- [ ] Open Command Prompt and navigate to where you want the project:

      cd C:\Users\%USERNAME%\Projects

- [ ] Clone the repository:

      git clone <repository-url> AnimeEdit-AI
      cd AnimeEdit-AI

  Or if you have a ZIP file, extract it and `cd` into the folder.

### 2.2 Install Python Dependencies

- [ ] From the project root, run:

      cd backend
      pip install -r requirements.txt

  Expected output: downloads and installs packages. Final line says "Successfully installed ..."

- [ ] Verify critical packages:

      python -c "import fastapi; import uvicorn; import librosa; import cv2; print('OK')"

  Expected output: `OK`

### 2.3 Verify the Start Script

- [ ] From the project root `AnimeEdit-AI`, run:

      run.bat

  Expected: The script runs tests, then starts the backend server.
  Look for lines like:
  - `Running tests...` → `OK (51 passed)`
  - `Server started at http://127.0.0.1:8000`

- [ ] Press `Ctrl+C` to stop the server (after verifying it starts).

---

## 3. Backend Smoke Tests

### 3.1 Start the Backend

- [ ] Open a **Command Prompt** in the project root.
- [ ] Run:

      cd backend
      uvicorn app.main:app --reload

  Expected: Server starts on `http://127.0.0.1:8000`. No errors in console.

- [ ] Keep this terminal window open (the server must run for all subsequent tests).

### 3.2 Health Check

- [ ] Open a **second** Command Prompt window and run:

      curl http://127.0.0.1:8000/health

  > If `curl` is not installed, open `http://127.0.0.1:8000/health` in a web browser instead.

  Expected output:
  ```json
  {"status":"ok","version":"0.1.0"}
  ```

  **PASS** ☐ / **FAIL** ☐

### 3.3 Analyze Endpoint (no API key)

- [ ] Run:

      curl -X POST http://127.0.0.1:8000/analyze ^
        -H "Content-Type: application/json" ^
        -d "{\"prompt\":\"cut every 4 beats with zoom-in on downbeats\"}"

  Expected output (local parser fallback, order may vary):
  ```json
  {
    "prompt": "cut every 4 beats with zoom-in on downbeats",
    "actions": [
      {"type":"beat_detect","label":"Detect beats","params":{}},
      {"type":"scene_detect","label":"Detect scene cuts","params":{}},
      {"type":"zoom","label":"Add zoom effect","params":{}}
    ]
  }
  ```

  **PASS** ☐ / **FAIL** ☐

### 3.4 Generate Plan Endpoint

- [ ] Run:

      curl -X POST http://127.0.0.1:8000/generate-plan ^
        -H "Content-Type: application/json" ^
        -d "{\"prompt\":\"add zoom on high motion\",\"segments\":[{\"start_time\":0,\"end_time\":5,\"motion_score\":45,\"confidence\":1},{\"start_time\":5,\"end_time\":10,\"motion_score\":5,\"confidence\":1}]}"

  Expected output: a JSON response containing `plan` with `timeline` and `effects`.
  - `timeline` should have 2 entries
  - `effects` should contain at least one zoom effect

  **PASS** ☐ / **FAIL** ☐

### 3.5 Apply Edit Endpoint

- [ ] Run:

      curl -X POST http://127.0.0.1:8000/apply-edit ^
        -H "Content-Type: application/json" ^
        -d "{\"actions\":[{\"type\":\"zoom\",\"label\":\"Test zoom\",\"params\":{\"magnitude\":1.3}}]}"

  Expected output:
  ```json
  {
    "applied": ["ae.applyZoom(1, '{\"magnitude\":1.3}')"],
    "status": "ok"
  }
  ```

  **PASS** ☐ / **FAIL** ☐

---

## 4. AE Plugin Installation

### 4.1 Locate the AE Extension Folder

- [ ] Close After Effects if it is running.
- [ ] Open Windows Explorer and navigate to:

      C:\Program Files\Adobe\Adobe After Effects <version>\Support Files

  Or the equivalent location for your AE version.

- [ ] Open the `CEP` folder (if it does not exist, create it).
- [ ] Open the `extensions` folder (if it does not exist, create it).

  The full path should look like:

      C:\Program Files\Adobe\Adobe After Effects 2020\Support Files\CEP\extensions\

### 4.2 Copy the Plugin

- [ ] Copy the entire `plugin` folder from the project to the `extensions` folder.
- [ ] Rename it to `com.animeedit.ai.panel` (so the final path is):

      ...\CEP\extensions\com.animeedit.ai.panel\CSXS\manifest.xml

  Verify the manifest file exists at this location.

### 4.3 Enable CEP Debugging (required for unsigned extensions)

- [ ] Open **regedit** (Windows Registry Editor) as Administrator.
- [ ] Navigate to:

      HKEY_CURRENT_USER\Software\Adobe\CSXS.8

  > If `CSXS.8` does not exist, create it under `Software\Adobe`.

- [ ] Create a new **String Value** (REG_SZ):
  - Name: `PlayerDebugMode`
  - Value: `1`

- [ ] Close regedit.

### 4.4 Load the Panel in AE

- [ ] Launch **Adobe After Effects**.
- [ ] Go to the menu: **Window** → **Extensions** → **AnimeEdit AI**
  > If you don't see it, restart AE and check again.
- [ ] Expected: a dark-themed panel appears:
  - Title bar says "AnimeEdit AI"
  - A colored dot in the header (red = offline, green = connected)
  - A text area with placeholder text
  - Buttons: **Analyze**, **Apply**, **Test Connection**, and a gear icon

  **PASS** ☐ / **FAIL** ☐

---

## 5. Panel Connection Tests

### 5.1 Backend Connection

- [ ] Make sure the backend server is running (from step 3.1).
- [ ] In the AE panel, observe the status dot in the top-right corner.
  - After ~3 seconds, it should turn **green** and display "Backend connected"
  - If it stays **red**, verify the backend is running on `http://127.0.0.1:8000`

  **PASS** ☐ / **FAIL** ☐

### 5.2 Test Connection (ExtendScript Bridge)

- [ ] In the AE panel, click the **Test Connection** button.
  - Status should briefly say "Testing connection…" (yellow dot)
  - Then change to "AE connected ✓" (green dot)

  **PASS** ☐ / **FAIL** ☐

### 5.3 Analyze a Prompt (panel → backend)

- [ ] Type the following into the prompt text area:

      zoom in on every beat with flash

- [ ] Click **Analyze**.
  - Status should show "Analyzing…" briefly
  - Then "Analysis ready" or "Local analysis"
  - The results section should appear below with action items:
    - Detect beats
    - Add zoom effect
    - Add flash effect

  **PASS** ☐ / **FAIL** ☐

---

## 6. Media Tests

### 6.1 Prepare Test Media

- [ ] Find or create a short video file (10–30 seconds, MP4 or MOV format).
  - Any anime clip, screen recording, or test video will work.
  - Recommended: a 15-second clip with visible motion and scene changes.
- [ ] Note the **full file path** to this video, e.g.:

      C:\Users\Public\Videos\test_clip.mp4

### 6.2 Scene Detection (API)

- [ ] Ensure the backend is running.
- [ ] In the second Command Prompt window, run:

      curl -X POST http://127.0.0.1:8000/detect-scenes ^
        -H "Content-Type: application/json" ^
        -d "{\"video_path\":\"C:\\Path\\To\\Your\\video.mp4\",\"fps\":1,\"threshold\":0.3}"

  Expected output: a JSON response with `segments` array, `total_scenes`, and `analysis_fps`.
  - If you get a 400 error "Cannot open video", verify the path is correct.

  **PASS** ☐ / **FAIL** ☐

### 6.3 Beat Detection (API)

- [ ] Find or create an audio file (10–30 seconds, WAV or MP3).
  - Any music with a clear beat works best.
- [ ] Run:

      curl -X POST http://127.0.0.1:8000/detect-beats ^
        -H "Content-Type: application/json" ^
        -d "{\"audio_path\":\"C:\\Path\\To\\Your\\audio.wav\"}"

  Expected output: a JSON response with `beats` array, `bpm`, `total_beats`, and `duration_seconds`.

  **PASS** ☐ / **FAIL** ☐

### 6.4 Full Pipeline: Analyze + Generate Plan + Apply

- [ ] Run analyze on a media-related prompt:

      curl -X POST http://127.0.0.1:8000/analyze ^
        -H "Content-Type: application/json" ^
        -d "{\"prompt\":\"cut scenes on beats, add zoom and flash\"}"

- [ ] Take the output and send it to `/generate-plan` with actual scene/beat data (use output from 6.2 and 6.3).
- [ ] Take the resulting plan actions and send them to `/apply-edit`.

  All three endpoints should return valid JSON with no errors.

  **PASS** ☐ / **FAIL** ☐

---

## 7. Failure Cases

### 7.1 Empty Prompt

- [ ] Run:

      curl -X POST http://127.0.0.1:8000/analyze ^
        -H "Content-Type: application/json" ^
        -d "{\"prompt\":\"\"}"

  Expected: HTTP 400 with `{"detail":"Prompt cannot be empty"}`

  **PASS** ☐ / **FAIL** ☐

### 7.2 Invalid Video Path

- [ ] Run:

      curl -X POST http://127.0.0.1:8000/detect-scenes ^
        -H "Content-Type: application/json" ^
        -d "{\"video_path\":\"C:\\nonexistent\\video.mp4\"}"

  Expected: HTTP 400 with an error detail containing "Cannot open" or similar.

  **PASS** ☐ / **FAIL** ☐

### 7.3 Invalid Audio Path

- [ ] Run:

      curl -X POST http://127.0.0.1:8000/detect-beats ^
        -H "Content-Type: application/json" ^
        -d "{\"audio_path\":\"C:\\nonexistent\\audio.wav\"}"

  Expected: HTTP 400 with an error detail about failed to load audio.

  **PASS** ☐ / **FAIL** ☐

### 7.4 No Actions Provided

- [ ] Run:

      curl -X POST http://127.0.0.1:8000/apply-edit ^
        -H "Content-Type: application/json" ^
        -d "{\"actions\":[]}"

  Expected: HTTP 400 with `{"detail":"No actions provided"}`

  **PASS** ☐ / **FAIL** ☐

### 7.5 No API Key (graceful degradation)

- [ ] Run with an invalid API key (simulates auth failure):

      curl -X POST http://127.0.0.1:8000/analyze ^
        -H "Content-Type: application/json" ^
        -d "{\"prompt\":\"zoom\",\"provider\":\"openrouter\",\"api_key\":\"sk-invalid\"}"

  Expected: The request may fail (the backend will try the real API and fall back to local parsing). Either:
  - A successful response with local-parser actions, OR
  - An HTTP error from the provider

  Either outcome is acceptable (the system degrades gracefully).

  **PASS** ☐ / **FAIL** ☐

### 7.6 Backend Offline

- [ ] Stop the backend server (`Ctrl+C` in the first terminal window).
- [ ] In the AE panel, observe:
  - The status dot turns **red** within 15 seconds
  - Status text reads "Backend offline"
- [ ] Click **Analyze** — the panel should still show results using local-only analysis.

  **PASS** ☐ / **FAIL** ☐

- [ ] Restart the backend server for subsequent tests.

---

## 8. Expected Outputs Reference

### Health Check
```json
{"status":"ok","version":"0.1.0"}
```

### Analyze (local, no API key)
```json
{
  "prompt": "cut every 4 beats with zoom",
  "actions": [
    {"type":"beat_detect","label":"Detect beats","params":{}},
    {"type":"scene_detect","label":"Detect scene cuts","params":{}},
    {"type":"zoom","label":"Add zoom effect","params":{}}
  ]
}
```

### Generate Plan
```json
{
  "plan": {
    "prompt": "...",
    "bpm": 120.0,
    "timeline": [
      {"segment_index": 0, "keep": true, "order": 0},
      {"segment_index": 1, "keep": false, "order": -1}
    ],
    "effects": [
      {"type": "zoom", "segment_index": 0, "beat_index": null, "params": {...}},
      {"type": "flash", "segment_index": null, "beat_index": 0, "params": {...}}
    ]
  }
}
```

### Apply Edit
```json
{
  "applied": ["ae.applyZoom(1, '{\"magnitude\":1.3}')"],
  "status": "ok"
}
```

### Scene Detection
```json
{
  "video_path": "C:\\path\\to\\video.mp4",
  "segments": [
    {"start_time": 0.0, "end_time": 1.0, "motion_score": 2.5, "confidence": 0.95}
  ],
  "total_scenes": 5,
  "analysis_fps": 1.0
}
```

### Beat Detection
```json
{
  "audio_path": "C:\\path\\to\\audio.wav",
  "beats": [
    {"time_seconds": 0.5, "bpm": 128.0, "confidence": 0.9, "drop_intensity": 0.3}
  ],
  "bpm": 128.0,
  "total_beats": 64,
  "duration_seconds": 30.0
}
```

---

## 9. Result Summary

| Section | Max Checks | Passed |
|---|---|---|
| 1. Environment Setup | — | ☐ / ☐ |
| 2. Project Setup | — | ☐ / ☐ |
| 3. Backend Smoke Tests | — | ☐ / ☐ |
| 4. AE Plugin Installation | — | ☐ / ☐ |
| 5. Panel Connection Tests | — | ☐ / ☐ |
| 6. Media Tests | — | ☐ / ☐ |
| 7. Failure Cases | — | ☐ / ☐ |

**FINAL RESULT**: **PASS** ☐ / **FAIL** ☐

If all checks pass, the MVP is ready for use.

---

## Troubleshooting Quick Reference

| Symptom | Likely Cause | Fix |
|---|---|---|
| `python` not found | Python not installed or not in PATH | Reinstall Python, check "Add to PATH" |
| `pip install` fails | Missing build tools | Install Microsoft C++ Build Tools |
| Panel not in AE menu | Plugin not in correct folder or CSXS.8 registry missing | Recheck `CEP\extensions` path and `CSXS.8` regedit key |
| `Backend offline` in panel | Server not running | Start `uvicorn app.main:app` |
| `FFmpeg not found` warning | FFmpeg not on PATH | Install FFmpeg or ignore (OpenCV fallback works) |
| `curl` not recognized | curl not installed | Use browser for GET, or install curl |
| Scene detection returns 400 | Video path invalid or file missing | Use absolute path with double backslashes |
| Tests fail on Windows | Line endings or path separators | Run `git config --global core.autocrlf true` then re-clone |
