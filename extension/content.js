// content.js — Injected into every page
// Responsibilities:
//   1. Notify background of text selections (for context menu)
//   2. Handle dynamic DOM via MutationObserver (Twitter/X, Reddit, etc.)
//   3. Show inline "Analyze" floating button on long selections (optional UX)

(function () {
  "use strict";

  let lastSelection = "";
  let floatBtn = null;

  // ── SELECTION LISTENER ────────────────────────────────────────────────────
  document.addEventListener("mouseup", handleSelection);
  document.addEventListener("keyup", handleSelection);

  function handleSelection() {
    const selection = window.getSelection();
    if (!selection) return;

    const text = selection.toString().trim();

    // Nothing selected or too short
    if (!text || text.length < 20) {
      removeFloatBtn();
      return;
    }

    // Same text as before — no need to update
    if (text === lastSelection) return;
    lastSelection = text;

    // Show floating button near selection end
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    showFloatBtn(rect, text);
  }

  // ── FLOATING BUTTON ───────────────────────────────────────────────────────
  function showFloatBtn(rect, text) {
    removeFloatBtn();

    floatBtn = document.createElement("div");
    floatBtn.id = "__polafusion_btn__";
    floatBtn.textContent = "🌍 Analyze";
    floatBtn.style.cssText = `
      position: fixed;
      z-index: 2147483647;
      top: ${Math.max(0, rect.bottom + window.scrollY - rect.top + rect.top + 8)}px;
      left: ${rect.left + window.scrollX}px;
      background: #1e293b;
      color: #f1f5f9;
      padding: 5px 12px;
      border-radius: 6px;
      font-size: 13px;
      font-family: system-ui, sans-serif;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.4);
      user-select: none;
      transition: background 0.15s;
    `;

    // Position relative to viewport (fixed), not document
    floatBtn.style.top = `${rect.bottom + 8}px`;
    floatBtn.style.left = `${rect.left}px`;

    floatBtn.addEventListener("mouseenter", () => {
      floatBtn.style.background = "#ef4444";
    });
    floatBtn.addEventListener("mouseleave", () => {
      floatBtn.style.background = "#1e293b";
    });

    floatBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      e.preventDefault();
      chrome.runtime.sendMessage({ type: "ANALYZE_TEXT", text });
      removeFloatBtn();
    });

    document.body.appendChild(floatBtn);

    // Auto-dismiss after 5 seconds
    setTimeout(removeFloatBtn, 5000);
  }

  function removeFloatBtn() {
    if (floatBtn) {
      floatBtn.remove();
      floatBtn = null;
    }
  }

  // Remove float button when clicking elsewhere
  document.addEventListener("mousedown", (e) => {
    if (floatBtn && !floatBtn.contains(e.target)) {
      removeFloatBtn();
    }
  });

  // ── MUTATIONOBSERVER — for Twitter/X, Reddit, etc. ────────────────────────
  // Dynamic pages remove and re-add DOM nodes, which can break text selection.
  // We watch for significant DOM changes and reset our selection state.
  const observer = new MutationObserver((mutations) => {
    const significant = mutations.some(
      (m) => m.addedNodes.length > 0 || m.removedNodes.length > 0
    );
    if (significant) {
      // If the current selection no longer exists in DOM, clear state
      const sel = window.getSelection();
      if (!sel || sel.toString().trim() === "") {
        lastSelection = "";
        removeFloatBtn();
      }
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });

  // ── KEYBOARD SHORTCUT: Alt+P ──────────────────────────────────────────────
  document.addEventListener("keydown", (e) => {
    if (e.altKey && e.key === "p") {
      const text = window.getSelection()?.toString().trim();
      if (text && text.length >= 20) {
        chrome.runtime.sendMessage({ type: "ANALYZE_TEXT", text });
      }
    }
  });
})();
