# 🚀 QUANTA Intent Engine — STEP 4 Chrome Extension Installation Guide

Welcome to the upgraded **QUANTA Real-Time Intent Signal Overlay** extension (STEP 4 Release)!

---

## 🌟 What's New in Step 4 Upgrade
1. **Real-Time Domain Matching**: Automatically matches the domain of the website you're visiting (`window.location.hostname`) against live QUANTA signals.
2. **High-Intent Glassmorphic Badges**:
   - **Matched Domain**: Displays company name, exact `intent_score` (e.g. `96% MATCH`), event category, description, and 1-click **Dispatch to CRM & Slack**.
   - **Unmatched Domain**: Displays `"No QUANTA signals detected for <domain> yet."` with a **Track Domain in QUANTA** button.
3. **CRM & Slack Engine Sync**: 1-click domain tracking directly ingests intent events into `quanta_crm.db` and dispatches live Slack alerts!
4. **Branded Product Branding**: Custom 3D gradient infinity loop icons (`icon16.png`, `icon48.png`, `icon128.png`).

---

## 📦 Step 1: Unzip the Extension Package
1. Double-click `quanta-extension.zip` in your macOS Downloads folder to extract it.
2. You will get a folder named `chrome-extension` containing:
   - `manifest.json` (with high-res icons)
   - `icon16.png`, `icon48.png`, `icon128.png`
   - `content.js` (Real domain matching logic) & `content.css`
   - `popup.html` & `popup.js`
   - `background.js`

---

## 🛠️ Step 2: Enable Developer Mode in Chrome
1. Open **Google Chrome** (or Brave / Edge / Arc).
2. Type `chrome://extensions` into your address bar and press **Enter**.
3. In the top-right corner of the Extensions page, toggle **Developer mode** to **ON**.

---

## ⚡ Step 3: Load the Unpacked Extension
1. Click **Load unpacked** (top-left).
2. Select the unzipped `chrome-extension` folder.
3. Click **Select** / **Open**.

---

## 🔥 Step 4: Test Domain Matching Live!
1. Visit **[stripe.com](https://stripe.com)** or **[apexfinancial.com](https://apexfinancial.com)**:
   - You will see the **⚡ QUANTA INTENT MATCH** overlay badge appear in the top-right corner showing actual matching signals (`96% MATCH`)!
2. Click **Dispatch to CRM & Slack** to verify CRM ingestion and Slack notifications!
3. Visit any unlisted domain (e.g. `example.com`):
   - You will see the non-intrusive fallback badge `"No QUANTA signals detected for example.com yet."` with **Track Domain in QUANTA**.

---

## 🛡️ Console & API Links
- **QUANTA Console**: [https://quanta.virtusol.com](https://quanta.virtusol.com)
- **Extension ZIP**: [https://quanta.virtusol.com/extension/quanta-extension.zip](https://quanta.virtusol.com/extension/quanta-extension.zip)
