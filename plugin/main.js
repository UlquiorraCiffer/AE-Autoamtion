(() => {
  'use strict'

  let csInterface = null

  if (typeof CSInterface !== 'undefined') {
    csInterface = new CSInterface()
  }

  /* ─── State ─── */
  const state = {
    apiKey: '',
    provider: 'openrouter',
    model: 'gpt-4o-mini',
    settingsOpen: false,
    backendUrl: 'http://127.0.0.1:8000',
    connected: false,
    analyzing: false,
    analysisResult: null,
    editPlan: null,
  }

  /* ─── DOM refs ─── */
  const $ = (id) => document.getElementById(id)
  const promptInput = $('prompt-input')
  const btnAnalyze = $('btn-analyze')
  const btnApply = $('btn-apply')
  const btnTest = $('btn-test')
  const btnSettings = $('btn-settings')
  const settingsPanel = $('settings-panel')
  const resultsSection = $('results-section')
  const resultsContent = $('results-content')
  const apiKeyInput = $('api-key')
  const providerSelect = $('provider-select')
  const modelSelect = $('model-select')
  const statusDot = $('status-dot')
  const statusText = $('status-text')

  /* ─── Polyfill: AbortSignal.timeout for Chromium 69 ─── */
  function timeoutSignal(ms) {
    var ctrl = new AbortController()
    setTimeout(function () { ctrl.abort() }, ms)
    return ctrl.signal
  }

  /* ─── Helpers ─── */
  async function testConnection() {
    if (!csInterface) {
      setStatus('AE not available', 'offline')
      return
    }
    btnTest.disabled = true
    setStatus('Testing connection…', 'busy')
    try {
      const result = await evalAE('ae.ping()')
      if (result === 'pong') {
        setStatus('AE connected ✓', 'online')
      } else {
        setStatus('Unexpected response', 'offline')
      }
    } catch {
      setStatus('AE call failed', 'offline')
    } finally {
      btnTest.disabled = false
    }
  }

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
      const res = await fetch(`${state.backendUrl}/health`, { signal: timeoutSignal(3000) })
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

    const payload = {
      prompt: text,
      provider: state.provider,
      model: state.model,
      api_key: state.apiKey || undefined,
    }

    try {
      const res = await fetch(`${state.backendUrl}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: timeoutSignal(30000),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const data = await res.json()
      state.analysisResult = data
      renderResults(data)
      btnApply.disabled = false
      setStatus('Analysis ready', 'online')
    } catch (err) {
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
      actions.push({ type: 'zoom', label: 'Add zoom effect', params: { magnitude: 1.3, direction: 'in' } })
    }

    if (/shake/i.test(lower) || /wiggle/i.test(lower)) {
      actions.push({ type: 'shake', label: 'Add shake effect', params: { frequency: 15, amplitude: 20 } })
    }

    if (/flash/i.test(lower)) {
      actions.push({ type: 'flash', label: 'Add flash effect', params: { opacity: 80, duration_seconds: 0.05 } })
    }

    if (/glow/i.test(lower)) {
      actions.push({ type: 'glow', label: 'Add glow effect', params: { intensity: 0.5, radius: 30 } })
    }

    if (/speed ramp|velocity/i.test(lower)) {
      actions.push({ type: 'velocity_ramp', label: 'Add velocity ramp', params: { speed: 1.5, ramp_in: 0.2, ramp_out: 0.3 } })
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
          const result = await evalAE(script)
          console.log(`[AE] ${action.type}: ${result}`)
        }
      } catch (err) {
        console.warn(`[AE] ${action.type} failed:`, err)
      }
    }

    btnApply.disabled = false
    setStatus('Applied', 'online')
  }

  /* ─── Build ExtendScript for an action ─── */
  function buildExtendScript(action) {
    const params = action.params || {}
    const json = JSON.stringify(params)

    switch (action.type) {
      case 'beat_detect':
        return null  // handled by backend
      case 'scene_detect':
        return null  // handled by backend
      case 'zoom':
        return `ae.applyZoom(1, '${escapeJS(json)}')`
      case 'shake':
        return `ae.applyShake(1, '${escapeJS(json)}')`
      case 'flash':
        return `ae.applyFlash('${escapeJS(json)}')`
      case 'glow':
        return `ae.applyGlow(1, '${escapeJS(json)}')`
      case 'velocity_ramp':
        return `ae.applyVelocityRamp(1, '${escapeJS(json)}')`
      case 'split':
        return `ae.splitLayer(${action.params.layerIndex || 1}, ${action.params.time || 0})`
      case 'trim':
        return `ae.trimLayer(${action.params.layerIndex || 1}, ${action.params.inTime || 0}, ${action.params.outTime || 0})`
      case 'add_markers':
        return `ae.addMarkers('${escapeJS(json)}')`
      case 'reorder':
        return `ae.reorderLayers('${escapeJS(json)}')`
      case 'execute_plan':
        return `ae.executePlan('${escapeJS(JSON.stringify(state.editPlan || {}))}')`
      default:
        return null
    }
  }

  function escapeJS(str) {
    return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n')
  }

  /* ─── Settings toggle ─── */
  function toggleSettings() {
    state.settingsOpen = !state.settingsOpen
    settingsPanel.classList.toggle('hidden', !state.settingsOpen)
  }

  function saveSettings() {
    state.apiKey = apiKeyInput.value.trim()
    state.provider = providerSelect.value
    state.model = modelSelect.value
  }

  /* ─── Init ─── */
  async function init() {
    if (csInterface) {
      try {
        const key = await evalAE('ae.getSettings()')
        if (key) {
          const parsed = JSON.parse(key)
          state.apiKey = parsed.apiKey || ''
          state.provider = parsed.provider || 'openrouter'
          state.model = parsed.model || 'gpt-4o-mini'
          apiKeyInput.value = state.apiKey
          providerSelect.value = state.provider
          modelSelect.value = state.model
        }
      } catch {
        // ignore
      }
    }

    checkBackend()
    setInterval(checkBackend, 15000)

    btnAnalyze.addEventListener('click', () => analyzePrompt(promptInput.value))
    btnApply.addEventListener('click', applyActions)
    btnTest.addEventListener('click', testConnection)

    btnSettings.addEventListener('click', toggleSettings)

    apiKeyInput.addEventListener('input', saveSettings)
    providerSelect.addEventListener('change', saveSettings)
    modelSelect.addEventListener('change', saveSettings)

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
