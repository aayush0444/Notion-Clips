// ============================================================
// content.js — NotionClip Chrome Extension
// ROLE: Isolated world bridge between page-world.js and popup.
// Listens for notionclip_data events from page-world.js (MAIN world)
// and responds to GET_VIDEO_DATA messages from popup.js.
// ============================================================

(function () {
  let cachedData = null;

  // ── Listen for data from page-world.js ────────────────────
  // page-world.js dispatches CustomEvents on window.
  // Isolated world content scripts CAN receive these events.
  window.addEventListener('notionclip_data', (event) => {
    cachedData = event.detail;
  });

  // ── Ask page-world.js to send its data immediately ────────
  // This handles the case where page-world.js already ran
  // before content.js attached the listener above.
  window.dispatchEvent(new CustomEvent('notionclip_request_data'));

  // ── Respond to popup requests ──────────────────────────────
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type !== 'GET_VIDEO_DATA') return;

    // Validate we're on a YouTube watch page
    const url = window.location.href;
    if (!url.includes('youtube.com/watch')) {
      sendResponse({ error: 'NOT_YOUTUBE_VIDEO' });
      return true;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const videoId = urlParams.get('v');
    if (!videoId) {
      sendResponse({ error: 'NOT_YOUTUBE_VIDEO' });
      return true;
    }

    // If we already have data cached, return it immediately
    if (cachedData) {
      if (cachedData.error) {
        sendResponse({ error: cachedData.error, message: cachedData.message });
      } else {
        sendResponse({
          success: true,
          data: {
            videoId: cachedData.videoId,
            videoTitle: cachedData.videoTitle,
            videoUrl: cachedData.videoUrl,
            transcript: cachedData.transcript,
          }
        });
      }
      return true;
    }

    // No data yet — ask page-world.js to run extraction
    window.dispatchEvent(new CustomEvent('notionclip_request_data'));

    // Poll until data arrives or timeout
    // 20 attempts x 500ms = 10 seconds max
    // ytInitialData approach is synchronous so should be fast
    let attempts = 0;
    const maxAttempts = 30;

    const poll = setInterval(() => {
      attempts++;

      if (cachedData) {
        clearInterval(poll);
        if (cachedData.error) {
          sendResponse({ error: cachedData.error, message: cachedData.message });
        } else {
          sendResponse({
            success: true,
            data: {
              videoId: cachedData.videoId,
              videoTitle: cachedData.videoTitle,
              videoUrl: cachedData.videoUrl,
              transcript: cachedData.transcript,
            }
          });
        }
        return;
      }

      // Every 5 attempts, ask page-world.js again
      if (attempts % 5 === 0) {
        window.dispatchEvent(new CustomEvent('notionclip_request_data'));
      }

      if (attempts >= maxAttempts) {
        clearInterval(poll);
        sendResponse({
          error: 'PAGE_NOT_LOADED',
          message: 'Transcript not ready after 10s. Hard refresh YouTube tab (Ctrl+Shift+R) and try again.'
        });
      }
    }, 500);

    return true; // Keep message channel open for async response
  });

})();