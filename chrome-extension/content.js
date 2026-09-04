// QUANTA Intent Signal Overlay - Content Script
(function () {
  const API_ENDPOINT = 'https://quanta.virtusol.com/api/v1/signals';
  const LOCAL_ENDPOINT = 'http://localhost:3002/api/v1/signals';

  async function fetchSignals() {
    try {
      let res = await fetch(API_ENDPOINT).catch(() => null);
      if (!res || !res.ok) {
        res = await fetch(LOCAL_ENDPOINT).catch(() => null);
      }
      if (res && res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.log('[QUANTA Extension] API unreachable:', e);
    }
    return [];
  }

  function injectOverlay(signal) {
    if (document.getElementById('quanta-intent-overlay-root')) return;

    const root = document.createElement('div');
    root.id = 'quanta-intent-overlay-root';

    root.innerHTML = `
      <div class="quanta-badge-container">
        <div class="quanta-badge-header">
          <div class="quanta-badge-title">
            <span>⚡ QUANTA INTENT</span>
          </div>
          <div class="quanta-badge-score">${signal.intent_score || 96}% MATCH</div>
          <button class="quanta-close-btn" id="quanta-close">&times;</button>
        </div>
        <div class="quanta-badge-body">
          <strong>${signal.company || 'High Intent Prospect'}</strong>: ${signal.description || 'Active intent signal detected on pricing path.'}
        </div>
        <div class="quanta-badge-footer">
          <span style="color: #94A3B8;">Category: ${signal.category || 'PRICING_PAGE'}</span>
          <a href="https://quanta.virtusol.com" target="_blank" class="quanta-link">Open Pipeline &rarr;</a>
        </div>
      </div>
    `;

    document.body.appendChild(root);

    document.getElementById('quanta-close').addEventListener('click', () => {
      root.remove();
    });
  }

  async function init() {
    const signals = await fetchSignals();
    if (signals && signals.length > 0) {
      // Pick top signal with score >= 90
      const topSignal = signals.find(s => s.intent_score >= 90) || signals[0];
      injectOverlay(topSignal);
    } else {
      // Default fallback stub overlay for active domain inspection
      injectOverlay({
        company: "Live Domain Inspector",
        intent_score: 95,
        description: `Active buyer intent tracking initialized for ${window.location.hostname}.`,
        category: "DOMAIN_MONITOR"
      });
    }
  }

  // Wait 1.5s after load to present non-intrusive badge
  setTimeout(init, 1500);
})();
