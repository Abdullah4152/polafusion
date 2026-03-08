// background.js — Service Worker v2
// Only responsibility: detect text selection, signal the popup via storage.
// The popup owns ALL fetch logic so it can manage per-mode caching.

const API_BASE = "http://127.0.0.1:8000";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "polafusion-analyze",
    title: "🌍 Analyze with PolaFusion",
    contexts: ["selection"],
  });
  chrome.storage.local.get(["mode"], (r) => {
    if (!r.mode) chrome.storage.local.set({ mode: "fallback" });
  });
});

chrome.contextMenus.onClicked.addListener(async (info) => {
  if (info.menuItemId !== "polafusion-analyze") return;

  const text = info.selectionText?.trim();
  if (!text || text.length < 20) {
    await chrome.storage.local.set({
      bgStatus: { type: "error", message: "Select at least 20 characters." },
    });
    chrome.action.openPopup().catch(() => {});
    return;
  }

  await chrome.storage.local.set({
    sessionText: text,
    sessionCache: { fallback: null, ensemble: null },
    bgStatus: { type: "new_text", text },
  });
  chrome.action.openPopup().catch(() => {});
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "ANALYZE_TEXT") {
    const text = message.text?.trim();
    if (text && text.length >= 20) {
      chrome.storage.local.set({
        sessionText: text,
        sessionCache: { fallback: null, ensemble: null },
        bgStatus: { type: "new_text", text },
      });
      chrome.action.openPopup().catch(() => {});
    }
    sendResponse({ received: true });
  }
  if (message.type === "GET_API_BASE") {
    sendResponse({ apiBase: API_BASE });
  }
  return true;
});
