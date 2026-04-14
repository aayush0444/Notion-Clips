// diagnostic.js - Run this in YouTube page console to test extension manually

async function testExtension() {
  console.log('=== NotionClip Extension Diagnostic ===\n');
  
  // 1. Check if we're on YouTube
  console.log('1. URL Check:');
  console.log('   Current URL:', window.location.href);
  console.log('   Is YouTube video page?', window.location.href.includes('youtube.com/watch'));
  
  // 2. Check video ID
  const urlParams = new URLSearchParams(window.location.search);
  const videoId = urlParams.get('v');
  console.log('\n2. Video ID:');
  console.log('   Video ID:', videoId || 'NOT FOUND');
  
  // 3. Check page title
  console.log('\n3. Page Title:');
  console.log('   Document title:', document.title);
  console.log('   Cleaned:', document.title.replace(/ - YouTube$/, '').trim());
  
  // 4. Check video player in DOM
  console.log('\n4. Video Player:');
  const player1 = document.querySelector('#movie_player');
  const player2 = document.querySelector('.html5-video-player');
  const video = document.querySelector('video');
  console.log('   #movie_player:', player1 ? 'FOUND ✓' : 'NOT FOUND ✗');
  console.log('   .html5-video-player:', player2 ? 'FOUND ✓' : 'NOT FOUND ✗');
  console.log('   <video> tag:', video ? 'FOUND ✓' : 'NOT FOUND ✗');
  
  // 5. Check for ytInitialPlayerResponse
  console.log('\n5. YouTube Data Objects:');
  console.log('   window.ytInitialPlayerResponse:', window.ytInitialPlayerResponse ? 'EXISTS ✓' : 'MISSING ✗');
  console.log('   window.ytplayer:', window.ytplayer ? 'EXISTS ✓' : 'MISSING ✗');
  console.log('   window.ytInitialData:', window.ytInitialData ? 'EXISTS ✓' : 'MISSING ✗');
  
  // 6. Try to find player response in script tags
  console.log('\n6. Script Tag Search:');
  const scripts = document.querySelectorAll('script');
  let foundInScript = false;
  for (const script of scripts) {
    const content = script.textContent || '';
    if (content.includes('ytInitialPlayerResponse')) {
      console.log('   Found ytInitialPlayerResponse in script tag ✓');
      const match = content.match(/ytInitialPlayerResponse\s*=\s*(\{.+?\});/s);
      if (match) {
        try {
          const data = JSON.parse(match[1]);
          console.log('   Parsed successfully ✓');
          console.log('   Has captions?', data.captions ? 'YES ✓' : 'NO ✗');
          if (data.captions) {
            const tracks = data.captions.playerCaptionsTracklistRenderer?.captionTracks;
            console.log('   Caption tracks:', tracks ? tracks.length : 0);
            if (tracks && tracks.length > 0) {
              console.log('   First track:', tracks[0].languageCode || tracks[0].vssId);
              console.log('   Has baseUrl?', tracks[0].baseUrl ? 'YES ✓' : 'NO ✗');
            }
          }
          foundInScript = true;
        } catch (e) {
          console.log('   Parse failed ✗:', e.message);
        }
      }
      break;
    }
  }
  if (!foundInScript) {
    console.log('   ytInitialPlayerResponse NOT found in any script tag ✗');
  }
  
  // 7. Try manual caption URL construction
  console.log('\n7. Fallback Caption URL:');
  if (videoId) {
    const fallbackUrl = `https://www.youtube.com/api/timedtext?v=${videoId}&lang=en&fmt=srv3`;
    console.log('   Constructed URL:', fallbackUrl);
    
    // Try to fetch it
    try {
      const response = await fetch(fallbackUrl);
      if (response.ok) {
        const text = await response.text();
        console.log('   Fetch result: SUCCESS ✓');
        console.log('   Response length:', text.length, 'bytes');
        console.log('   First 100 chars:', text.substring(0, 100));
      } else {
        console.log('   Fetch result: FAILED ✗ Status:', response.status);
      }
    } catch (error) {
      console.log('   Fetch result: ERROR ✗', error.message);
    }
  }
  
  // 8. Check if extension is loaded
  console.log('\n8. Extension Status:');
  console.log('   window.__notionclip:', window.__notionclip ? 'EXISTS ✓' : 'NOT SET ✗');
  if (window.__notionclip) {
    console.log('   Data:', window.__notionclip);
  }
  
  // 9. Test message to extension
  console.log('\n9. Extension Communication Test:');
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    console.log('   ERROR: This should be run in the page console, not extension console!');
  } catch (e) {
    console.log('   Running in page context ✓ (this is correct)');
  }
  
  console.log('\n=== Diagnostic Complete ===');
  console.log('\nNext steps:');
  console.log('1. Check if video player exists (should be ✓)');
  console.log('2. Check if captions were found (should be ✓)');
  console.log('3. If all ✓, check extension console for errors');
  console.log('4. Make sure extension is reloaded: chrome://extensions/');
}

// Run the test
testExtension();
