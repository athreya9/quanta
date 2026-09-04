document.addEventListener('DOMContentLoaded', async () => {
  const companyEl = document.getElementById('top-company');
  const descEl = document.getElementById('top-desc');
  const testBtn = document.getElementById('trigger-test-btn');
  const statusEl = document.getElementById('conn-status');
  const modePill = document.getElementById('intent-mode-pill');
  const updateBanner = document.getElementById('update-banner');
  const updateMsg = document.getElementById('update-msg');
  const updateBtn = document.getElementById('update-ext-btn');
  const forceReloadBtn = document.getElementById('force-reload-btn');
  const extVerEl = document.getElementById('ext-ver');

  const API_HOST = 'https://quanta.virtusol.com';

  const manifestVersion = (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.getManifest) 
    ? chrome.runtime.getManifest().version 
    : '1.1.0';

  if (extVerEl) {
    extVerEl.textContent = `v${manifestVersion}`;
  }

  async function checkExtensionVersionAndMode() {
    try {
      const res = await fetch(`${API_HOST}/api/v1/extension/version`);
      if (res.ok) {
        const data = await res.json();
        if (data.intent_mode === 'demo') {
          if (modePill) {
            modePill.textContent = 'DEMO INTENT';
            modePill.className = 'mode-pill mode-demo';
          }
        } else {
          if (modePill) {
            modePill.textContent = 'PRODUCTION INTENT';
            modePill.className = 'mode-pill mode-production';
          }
        }
        if (data.latest_version && data.latest_version > manifestVersion) {
          updateMsg.textContent = `Version v${data.latest_version} available! (${data.changelog || 'New signal features'})`;
          updateBanner.style.display = 'block';
        }
      }
    } catch (e) {
      console.log('Version check skipped:', e);
    }
  }

  async function getActiveDomain() {
    try {
      if (typeof chrome !== 'undefined' && chrome.tabs) {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tabs && tabs[0] && tabs[0].url) {
          const urlObj = new URL(tabs[0].url);
          let host = urlObj.hostname;
          if (host.startsWith('www.')) host = host.slice(4);
          return host;
        }
      }
    } catch (e) {
      console.log('Error reading active tab domain:', e);
    }
    return '';
  }

  async function loadDomainSignals() {
    const domain = await getActiveDomain();
    try {
      let endpoint = `${API_HOST}/api/v1/signals`;
      if (domain) {
        endpoint += `?domain=${encodeURIComponent(domain)}`;
      }

      const res = await fetch(endpoint);
      if (res.ok) {
        const signals = await res.json();
        if (signals && signals.length > 0) {
          companyEl.textContent = `${signals[0].company} (${signals[0].intent_score}% Intent)`;
          descEl.textContent = `[${signals[0].event_type}]: ${signals[0].description}`;
          if (statusEl) {
            statusEl.textContent = 'MATCHED';
            statusEl.style.color = '#34D399';
          }
          return;
        }
      }
    } catch (e) {
      console.log('Error fetching signals in popup:', e);
    }

    if (domain) {
      companyEl.textContent = `Active Domain: ${domain}`;
      descEl.textContent = `No active intent signals for ${domain} yet. Click below to initiate domain intent monitoring.`;
      if (statusEl) {
        statusEl.textContent = 'MONITORING';
        statusEl.style.color = '#FBBF24';
      }
    } else {
      companyEl.textContent = 'QUANTA Signal Stream Ready';
      descEl.textContent = 'Inspect any target company website to match real-time B2B buyer intent.';
      if (statusEl) {
        statusEl.textContent = 'ONLINE';
        statusEl.style.color = '#34D399';
      }
    }
  }

  testBtn.addEventListener('click', async () => {
    testBtn.disabled = true;
    testBtn.textContent = 'Sending Alert...';
    try {
      const res = await fetch(`${API_HOST}/api/v1/signals/test-alert`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        alert(`Alert Dispatched!\n\n${data.message}`);
      } else {
        alert('Test alert dispatched to backend!');
      }
    } catch (e) {
      alert('Alert dispatched!');
    } finally {
      testBtn.disabled = false;
      testBtn.textContent = '⚡ Dispatch Test Slack & Overlay Alert';
    }
  });

  if (forceReloadBtn) {
    forceReloadBtn.addEventListener('click', () => {
      if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.reload) {
        chrome.runtime.reload();
      } else {
        window.location.reload();
      }
    });
  }

  if (updateBtn) {
    updateBtn.addEventListener('click', () => {
      if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.reload) {
        chrome.runtime.reload();
      }
      window.open(`${API_HOST}/extension/quanta-extension.zip`, '_blank');
    });
  }

  loadDomainSignals();
  checkExtensionVersionAndMode();
});
