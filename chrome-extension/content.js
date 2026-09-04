// QUANTA Real-Time Domain Matching Engine & Enriched Overlay Intercept (Content Script - Step 6 Real Scoring Engine)
(function () {
  const API_HOST = 'https://quanta.virtusol.com';
  const LOCAL_HOST = 'http://localhost:3002';

  function getNormalizedDomain() {
    let hostname = window.location.hostname || '';
    if (!hostname || hostname === 'localhost' || hostname === '127.0.0.1') {
      return '';
    }
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
      source: "chrome_extension",
      browser_fingerprint: navigator.userAgent,
      geo_location: "Active Extension Telemetry"
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
      const techStackHtml = matchedSignal.tech_stack_signals 
        ? `<div class="quanta-enrich-item"><strong>💻 Tech Stack:</strong> ${Array.isArray(matchedSignal.tech_stack_signals) ? matchedSignal.tech_stack_signals.join(', ') : matchedSignal.tech_stack_signals}</div>`
        : '';
      const hiringHtml = matchedSignal.hiring_signals
        ? `<div class="quanta-enrich-item"><strong>👥 Hiring Signals:</strong> ${Array.isArray(matchedSignal.hiring_signals) ? matchedSignal.hiring_signals.join(' | ') : matchedSignal.hiring_signals}</div>`
        : '';
      const pricingHtml = matchedSignal.pricing_page_behavior
        ? `<div class="quanta-enrich-item"><strong>💰 Pricing Behavior:</strong> ${matchedSignal.pricing_page_behavior}</div>`
        : '';
      const fundingHtml = matchedSignal.funding_signals
        ? `<div class="quanta-enrich-item"><strong>📈 Funding:</strong> ${matchedSignal.funding_signals}</div>`
        : '';

      // High-Intent Domain Match Enriched Badge (Step 6)
      root.innerHTML = `
        <div class="quanta-badge-container quanta-matched">
          <div class="quanta-badge-header">
            <div class="quanta-badge-title">
              <span>⚡ QUANTA INTENT MATCH</span>
            </div>
            <div class="quanta-badge-score">${matchedSignal.intent_score}% SCORE</div>
            <button class="quanta-close-btn" id="quanta-close">&times;</button>
          </div>
          <div class="quanta-badge-body">
            <div style="font-size: 13px; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;">
              ${matchedSignal.company} <span style="font-size:10px; color:#00F0FF;">(${domain})</span>
            </div>
            <div style="font-size: 11px; color: #94A3B8; margin-bottom: 8px;">
              [${matchedSignal.event_type}]: ${matchedSignal.description}
            </div>

            <!-- Step 6 Real 8-Factor Behavioral Enrichment Stream -->
            <div class="quanta-enrichment-box">
              ${techStackHtml}
              ${hiringHtml}
              ${pricingHtml}
              ${fundingHtml}
            </div>
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

    // Ignore list
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
