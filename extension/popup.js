// ============================================================
// popup.js — NotionClip Chrome Extension
// ROLE: UI state machine only. All network goes via background.js
// ============================================================

// ── DOM References ───────────────────────────────────────────
const videoStrip    = document.getElementById("videoStrip");
const elVideoTitle  = document.getElementById("videoTitle");
const elVideoUrl    = document.getElementById("videoUrl");

const stateIdle     = document.getElementById("stateIdle");
const stateLoading  = document.getElementById("stateLoading");
const stateResult   = document.getElementById("stateResult");
const stateError    = document.getElementById("stateError");

const btnAnalyse    = document.getElementById("btnAnalyse");
const loadingText   = document.getElementById("loadingText");
const loadingSub    = document.getElementById("loadingSub");
const loadingMeta   = document.getElementById("loadingMeta");

const verdictBadge  = document.getElementById("verdictBadge");
const verdictIconWatch = document.getElementById("verdictIconWatch");
const verdictIconSkip = document.getElementById("verdictIconSkip");
const verdictWord   = document.getElementById("verdictWord");
const oneLiner      = document.getElementById("oneLiner");
const btnSave       = document.getElementById("btnSave");
const reanalyseRow  = document.getElementById("reanalyseRow");
const reanalyseBtn  = document.getElementById("reanalyseBtn");

const errorTitle    = document.getElementById("errorTitle");
const errorDesc     = document.getElementById("errorDesc");
const errorDebug    = document.getElementById("errorDebug");
const btnRetry      = document.getElementById("btnRetry");
const btnClosePanel = document.getElementById("btnClosePanel");


// ── App State ────────────────────────────────────────────────
let currentVideoData  = null;   // { videoId, videoTitle, videoUrl, transcriptBaseUrl }
let lastAnalysisResult = null;  // full result object from backend
let loadingTimer      = null;   // interval for loading text rotation
let currentTabId      = null;   // active YouTube tab id


// ── Error Messages Map ───────────────────────────────────────
const ERROR_MESSAGES = {
  NOT_YOUTUBE_VIDEO: {
    title: "Not a YouTube video",
    desc: "Go to a YouTube video page (youtube.com/watch?v=...) and try again."
  },
  PAGE_NOT_LOADED: {
    title: "Page still loading",
    desc: "The YouTube page hasn't fully loaded yet. Wait a moment and click the extension icon again."
  },
  NO_TRANSCRIPT: {
    title: "No captions available",
    desc: "This video doesn't have captions or auto-generated subtitles. NotionClip needs a transcript to analyse the video."
  },
  EXTRACTION_FAILED: {
    title: "Couldn't read video data",
    desc: "Something went wrong reading the YouTube page. Try refreshing the page and trying again."
  },
  TRANSCRIPT_FETCH_FAILED: {
    title: "Transcript fetch failed",
    desc: "YouTube returned an error when fetching captions. Refresh the YouTube page and try again."
  },
  NETWORK_ERROR: {
    title: "No internet connection",
    desc: "Check your internet connection and try again."
  },
  RATE_LIMITED: {
    title: "Too many requests",
    desc: "You've hit the usage limit. Wait a minute and try again."
  },
  BACKEND_ERROR: {
    title: "Server error",
    desc: "The NotionClip server returned an error. This is usually temporary — try again in 30 seconds."
  },
  NO_NOTION_TOKEN: {
    title: "Notion not connected",
    desc: "Open the NotionClip web app to connect your Notion workspace first, then come back here."
  },
  SAVE_FAILED: {
    title: "Save to Notion failed",
    desc: "Couldn't save to your Notion workspace. Check your connection and try again."
  },
  CONTENT_SCRIPT_ERROR: {
    title: "Extension not ready",
    desc: "Reload the YouTube tab (Ctrl+R) and try again. This happens on first install."
  },
  UNKNOWN: {
    title: "Something went wrong",
    desc: "An unexpected error occurred. See debug info below."
  }
};

async function sendMessageToTabWithInject(tabId, payload) {
  try {
    return await chrome.tabs.sendMessage(tabId, payload);
  } catch (err) {
    const message = String(err?.message || "");
    const missingReceiver = message.includes("Receiving end does not exist") || message.includes("Could not establish connection");

    if (!missingReceiver) {
      throw err;
    }

    // First-open and extension-update flows may leave old tabs without an
    // injected content script. Inject and retry once.
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content.js"],
    });

    return await chrome.tabs.sendMessage(tabId, payload);
  }
}

async function getVideoDataFromTab(tabId) {
  return sendMessageToTabWithInject(tabId, { type: "GET_VIDEO_DATA" });
}

async function resolveTargetTab() {
  // default_popup: active tab in current window IS the YouTube tab
  const currentWindowTabs = await chrome.tabs.query({
    active: true,
    currentWindow: true
  });
  const currentWindowTab = currentWindowTabs[0];
  if (currentWindowTab?.url?.includes("youtube.com/watch")) {
    return currentWindowTab;
  }

  // Fallback: find any YouTube watch tab across all windows
  const allYouTubeTabs = await chrome.tabs.query({
    url: "*://*.youtube.com/watch*"
  });
  if (allYouTubeTabs.length > 0) {
    return allYouTubeTabs[0];
  }

  return null;
}

// closeExtensionPanel removed — sidePanel mode removed, using default_popup


// ── State Machine ─────────────────────────────────────────────
function showState(state) {
  stateIdle.style.display    = state === "idle"    ? "block" : "none";
  stateLoading.style.display = state === "loading" ? "block" : "none";
  stateResult.style.display  = state === "result"  ? "block" : "none";
  stateError.style.display   = state === "error"   ? "block" : "none";
}

function showError(code, rawMessage = "") {
  const msg = ERROR_MESSAGES[code] || ERROR_MESSAGES.UNKNOWN;
  errorTitle.textContent = msg.title;
  errorDesc.textContent  = msg.desc;
  // Always show debug info during testing — helps you identify issues fast
  errorDebug.textContent = `Code: ${code}${rawMessage ? " — " + rawMessage : ""}`;
  stopLoadingText();
  showState("error");
  btnAnalyse.disabled = false;
}

function setLoadingMeta(text) {
  if (loadingMeta) loadingMeta.textContent = text;
}

function setLoadingSub(text) {
  if (loadingSub) loadingSub.textContent = text;
}

// ── Loading Text Rotation ─────────────────────────────────────
function startLoadingText() {
  setLoadingSub("This usually takes 8-20 seconds");
  setLoadingMeta("Fetching transcript from YouTube page...");

  const stages = [
    { text: "Fetching transcript...",  delay: 0    },
    { text: "Running AI analysis...",  delay: 2500 },
    { text: "Almost there...",         delay: 10000 },
  ];
  stages.forEach(stage => {
    const t = setTimeout(() => {
      if (loadingText) loadingText.textContent = stage.text;
    }, stage.delay);
    // store all timers so we can clear them
    if (!loadingTimer) loadingTimer = [];
    loadingTimer.push(t);
  });
}

function stopLoadingText() {
  if (loadingTimer) {
    loadingTimer.forEach(t => clearTimeout(t));
    loadingTimer = null;
  }
}


// ── Timestamp Helper ──────────────────────────────────────────
function getTimeAgo(timestamp) {
  const diffMs   = Date.now() - timestamp;
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1)  return "just now";
  if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? "s" : ""} ago`;
  const diffHrs = Math.floor(diffMins / 60);
  return `${diffHrs} hour${diffHrs > 1 ? "s" : ""} ago`;
}


// ── Populate Result State ─────────────────────────────────────
// ============================================================
// 🔴 BACKEND_MARKER_5 — RESPONSE FIELD NAMES
// Ask Copilot: "What exact field names does /analyze return?"
// Update the field names below to match your actual response.
// Current assumptions:
//   result.verdict   → "Watch" or "Skip" (exact string)
//   result.one_liner → one-sentence summary string
// If your backend uses different names (e.g. result.watch_skip,
// result.summary, result.brief) — change them here.
// ============================================================
function showResult(result, fromCache = false, cachedAt = null) {
  lastAnalysisResult = result;

  const verdict = result.verdict || result.what_youll_miss_if_skip || result.best_for || "";
  const verdictLower = verdict.toLowerCase();
  const isWatch = verdictLower.includes("watch");
  const isSkim = verdictLower.includes("skim");

  // Verdict badge styling
  verdictBadge.className = "verdict-badge " + (isWatch ? "watch" : "skip");
  verdictWord.textContent = isWatch ? "Watch" : (isSkim ? "Skim" : "Skip");
  verdictIconWatch.style.display = isWatch ? "block" : "none";
  verdictIconSkip.style.display = isWatch ? "none" : "block";

  // One-liner summary
  // 🔴 BACKEND_MARKER_5b: Update field name if different
  oneLiner.textContent = result.why || result.what_youll_miss_if_skip || result.best_for || "";

  // Cache row
  if (fromCache && cachedAt) {
    reanalyseRow.style.display = "flex";
    document.getElementById("cachedTime").textContent = getTimeAgo(cachedAt);
  } else {
    reanalyseRow.style.display = "none";
  }

  showState("result");
  btnAnalyse.disabled = false;
}


// ── Main Flow: On Popup Open ──────────────────────────────────
async function init() {
  showState("idle"); // default while we check

  let tab;
  try {
    tab = await resolveTargetTab();
  } catch (err) {
    showError("UNKNOWN", "Could not query active tab: " + err.message);
    return;
  }

  if (!tab?.url?.includes("youtube.com/watch")) {
    showError("NOT_YOUTUBE_VIDEO");
    return;
  }

  if (tab.status === "loading") {
    await new Promise(resolve => setTimeout(resolve, 2000));
  } else {
    // ytInitialData approach is synchronous — 1s is enough
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  currentTabId = tab.id;

  // Ask content script for video data
  let response;
  try {
    response = await getVideoDataFromTab(tab.id);
  } catch (err) {
    // Content script not injected (first install, or tab loaded before extension)
    showError("CONTENT_SCRIPT_ERROR", err.message);
    return;
  }

  if (!response) {
    showError("CONTENT_SCRIPT_ERROR", "No response from content script");
    return;
  }

  if (response.error) {
    showError(response.error, response.message);
    return;
  }

  // Success — populate video strip
  currentVideoData = response.data;
  elVideoTitle.textContent = currentVideoData.videoTitle || "YouTube Video";
  elVideoUrl.textContent   = currentVideoData.videoUrl || "";
  videoStrip.style.display = "block";

  // Check cache for this video
  const cacheKey = "analysis_" + currentVideoData.videoId;
  const cached   = await chrome.storage.local.get([cacheKey]);

  if (cached[cacheKey]) {
    const { result, timestamp } = cached[cacheKey];
    showResult(result, true, timestamp);
  } else {
    showState("idle");
  }
}


// ── Analyse Button Click ──────────────────────────────────────
btnAnalyse.addEventListener("click", async () => {
  if (!currentVideoData) {
    showError("UNKNOWN", "No video data available");
    return;
  }

  showState("loading");
  btnAnalyse.disabled = true;
  startLoadingText();

  const transcriptText = String(currentVideoData?.transcript || "").trim();
  if (!transcriptText) {
    stopLoadingText();
    showError("NO_TRANSCRIPT", "Transcript not ready — refresh the YouTube page");
    return;
  }

  setLoadingMeta("Transcript captured from your YouTube session");
  setLoadingSub("Running AI analysis on captured transcript...");

  // Step 2: Send to backend for analysis via background
  const analysisRes = await chrome.runtime.sendMessage({
    type: "ANALYZE_VIDEO",
    videoUrl: currentVideoData.videoUrl,
    transcript: transcriptText,
  });

  stopLoadingText();

  if (analysisRes.error) {
    showError(analysisRes.error, analysisRes.message);
    return;
  }

  // Cache the result
  const cacheKey = "analysis_" + currentVideoData.videoId;
  await chrome.storage.local.set({
    [cacheKey]: {
      result: analysisRes.result,
      timestamp: Date.now()
    }
  });

  showResult(analysisRes.result);
});


// ── Save to Notion Button Click ───────────────────────────────
btnSave.addEventListener("click", async () => {
  if (!lastAnalysisResult || !currentVideoData) return;

  // Loading state
  btnSave.className = "btn-save saving";
  btnSave.textContent = "Saving...";
  btnSave.disabled = true;

  const saveRes = await chrome.runtime.sendMessage({
    type: "SAVE_TO_NOTION",
    videoUrl: currentVideoData.videoUrl,
    analysis: lastAnalysisResult
  });

  if (saveRes.error === "NO_NOTION_TOKEN") {
    // Open web app so user can connect Notion
    chrome.tabs.create({ url: "https://notion-clips.vercel.app" });
    btnSave.className = "btn-save";
    btnSave.textContent = "Save to Notion";
    btnSave.disabled = false;
    return;
  }

  if (saveRes.error) {
    btnSave.className = "btn-save save-error";
    btnSave.textContent = "Save failed — try again";
    btnSave.disabled = false;
    // Reset after 3 seconds
    setTimeout(() => {
      btnSave.className = "btn-save";
      btnSave.textContent = "Save to Notion";
    }, 3000);
    return;
  }

  // Success
  btnSave.className = "btn-save saved";
  btnSave.textContent = "Saved to Notion";
  // Keep disabled — already saved
});


// ── Retry Button Click ────────────────────────────────────────
btnRetry.addEventListener("click", () => {
  showState("idle");
  init();
});


// ── Re-analyse Link Click ─────────────────────────────────────
reanalyseBtn.addEventListener("click", () => {
  // Clear cache for this video
  if (currentVideoData) {
    chrome.storage.local.remove("analysis_" + currentVideoData.videoId);
  }
  showState("idle");
});

// btnClosePanel removed — not needed in default_popup mode


// ── Boot ─────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", init);