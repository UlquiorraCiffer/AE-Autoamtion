(() => {
  'use strict'

  let csInterface = null

  if (typeof CSInterface !== 'undefined') {
    csInterface = new CSInterface()
  }

  /* ─── State ─── */
  const state = {
    apiKey: '',
    model: 'gpt-4o-mini',
    settingsOpen: false,
    backendUrl: 'http://127.0.0.1:8000',
    connected: false,
    analyzing: false,
    analysisResult: null,
  }

  /* ─── DOM refs ─── */
  const $ = (id) => document.getElementById(id)
  const promptInput = $('prompt-input')
  const btnAnalyze = $('btn-analyze')
  const btnApply = $('btn-apply')
  const btnSettings = $('btn-settings')
  const settingsPanel = $('settings-panel')
  const resultsSection = $('results-section')
  const resultsContent = $('results-content')
  const apiKeyInput = $('api-key')
  const modelSelect = $('model-select')
  const statusDot = $('status-dot')
  const statusText = $('status-text')

  /* ─── Helpers ─── */
  function setStatus(text, level) {
    statusText.textContent = text
    statusDot.className = 'dot'
    statusDot.classList.add(level || 'offline')
  }

  function evalAE(script) {
    return new Promise((resolve, reject) => {
      if (!csInterface) {
        reject(new Error('CSInterface not available'))
        return
      }
      csInterface.evalScript(script, (result) => {
        resolve(result)
      })
    })
  }

  /* ─── Backend communication ─── */
  async function checkBackend() {
    try {
      const res = await fetch(`${state.backendUrl}/health`, { signal: AbortSignal.timeout(3000) })
      if (res.ok) {
        state.connected = true
        setStatus('Backend connected', 'online')
        return true
      }
    } catch {
      // fall through
    }
    state.connected = false
    setStatus('Backend offline', 'offline')
    return false
  }

  async function analyzePrompt(text) {
    if (!text.trim()) return

    state.analyzing = true
    btnAnalyze.disabled = true
    btnApply.disabled = true
    setStatus('Analyzing…', 'busy')

    // Build payload for the backend LLM router
    const payload = {
      prompt: text,
      model: state.model,
      api_key: state.apiKey || undefined,
    }

    try {
      const res = await fetch(`${state.backendUrl}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(30000),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const data = await res.json()
      state.analysisResult = data
      renderResults(data)
      btnApply.disabled = false
      setStatus('Analysis ready', 'online')
    } catch (err) {
      // Offline fallback — still show parsed result shape for demo
      state.analysisResult = { actions: parsePromptLocally(text) }
      renderResults(state.analysisResult)
      btnApply.disabled = false
      setStatus('Local analysis', 'online')
    } finally {
      state.analyzing = false
      btnAnalyze.disabled = false
    }
  }

  /* ─── Fallback local parser ─── */
  function parsePromptLocally(text) {
    const lower = text.toLowerCase()
    const actions = []

    if (/beat/i.test(lower) || /bpm/i.test(lower)) {
      actions.push({ type: 'beat_detect', label: 'Detect beats', params: {} })
    }

    if (/scene/i.test(lower) || /cut/i.test(lower)) {
      actions.push({ type: 'scene_detect', label: 'Detect scene cuts', params: {} })
    }

    if (/zoom/i.test(lower) || /punch/i.test(lower)) {
      actions.push({ type: 'zoom', label: 'Add zoom effect', params: {} })
    }

    if (/shake/i.test(lower) || /wiggle/i.test(lower)) {
      actions.push({ type: 'shake', label: 'Add shake effect', params: {} })
    }

    if (/flash/i.test(lower)) {
      actions.push({ type: 'flash', label: 'Add flash effect', params: {} })
    }

    if (actions.length === 0) {
      actions.push({ type: 'unknown', label: 'Unrecognised prompt — try describing cuts, beats, or effects', params: {} })
    }

    return actions
  }

  /* ─── Render results ─── */
  function renderResults(data) {
    resultsContent.innerHTML = ''
    resultsSection.classList.remove('hidden')

    const actions = data.actions || []
    if (actions.length === 0) {
      const div = document.createElement('div')
      div.className = 'result-item muted'
      div.textContent = 'No actions generated.'
      resultsContent.appendChild(div)
      return
    }

    for (const action of actions) {
      const div = document.createElement('div')
      div.className = 'result-item'
      const label = action.label || action.type
      div.textContent = label
      resultsContent.appendChild(div)
    }
  }

  /* ─── Apply actions to AE ─── */
  async function applyActions() {
    if (!state.analysisResult) return

    btnApply.disabled = true
    setStatus('Applying…', 'busy')

    const actions = state.analysisResult.actions || []

    for (const action of actions) {
      try {
        const script = buildExtendScript(action)
        if (script) {
          await evalAE(script)
        }
      } catch {
        // continue with next action
      }
    }

    btnApply.disabled = false
    setStatus('Applied', 'online')
  }

  /* ─── Build ExtendScript for an action ─── */
  function buildExtendScript(action) {
    switch (action.type) {
      case 'beat_detect':
        return 'ae.beatDetect()'
      case 'scene_detect':
        return 'ae.sceneDetect()'
      case 'zoom':
        return 'ae.addZoom()'
      case 'shake':
        return 'ae.addShake()'
      case 'flash':
        return 'ae.addFlash()'
      default:
        return null
    }
  }

  /* ─── Settings toggle ─── */
  function toggleSettings() {
    state.settingsOpen = !state.settingsOpen
    settingsPanel.classList.toggle('hidden', !state.settingsOpen)
  }

  function saveSettings() {
    state.apiKey = apiKeyInput.value.trim()
    state.model = modelSelect.value
  }

  /* ─── Init ─── */
  async function init() {
    // Load persisted settings
    if (csInterface) {
      try {
        const key = await evalAE('ae.getSettings()')
        if (key) {
          const parsed = JSON.parse(key)
          state.apiKey = parsed.apiKey || ''
          state.model = parsed.model || 'gpt-4o-mini'
          apiKeyInput.value = state.apiKey
          modelSelect.value = state.model
        }
      } catch {
        // ignore
      }
    }

    // Check backend
    checkBackend()
    setInterval(checkBackend, 15000)

    // Listeners
    btnAnalyze.addEventListener('click', () => analyzePrompt(promptInput.value))
    btnApply.addEventListener('click', applyActions)

    btnSettings.addEventListener('click', toggleSettings)

    apiKeyInput.addEventListener('input', saveSettings)
    modelSelect.addEventListener('change', saveSettings)

    // Keyboard shortcut
    promptInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault()
        analyzePrompt(promptInput.value)
      }
    })
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
  } else {
    init()
  }
})()
