// EUComply — Background Service Worker
// Manages extension badge: shows compliance score on the toolbar icon.

chrome.runtime.onInstalled.addListener(function() {
  // Reset badge on install
  chrome.action.setBadgeText({ text: '' });
  chrome.action.setBadgeBackgroundColor({ color: '#2868d0' });
});

// Listen for scan results from popup
chrome.storage.onChanged.addListener(function(changes, area) {
  if (area === 'local' && changes.lastScan) {
    var scan = changes.lastScan.newValue;
    if (scan && scan.score !== undefined) {
      // Set badge: show score number
      var label = String(scan.score);
      chrome.action.setBadgeText({ text: label });

      // Color based on score
      var color = scan.score >= 80 ? '#1a7a44' : (scan.score >= 50 ? '#b85a0a' : '#b03030');
      chrome.action.setBadgeBackgroundColor({ color: color });
    }
  }
});

// Optionally: clear badge when user navigates
// (too noisy to clear on every navigation, keep last scan visible)