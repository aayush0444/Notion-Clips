// Bridge auth/session tokens from the web app into extension storage.
(function () {
  const ALLOWED_ORIGINS = new Set([
    "https://notion-clips.vercel.app",
    "https://notionclip.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
  ]);

  function isAllowedOrigin(origin) {
    if (!origin || origin === "null") return false;
    if (ALLOWED_ORIGINS.has(origin)) return true;

    // Allow local dev ports while keeping origin scope limited to localhost loopback.
    return /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(origin);
  }

  window.addEventListener("message", (event) => {
    if (event.source !== window) return;
    if (!isAllowedOrigin(event.origin)) return;

    const data = event.data || {};
    if (data.type === "NOTIONCLIP_SYNC_AUTH") {
      chrome.runtime.sendMessage({
        type: "SYNC_AUTH_TOKENS",
        payload: data.payload || {},
      });
      return;
    }

    if (data.type === "NOTIONCLIP_CLEAR_AUTH") {
      chrome.runtime.sendMessage({ type: "CLEAR_AUTH_TOKENS" });
    }
  });
})();
