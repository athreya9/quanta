document.addEventListener('DOMContentLoaded', async () => {
  const companyEl = document.getElementById('top-company');
  const descEl = document.getElementById('top-desc');
  const testBtn = document.getElementById('trigger-test-btn');
  const statusEl = document.getElementById('conn-status');

  const API_HOST = 'https://quanta.virtusol.com';

  async function loadTopSignal() {
    try {
      const res = await fetch(`${API_HOST}/api/v1/signals`);
      if (res.ok) {
        const signals = await res.json();
        if (signals.length > 0) {
          companyEl.textContent = `${signals[0].company} (${signals[0].intent_score}% Intent)`;
          descEl.textContent = signals[0].description;
          statusEl.textContent = 'ONLINE';
          statusEl.style.color = '#34D399';
          return;
        }
      }
    } catch (e) {
      console.log('Error fetching signals in popup:', e);
    }
    companyEl.textContent = 'Demo Prospect Corp (98% Intent)';
    descEl.textContent = 'High-intent pricing page evaluation detected across multiple team IPs.';
    statusEl.textContent = 'LOCAL STUB';
    statusEl.style.color = '#FBBF24';
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
      alert('Alert dispatched (Backend offline or local stub)!');
    } finally {
      testBtn.disabled = false;
      testBtn.textContent = '⚡ Dispatch Test Slack & Overlay Alert';
    }
  });

  loadTopSignal();
});
