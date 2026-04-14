// ============================================================
// page-world.js — NotionClip Chrome Extension
// ROLE: MAIN world. Polls window.ytInitialData until YouTube
// populates transcript segments, then extracts via regex.
//
// WHY POLLING: YouTube loads transcript data into ytInitialData
// asynchronously after page load via internal API calls.
// The confirmed working regex works — but only after YouTube
// has populated the data. We poll until it appears.
// ============================================================

(function () {
  let lastDispatchedDetail = null;
  let extractionInProgress = false;

  function dispatch(detail) {
    lastDispatchedDetail = detail;
    window.dispatchEvent(new CustomEvent('notionclip_data', { detail }));
  }

  function getVideoMeta() {
    const pr = window.ytInitialPlayerResponse;
    const urlParams = new URLSearchParams(window.location.search);
    const videoId = urlParams.get('v') || pr?.videoDetails?.videoId || null;
    const videoTitle = pr?.videoDetails?.title
      || document.title.replace(/\s*[-–]\s*YouTube\s*$/i, '').trim() || '';
    const videoUrl = window.location.href;
    return { videoId, videoTitle, videoUrl };
  }

  // ── The confirmed working extraction ──────────────────────
  // Regex confirmed in console: 81 segments, 9929 chars
  // Works on window.ytInitialData AFTER YouTube populates it
  function tryExtractTranscript() {
    try {
      const data = window.ytInitialData;
      if (!data) return null;

      const dataStr = JSON.stringify(data);

      // Check if transcript data is populated yet
      if (!dataStr.includes('TIMELINE_VIEW_STYLE')) return null;

      const matches = [
        ...dataStr.matchAll(/"simpleText":"([^"]+)","style":"TIMELINE_VIEW_STYLE/g)
      ];

      if (matches.length === 0) return null;

      const transcript = matches
        .map(m => m[1])
        .map(t => t
          .replace(/\\u([0-9a-fA-F]{4})/g, (_, c) =>
            String.fromCharCode(parseInt(c, 16)))
          .replace(/\\n/g, ' ')
          .replace(/\\"/g, '"')
          .replace(/\\\\/g, '\\')
          .trim()
        )
        .filter(Boolean)
        .join(' ')
        .replace(/\s+/g, ' ')
        .trim();

      return transcript.length > 50 ? transcript : null;
    } catch (e) {
      return null;
    }
  }

  // ── Poll until transcript appears or timeout ───────────────
  // YouTube typically populates transcript data within 2-5 seconds
  // We poll every 300ms for up to 15 seconds
  async function extractWithPolling(meta) {
    const maxAttempts = 50;   // 50 x 300ms = 15 seconds
    const interval = 300;

    for (let i = 0; i < maxAttempts; i++) {
      const transcript = tryExtractTranscript();

      if (transcript) {
        dispatch({ success: true, ...meta, transcript });
        return;
      }

      // Wait 300ms before next attempt
      await new Promise(r => setTimeout(r, interval));
    }

    // 15 seconds elapsed — transcript never appeared
    // Check if this video even has captions
    const pr = window.ytInitialPlayerResponse;
    const captionTracks = pr?.captions
      ?.playerCaptionsTracklistRenderer?.captionTracks;

    if (!captionTracks || captionTracks.length === 0) {
      dispatch({ error: 'NO_TRANSCRIPT', ...meta,
        message: 'No captions available for this video' });
    } else {
      dispatch({ error: 'NO_TRANSCRIPT', ...meta,
        message: 'Captions exist but transcript data did not load in 15s' });
    }
  }

  // ── Main entry point ───────────────────────────────────────
  function extractAndSend() {
    if (extractionInProgress) return;

    const meta = getVideoMeta();
    if (!meta.videoId) {
      dispatch({ error: 'PAGE_NOT_LOADED', message: 'No video ID found' });
      return;
    }

    // Try immediately first — may already be populated
    const immediate = tryExtractTranscript();
    if (immediate) {
      dispatch({ success: true, ...meta, transcript: immediate });
      return;
    }

    // Not ready yet — poll for it
    extractionInProgress = true;
    extractWithPolling(meta).finally(() => {
      extractionInProgress = false;
    });
  }

  // ── Run on load ────────────────────────────────────────────
  extractAndSend();

  // ── Handle YouTube SPA navigation ─────────────────────────
  window.addEventListener('yt-navigate-finish', () => {
    lastDispatchedDetail = null;
    extractionInProgress = false;
    setTimeout(extractAndSend, 500);
  });

  // ── Re-dispatch on demand from content.js ─────────────────
  window.addEventListener('notionclip_request_data', () => {
    if (lastDispatchedDetail && lastDispatchedDetail.success) {
      window.dispatchEvent(new CustomEvent('notionclip_data', {
        detail: lastDispatchedDetail
      }));
    } else if (!extractionInProgress) {
      extractAndSend();
    }
    // If extraction is in progress, it will dispatch when done
  });

})();