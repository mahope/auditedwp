# EUComply Chrome Extension

One-click EU compliance scanning in your browser toolbar.

## Features

- Click the extension icon → auto-fills current tab's domain
- Calls the same free scanning API as eucomply.pages.dev
- Shows score + detailed results (HTTPS, cookies, forms, legal, headers)
- Badge icon shows the last scan score
- Links to Pro version for auditor-ready PDF reports

## How to install (unpacked)

1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode" (top-right toggle)
3. Click "Load unpacked"
4. Select this folder (`chrome-ext/` in the project root)
5. Pin the extension from the toolbar menu

## How to publish to Chrome Web Store

1. Create a Chrome Web Store developer account ($5 one-time fee, requires Mads)
2. Zip the contents of this folder (not the parent folder)
3. Upload to Chrome Web Store Dashboard
4. Fill in the store listing (description, screenshots, promo images)
5. Submit for review

### Store listing text (copy-ready)

**Title:** EUComply — Website Compliance Checker
**Short description:** Free one-click EU compliance scan. Check HTTPS, cookies, privacy links & more on any URL.
**Category:** Developer Tools
**Price:** Free + optional Pro upgrade via eucomplypro.com

## Local development

```bash
# Regenerate icons if needed
cd chrome-ext/icons && python3 generate-icons.py
# Then reload in chrome://extensions/
```

## Files

| File | Purpose |
|------|---------|
| `manifest.json` | Chrome Extension Manifest V3 |
| `popup.html` | Popup UI |
| `popup.js` | Popup logic (calls the scanning API) |
| `background.js` | Service worker for badge management |
| `icons/` | 16x16, 48x48, 128x128 PNG icons |
| `icons/generate-icons.py` | Script to regenerate icons |

## API

Uses the same public API as the website: `https://eucomply-scan.mahope-eeb.workers.dev/scan?url=<hostname>`