// QUANTA Step 7: Silent Autonomous Intent Engine + LinkedIn Job Post Detector
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

  function detectJobPostSignal() {
    const url = window.location.href.toLowerCase();
    const host = window.location.hostname.toLowerCase();

    if (host.includes('linkedin.com') && (url.includes('/jobs') || url.includes('/view/'))) {
      return { isJob: true, source: 'LinkedIn Job Post', role: document.title || 'Outbound Sales Specialist' };
    }
    if (host.includes('greenhouse.io') || host.includes('indeed.com') || host.includes('lever.co') || url.includes('/careers')) {
      return { isJob: true, source: 'Greenhouse/Indeed Job Post', role: document.title || 'Growth Lead' };
    }
    return { isJob: false };
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

  async function autoIngestSilentTelemetry(domain, eventType, intentScore, extraData = {}) {
    const payload = {
      domain: domain,
      company: extraData.company || fDomainCompany(domain),
      event_type: eventType,
      url: window.location.href,
      timestamp: new Date().toISOString(),
      intent_score: intentScore,
      source: "chrome_extension",
      browser_fingerprint: navigator.userAgent,
      geo_location: "Autonomous Telemetry"
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
      console.log('[QUANTA Extension] Silent ingest skipped:', e);
    }
    return null;
  }

  function fDomainCompany(domain) {
    if (!domain) return "Target Domain";
    const parts = domain.split('.');
    return parts[0].charAt(0).toUpperCase() + parts[0].slice(1) + " Corp";
  }

  function injectHighIntentOverlayBadge(matchedSignal, domain) {
    if (document.getElementById('quanta-intent-overlay-root')) return;

    const root = document.createElement('div');
    root.id = 'quanta-intent-overlay-root';

    const techStackHtml = matchedSignal.tech_stack_signals 
      ? `<div class="quanta-enrich-item"><strong>💻 Tech Stack:</strong> ${Array.isArray(matchedSignal.tech_stack_signals) ? matchedSignal.tech_stack_signals.join(', ') : matchedSignal.tech_stack_signals}</div>`
      : '';
    const hiringHtml = matchedSignal.hiring_signals
      ? `<div class="quanta-enrich-item"><strong>👥 Hiring Signals:</strong> ${Array.isArray(matchedSignal.hiring_signals) ? matchedSignal.hiring_signals.join(' | ') : matchedSignal.hiring_signals}</div>`
      : '';

    // Step 7 Autonomous High Intent Badge (Only shown when intent >= 85)
    root.innerHTML = `
      <div class="quanta-badge-container quanta-matched">
        <div class="quanta-badge-header">
          <div class="quanta-badge-title">
            <span>⚡ QUANTA AUTONOMOUS INTENT</span>
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

          <div class="quanta-enrichment-box">
            ${techStackHtml}
            ${hiringHtml}
          </div>
        </div>
        <div class="quanta-badge-actions">
          <a href="https://quanta.virtusol.com" target="_blank" class="quanta-link" style="font-weight:700;">Open QUANTA Pipeline &rarr;</a>
        </div>
      </div>
    `;

    document.body.appendChild(root);

    document.getElementById('quanta-close')?.addEventListener('click', () => {
      root.remove();
    });
  }

  async function initAutonomousStream() {
    const domain = getNormalizedDomain();
    if (!domain) return;

    // Ignore list
    const ignoreList = ['google.com', 'bing.com', 'yahoo.com', 'quanta.virtusol.com'];
    if (ignoreList.some(i => domain.includes(i))) {
      return;
    }

    // 1. Check for LinkedIn / Greenhouse Job Post Signal
    const jobCheck = detectJobPostSignal();
    if (jobCheck.isJob) {
      await autoIngestSilentTelemetry(domain, "JOB_POST_INTERCEPT", 92, {
        company: fDomainCompany(domain)
      });
    } else {
      // Auto-ingest silent telemetry for domain visit
      await autoIngestSilentTelemetry(domain, "AUTONOMOUS_DOMAIN_INTERCEPT", 88);
    }

    // 2. Fetch matched signals from QUANTA
    const signals = await fetchSignalsForDomain(domain);
    if (signals && signals.length > 0 && signals[0].intent_score >= 85) {
      // Render overlay ONLY if real high intent score >= 85
      injectHighIntentOverlayBadge(signals[0], domain);
    }
  }

  // Execute silent autonomous stream after load
  setTimeout(initAutonomousStream, 1500);
})();
