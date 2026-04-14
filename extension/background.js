// ============================================================
// background.js — NotionClip Chrome Extension
// ROLE: Service worker. Handles all network/API calls.
// popup.js communicates with this via chrome.runtime.sendMessage.
// ============================================================

// ── Backend URL configuration ─────────────────────────────
// Reads from host_permissions in manifest to avoid hardcoding.
// Can be overridden via chrome.storage.local.set({api_base_url: "..."})

const API_CONFIG_KEY = "api_base_url";

function trimSlash(value) {
  return String(value || "").replace(/\/+$/, "");
}

function deriveApiBaseUrlFromManifest() {
  const hostPermissions = chrome.runtime.getManifest().host_permissions || [];
  const candidates = hostPermissions
    .filter(p => !p.includes("youtube.com") && p.startsWith("*://"))
    .map(p => trimSlash(p.replace("*://", "https://").replace(/\/\*$/, "")));

  if (!candidates.length) return "";
  const renderCandidate = candidates.find(u => u.includes("onrender.com"));
  if (renderCandidate) return renderCandidate;
  return candidates[0];
}

async function getApiBaseUrl() {
  const stored = await chrome.storage.local.get([API_CONFIG_KEY]);
  const configured = typeof stored[API_CONFIG_KEY] === "string"
    ? trimSlash(stored[API_CONFIG_KEY]) : "";
  const resolved = configured || deriveApiBaseUrlFromManifest();
  if (!resolved) {
    throw new Error("Backend URL not configured. Check host_permissions in manifest.");
  }
  return resolved;
}


// ── Message Router ────────────────────────────────────────
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

  if (message.type === "ANALYZE_VIDEO") {
    handleAnalyzeVideo(message.videoUrl, message.transcript)
      .then(result => sendResponse(result))
      .catch(err => sendResponse({ error: "NETWORK_ERROR", message: err.message }));
    return true;
  }

  if (message.type === "SAVE_TO_NOTION") {
    handleSaveToNotion(message.videoUrl, message.analysis)
      .then(result => sendResponse(result))
      .catch(err => sendResponse({ error: "SAVE_FAILED", message: err.message }));
    return true;
  }

  if (message.type === "SYNC_AUTH_TOKENS") {
    handleSyncAuthTokens(message.payload)
      .then(result => sendResponse(result))
      .catch(err => sendResponse({ error: "SYNC_FAILED", message: err.message }));
    return true;
  }

  if (message.type === "CLEAR_AUTH_TOKENS") {
    chrome.storage.local.remove(["access_token", "user_id", "notion_token"])
      .then(() => sendResponse({ success: true }))
      .catch(err => sendResponse({ error: "CLEAR_FAILED", message: err.message }));
    return true;
  }

});


// ── AI Analysis ───────────────────────────────────────────
// Sends YouTube URL + transcript to backend /verdict endpoint.
// Backend performs AI analysis and returns verdict + summary.
async function handleAnalyzeVideo(videoUrl, transcript) {
  try {
    const apiBaseUrl = await getApiBaseUrl();

    const resolvedTranscript = String(transcript || "").trim();
    if (!resolvedTranscript) {
      return { error: "NO_TRANSCRIPT", message: "Transcript is empty" };
    }

    const response = await fetch(`${apiBaseUrl}/verdict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: videoUrl,
        transcript: resolvedTranscript,
        mode: "quick",
      }),
    });

    if (response.status === 429) {
      return { error: "RATE_LIMITED", message: "Too many requests. Wait a minute." };
    }
    if (response.status === 500) {
      const text = await response.text();
      return { error: "BACKEND_ERROR", message: text.slice(0, 200) };
    }
    if (!response.ok) {
      return { error: "BACKEND_ERROR", message: `HTTP ${response.status}` };
    }

    const result = await response.json();
    return { success: true, result };

  } catch (err) {
    return { error: "NETWORK_ERROR", message: err.message };
  }
}


// ── Save to Notion ────────────────────────────────────────
// Sends analysis result to backend /push endpoint.
// Requires notion_token stored in chrome.storage.local.
async function handleSaveToNotion(videoUrl, analysis) {
  try {
    const apiBaseUrl = await getApiBaseUrl();
    const stored = await chrome.storage.local.get(["notion_token"]);

    if (!stored.notion_token) {
      return { error: "NO_NOTION_TOKEN",
        message: "Connect Notion in the web app first" };
    }

    const response = await fetch(`${apiBaseUrl}/push`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        video_url: videoUrl,
        mode: "quick",
        insights: {
          title: analysis.title || "YouTube Video",
          summary: analysis.why || analysis.summary || "",
          key_takeaways: analysis.key_takeaways || [],
          topics_covered: analysis.topics_covered || [],
          action_items: analysis.action_items || [],
        },
        notion_token: stored.notion_token,
      }),
    });

    if (!response.ok) {
      const text = await response.text();
      return { error: "SAVE_FAILED", message: text.slice(0, 200) };
    }

    return { success: true };

  } catch (err) {
    return { error: "SAVE_FAILED", message: err.message };
  }
}


// ── Auth Token Sync ───────────────────────────────────────
// Called by web_bridge.js when user logs into the web app.
// Stores tokens so extension can use them for Notion saves.
async function handleSyncAuthTokens(payload) {
  const accessToken = typeof payload?.access_token === "string"
    ? payload.access_token : "";
  const userId = typeof payload?.user_id === "string"
    ? payload.user_id : "";
  const notionToken = typeof payload?.notion_token === "string"
    ? payload.notion_token : "";

  if (!accessToken || !userId) {
    return { error: "SYNC_INVALID", message: "Missing access_token or user_id" };
  }

  await chrome.storage.local.set({
    access_token: accessToken,
    user_id: userId,
    notion_token: notionToken,
  });

  return { success: true };
}