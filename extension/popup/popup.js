// popup.js — PolaFusion v2
// Per-mode result cache. Mode toggle re-runs or shows cached result instantly.
// Ensemble always calls ensemble — never degrades.

const API_BASE = "http://127.0.0.1:8000";

const $ = (id) => document.getElementById(id);

const states = {
  idle:    $("stateIdle"),
  loading: $("stateLoading"),
  error:   $("stateError"),
  result:  $("stateResult"),
};

// Session state — backed by chrome.storage.local so it survives popup close/reopen
let _sessionText = null;
let _cache = { fallback: null, ensemble: null };
let _currentMode = "fallback";
let _loadingMode = null;

// ─── INIT ─────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  const stored = await chrome.storage.local.get(["sessionText", "sessionCache", "mode", "bgStatus"]);
  _sessionText = stored.sessionText  || null;
  _cache       = stored.sessionCache || { fallback: null, ensemble: null };
  _currentMode = stored.mode         || "fallback";

  setActiveMode(_currentMode);
  updateModeLabels();

  $("btnFallback").addEventListener("click", () => switchMode("fallback"));
  $("btnEnsemble").addEventListener("click", () => switchMode("ensemble"));

  // Check if background just signaled new text
  if (stored.bgStatus?.type === "new_text" && stored.bgStatus.text !== _sessionText) {
    await chrome.storage.local.set({ bgStatus: null });
    startNewSession(stored.bgStatus.text);
    return;
  }

  listenForUpdates();
  renderCurrentState();
});

// ─── STORAGE LISTENER (background signals new text while popup is open) ───────
function listenForUpdates() {
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local") return;
    if (changes.bgStatus?.newValue?.type === "new_text") {
      chrome.storage.local.set({ bgStatus: null });
      startNewSession(changes.bgStatus.newValue.text);
    }
  });
}

// ─── NEW SESSION ──────────────────────────────────────────────────────────────
async function startNewSession(text) {
  _sessionText = text;
  _cache = { fallback: null, ensemble: null };
  await chrome.storage.local.set({ sessionText: text, sessionCache: _cache });
  updateModeLabels();
  runAnalysis(text, _currentMode);
}

// ─── MODE SWITCH ──────────────────────────────────────────────────────────────
async function switchMode(mode) {
  _currentMode = mode;
  await chrome.storage.local.set({ mode });
  setActiveMode(mode);

  if (_cache[mode]) {
    // Already have result — show instantly
    showState("result");
    renderResult(_cache[mode]);
    setupFeedback(_cache[mode], _sessionText);
    setupCopy(_cache[mode]);
    return;
  }

  if (!_sessionText) { showState("idle"); return; }

  // No cache for this mode yet — fetch it
  runAnalysis(_sessionText, mode);
}

function setActiveMode(mode) {
  $("btnFallback").classList.toggle("active", mode === "fallback");
  $("btnEnsemble").classList.toggle("active", mode === "ensemble");
}

function updateModeLabels() {
  $("btnFallback").textContent = _cache.fallback ? "⚡ Fast ✓" : "⚡ Fast";
  $("btnEnsemble").textContent = _cache.ensemble ? "🔥 Full ✓" : "🔥 Full";
}

// ─── ANALYSIS ─────────────────────────────────────────────────────────────────
async function runAnalysis(text, mode) {
  if (_loadingMode === mode) return;
  _loadingMode = mode;

  showState("loading");
  $("loadingText").textContent = mode === "ensemble" ? "Running full ensemble…" : "Analyzing…";
  $("loadingHint").textContent = mode === "ensemble" ? "8 models · 30–90s" : "Fast mode · ~2s";

  try {
    const response = await fetch(`${API_BASE}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, mode }),  // mode passed exactly — no fallback
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${response.status}`);
    }

    const result = await response.json();
    _cache[mode] = result;
    await chrome.storage.local.set({ sessionCache: _cache });

    if (_currentMode === mode) {
      showState("result");
      renderResult(result);
      setupFeedback(result, text);
      setupCopy(result);
    }
  } catch (err) {
    if (_currentMode === mode) {
      showState("error");
      $("errorMsg").textContent = err.message || "Could not reach API.";
      $("btnRetry").onclick = () => runAnalysis(text, mode);
    }
  } finally {
    _loadingMode = null;
    updateModeLabels();
  }
}

// ─── RENDER CURRENT STATE ─────────────────────────────────────────────────────
function renderCurrentState() {
  if (_cache[_currentMode]) {
    showState("result");
    renderResult(_cache[_currentMode]);
    setupFeedback(_cache[_currentMode], _sessionText);
    setupCopy(_cache[_currentMode]);
  } else if (_sessionText) {
    runAnalysis(_sessionText, _currentMode);
  } else {
    showState("idle");
  }
}

function showState(name) {
  Object.entries(states).forEach(([key, el]) => {
    el.classList.toggle("hidden", key !== name);
  });
}

// ─── RENDER RESULT ────────────────────────────────────────────────────────────
function renderResult(r) {
  $("langFlag").textContent = r.language_flag || "🌐";
  $("langName").textContent = r.language_name || r.detected_language;

  const tierBadge = $("tierBadge");
  tierBadge.textContent = r.confidence_tier === "high" ? "✓ High Accuracy"
    : r.confidence_tier === "medium" ? "~ Medium Accuracy" : "⚠ Limited Accuracy";
  tierBadge.className = `tier-badge tier-${r.confidence_tier}`;

  $("textPreview").textContent = r.text_preview || "";
  $("timingLabel").textContent = r.processing_ms ? `${r.processing_ms}ms · ${r.mode_used}` : "";

  renderSubtask1(r.subtask1);
  renderSubtask2(r.subtask2);
  renderSubtask3(r.subtask3);
  updateModeLabels();
}

function renderSubtask1(st1) {
  if (!st1) return;
  const isPolarized = st1.label === 1;
  const pct = Math.round((st1.probability || 0) * 100);
  const verdict = $("st1Verdict");
  verdict.textContent = isPolarized ? "🔴 POLARIZED" : "🟢 NOT POLARIZED";
  verdict.className = `st1-verdict ${isPolarized ? "verdict-polarized" : "verdict-neutral"}`;
  $("st1Score").textContent = `${pct}%`;
  const bar = $("st1Bar");
  bar.style.width = `${pct}%`;
  bar.style.background = isPolarized ? `hsl(${Math.round((1 - st1.probability) * 40)}, 80%, 50%)` : "#22c55e";
}

const TYPE_DISPLAY = {
  "political": "Political", "racial/ethnic": "Racial/Ethnic",
  "religious": "Religious", "gender/sexual": "Gender/Sexual", "other": "Other",
};

function renderSubtask2(st2) {
  const el = $("st2Content");
  if (!st2) { el.innerHTML = ""; return; }
  if (st2.gated_out) { el.innerHTML = `<p class="gated-msg">Not applicable — text is not polarized.</p>`; return; }
  if (!st2.labels)   { el.innerHTML = ""; return; }
  el.innerHTML = `<div class="type-badges">${
    Object.entries(st2.labels).map(([k, v]) =>
      `<span class="type-badge ${v.predicted === 1 ? "active" : "inactive"}">${TYPE_DISPLAY[k] || k}</span>`
    ).join("")
  }</div>`;
}

const MANIF_DISPLAY = {
  "stereotype": "Stereotype", "vilification": "Vilification",
  "dehumanization": "Dehumanization", "extreme_language": "Extreme Lang.",
  "lack_of_empathy": "Lack of Empathy", "invalidation": "Invalidation",
};

function renderSubtask3(st3) {
  const el = $("st3Content");
  if (!st3) { el.innerHTML = ""; return; }
  if (!st3.available) { el.innerHTML = `<p class="unavailable-msg">Not available for this language.</p>`; return; }
  if (st3.gated_out)  { el.innerHTML = `<p class="gated-msg">Not applicable — text is not polarized.</p>`; return; }
  if (st3.suppressed) { el.innerHTML = `<p class="suppressed-msg">⚠️ ${st3.warning || "Unreliable for this language."}</p>`; return; }
  if (!st3.labels)    { el.innerHTML = ""; return; }
  const sorted = Object.entries(st3.labels).sort(([, a], [, b]) => b.score - a.score);
  el.innerHTML = `<div class="manif-rows">${sorted.map(([k, v]) => {
    const pct = Math.round(v.score * 100);
    return `<div class="manif-row">
      <span class="manif-label">${MANIF_DISPLAY[k] || k}</span>
      <div class="manif-bar-wrap"><div class="manif-bar ${v.predicted === 1 ? "predicted" : "not-predicted"}" style="width:${pct}%"></div></div>
      <span class="manif-score">${pct}%</span>
    </div>`;
  }).join("")}</div>`;
}

// ─── FEEDBACK ─────────────────────────────────────────────────────────────────
function setupFeedback(result, selectedText) {
  let sent = false;
  async function sendFeedback(correct) {
    if (sent) return; sent = true;
    $("btnThumbUp").classList.toggle("selected", correct === 1);
    $("btnThumbDown").classList.toggle("selected", correct === 0);
    try {
      await fetch(`${API_BASE}/feedback`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: selectedText || "", lang_code: result.detected_language,
          mode_used: result.mode_used, st1_predicted: result.subtask1?.label ?? -1,
          st1_correct: correct, raw_response: result }),
      });
    } catch (_) {}
    $("feedbackConfirm").classList.remove("hidden");
    setTimeout(() => $("feedbackConfirm").classList.add("hidden"), 2500);
  }
  $("btnThumbUp").onclick   = () => sendFeedback(1);
  $("btnThumbDown").onclick = () => sendFeedback(0);
}

// ─── COPY ─────────────────────────────────────────────────────────────────────
function setupCopy(result) {
  $("btnCopy").onclick = () => {
    const lines = [
      `PolaFusion Analysis`, `Language: ${result.language_name} ${result.language_flag}`,
      `Accuracy: ${result.confidence_tier}`, ``,
      `ST1: ${result.subtask1?.label === 1 ? "POLARIZED" : "NOT POLARIZED"} (${Math.round((result.subtask1?.probability || 0) * 100)}%)`,
    ];
    if (result.subtask2?.labels && !result.subtask2?.gated_out) {
      const types = Object.entries(result.subtask2.labels).filter(([,v]) => v.predicted===1).map(([k]) => TYPE_DISPLAY[k]||k);
      lines.push(`ST2 Types: ${types.length ? types.join(", ") : "None"}`);
    }
    if (result.subtask3?.labels && !result.subtask3?.gated_out && !result.subtask3?.suppressed) {
      const mfs = Object.entries(result.subtask3.labels).filter(([,v]) => v.predicted===1).map(([k]) => MANIF_DISPLAY[k]||k);
      lines.push(`ST3 Manifestations: ${mfs.length ? mfs.join(", ") : "None"}`);
    }
    lines.push(``, `Mode: ${result.mode_used} | Time: ${result.processing_ms}ms`);
    navigator.clipboard.writeText(lines.join("\n")).then(() => {
      $("btnCopy").textContent = "✅ Copied";
      setTimeout(() => { $("btnCopy").textContent = "📋 Copy"; }, 1500);
    });
  };
}
