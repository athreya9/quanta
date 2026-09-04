// QUANTA Extension Background Worker
chrome.runtime.onInstalled.addListener(() => {
  console.log('[QUANTA Extension] Service Worker Installed');
  chrome.action.setBadgeText({ text: "" });
});

chrome.runtime.onStartup.addListener(() => {
  chrome.action.setBadgeText({ text: "" });
});
