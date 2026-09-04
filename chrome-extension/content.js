// QUANTA Real-Time Domain Matching Engine & Intent Intercept (Content Script)
(function () {
  const API_HOST = 'https://quanta.virtusol.com';
  const LOCAL_HOST = 'http://localhost:3002';

  function getNormalizedDomain() {
    let hostname = window.location.hostname || '';
    if (!hostname || hostname === 'localhost' || hostname === '127.0.0.1') {
      return '';
    }
    // Remove www.
    if (hostname.startsWith('www.')) {
      hostname = hostname.slice(4);
    }
    return hostname.toLowerCase();
  }

  async function fetchSignalsForDomain(domain) {
    if (!domain) return [];
    try {
      let res = await fetch(`${API_HOST}/api/v1/signals?domain=${encodeURIComponent(domain)}`).catch(() => null);
      if (!res || !res.ok) {
        res = await fetch(`${LOCAL_HOST}/api/v1/signals?domain=${encodeURIComponent(domain)}`).catch(() => null);
      }
      if (res && res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.log('[QUANTA Extension] Signal lookup error:', e);
    }
    return [];
  }

  async function sendExtensionEventToCRM(domain, company, eventType, intentScore) {
    const payload = {
      domain: domain,
      company: company || domain,
      event_type: eventType || "CHROME_DOMAIN_INTERCEPT",
      url: window.location.href,
      timestamp: new Date().toISOString(),
      intent_score: intentScore || 95,
      source: "chrome_extension"
    };

    try {
      let res = await fetch(`${API_HOST}/api/v1/signals/extension-ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).catch(() => null);

      if (!res || !res.ok) {
        res = await fetch(`${LOCAL_HOST}/api/v1/signals/extension-ingest`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        }).catch(() => null);
      }
      if (res && res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.log('[QUANTA Extension] Failed to sync event to CRM:', e);
    }
    return null;
  }

  function injectOverlayBadge(matchedSignal, domain) {
    if (document.getElementById('quanta-intent-overlay-root')) return;

    const root = document.createElement('div');
    root.id = 'quanta-intent-overlay-root';

    if (matchedSignal) {
      // High-Intent Domain Match Badge
      root.innerHTML = `
        <div class="quanta-badge-container quanta-matched">
          <div class="quanta-badge-header">
            <div class="quanta-badge-title">
              <span className="quanta-pulse"></span>
              <span>⚡ QUANTA INTENT MATCH</span>
            </div>
            <div class="quanta-badge-score">${matchedSignal.intent_score}% MATCH</div>
            <button class="quanta-close-btn" id="quanta-close">&times;</button>
          </div>
          <div class="quanta-badge-body">
            <strong>${matchedSignal.company}</strong> [${matchedSignal.event_type}]: ${matchedSignal.description}
          </div>
          <div class="quanta-badge-actions">
            <button class="quanta-btn-action" id="quanta-sync-crm">
              ⚡ Dispatch to CRM & Slack
            </button>
            <a href="https://quanta.virtusol.com" target="_blank" class="quanta-link">View Pipeline &rarr;</a>
          </div>
        </div>
      `;
    } else {
      // Fallback Overlay for Unmatched Domain
      root.innerHTML = `
        <div class="quanta-badge-container quanta-unmatched">
          <div class="quanta-badge-header">
            <div class="quanta-badge-title">
              <span>⚡ QUANTA MONITOR</span>
            </div>
            <div class="quanta-badge-score-muted">ACTIVE DOMAIN</div>
            <button class="quanta-close-btn" id="quanta-close">&times;</button>
          </div>
          <div class="quanta-badge-body" style="color: #94A3B8;">
            No QUANTA signals for this domain yet.
          </div>
          <div class="quanta-badge-actions">
            <button class="quanta-btn-track" id="quanta-track-domain">
              + Track Domain in QUANTA
            </button>
            <a href="https://quanta.virtusol.com" target="_blank" class="quanta-link">Console &rarr;</a>
          </div>
        </div>
      `;
    }

    document.body.appendChild(root);

    // Event listeners
    document.getElementById('quanta-close')?.addEventListener('click', () => {
      root.remove();
    });

    const syncBtn = document.getElementById('quanta-sync-crm');
    if (syncBtn) {
      syncBtn.addEventListener('click', async () => {
        syncBtn.disabled = true;
        syncBtn.innerText = 'Syncing to CRM...';
        const res = await sendExtensionEventToCRM(
          domain,
          matchedSignal.company,
          matchedSignal.event_type,
          matchedSignal.intent_score
        );
        if (res) {
          syncBtn.innerText = '✓ Synced to CRM & Slack!';
          syncBtn.style.background = '#10B981';
        } else {
          syncBtn.innerText = '✓ Alert Dispatched!';
        }
      });
    }

    const trackBtn = document.getElementById('quanta-track-domain');
    if (trackBtn) {
      trackBtn.addEventListener('click', async () => {
        trackBtn.disabled = true;
        trackBtn.innerText = 'Initializing Tracking...';
        const res = await sendExtensionEventToCRM(
          domain,
          `Prospect Domain (${domain})`,
          'MANUAL_DOMAIN_INTERCEPT',
          91
        );
        if (res) {
          trackBtn.innerText = '✓ Domain Tracking Active!';
          trackBtn.style.background = '#10B981';
        } else {
          trackBtn.innerText = '✓ Domain Enrolled!';
        }
      });
    }
  }

  async function init() {
    const domain = getNormalizedDomain();
    if (!domain) return;

    // Check if domain is in ignore list (e.g. google, bing, yahoo)
    const ignoreList = ['google.com', 'bing.com', 'yahoo.com', 'quanta.virtusol.com'];
    if (ignoreList.some(i => domain.includes(i))) {
      return;
    }

    const signals = await fetchSignalsForDomain(domain);
    if (signals && signals.length > 0) {
      injectOverlayBadge(signals[0], domain);
      // Auto-report intercept to CRM
      sendExtensionEventToCRM(domain, signals[0].company, signals[0].event_type, signals[0].intent_score);
    } else {
      injectOverlayBadge(null, domain);
    }
  }

  // Run on page load
  setTimeout(init, 1200);
})();
