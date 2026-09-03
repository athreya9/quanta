import React, { useEffect } from 'react';

/**
 * Lightweight Analytics Attribution Tracker
 * Supports Plausible or Matomo script injection for lead source & UTM attribution.
 */
export default function AnalyticsTracker() {
  useEffect(() => {
    // Capture UTM parameters from URL
    const urlParams = new URLSearchParams(window.location.search);
    const utmSource = urlParams.get('utm_source');
    const utmMedium = urlParams.get('utm_medium');
    const utmCampaign = urlParams.get('utm_campaign');

    if (utmSource || utmMedium) {
      sessionStorage.setItem('quanta_utm', JSON.stringify({ utmSource, utmMedium, utmCampaign }));
    }
  }, []);

  return null;
}
