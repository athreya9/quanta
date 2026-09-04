// QUANTA Extension Background Worker
chrome.runtime.onInstalled.addListener(() => {
  console.log('[QUANTA Extension] Service Worker Installed');
  chrome.action.setBadgeText({ text: "98%" });
  chrome.action.setBadgeBackgroundColor({ color: "#00F0FF" });
});

chrome.runtime.onStartup.addListener(() => {
  chrome.action.setBadgeText({ text: "98%" });
});
