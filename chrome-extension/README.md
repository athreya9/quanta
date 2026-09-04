# QUANTA Intent Signal Overlay — Chrome Extension

A minimal Manifest V3 Chrome Extension overlay stub for **QUANTA – Real-Time Intent Signal Engine**.

## Features
- **Live Signal Stream Integration**: Connects to `https://quanta.virtusol.com/api/v1/signals`.
- **Domain Overlay Badge**: Injects a high-tech glassmorphic badge showing active intent scores when inspecting target domains.
- **Alert Dispatcher**: Trigger instant test alerts directly from the extension popup window to Slack (`SLACK_WEBHOOK_URL`).

## Installation Instructions (Chrome / Edge / Brave)
1. Open Google Chrome and navigate to `chrome://extensions`.
2. Enable **Developer mode** using the toggle switch in the top-right corner.
3. Click **Load unpacked**.
4. Select the `/chrome-extension` directory inside the QUANTA repository.
5. The **QUANTA Intent Engine** extension will now be active in your browser toolbar with a `98%` badge icon.
