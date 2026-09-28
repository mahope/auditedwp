# EUComply Chrome Extension

One-click EU compliance scanning in your browser toolbar.

## Features

- Click the extension icon → auto-fills current tab's domain
- Calls the same free scanning API as eucomplypro.com
- Shows score + detailed results for nine technical URL signals
- Badge icon shows the last scan score
- Links to the current WordPress Pro document tools

## How to install (unpacked)

1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode" (top-right toggle)
3. Click "Load unpacked"
4. Select this folder (`chrome-ext/` in the project root)
5. Pin the extension from the toolbar menu

## How to publish to Chrome Web Store

Nobody can do this from the repo — it needs a Chrome Web Store developer
account ($5 one-time fee) and the OAuth credentials behind it. Everything the
upload needs is already measured by `tools/check_store_ready.py`; run it
before you upload:

```bash
python3 tools/check_store_ready.py          # the gate that must be green
python3 tools/check_store_ready.py --selftest
```

The gate measures the manifest against the store's own limits (name ≤45,
description ≤132, icons 16/48/128 as real PNGs, no local URLs), proves every
declared permission is actually used, checks that `host_permissions` and the
API the popup calls are the same origin, and that the published
`/extension/` page links exactly one paid path.

1. Create a Chrome Web Store developer account (needs Mads)
2. Rebuild the published package first — do not zip this folder by hand:

   ```bash
   python3 tools/build_extension_zip.py --write
   ```

   It builds `site/assets/eucomply-extension-<version>.zip` from this folder
   with sorted members and fixed timestamps, so the archive is reproducible and
   `--check` can fail if the committed one drifts. The version in `manifest.json`
   is the file name, so the archive, the download link and the store listing
   cannot disagree.
3. Upload `site/assets/eucomply-extension-<version>.zip` to the Chrome Web Store Dashboard
4. Fill in the store listing below, plus **at least one screenshot**
   (1280×800 or 640×400) — that screenshot is the one asset still missing
5. Declare the data usage: the extension sends the scanned URL to the API and
   nothing else, and the privacy policy is at https://eucomplypro.com/privacy/

### Store listing text (copy-ready)

**Title:** EUComply — Website Compliance Checker
**Short description:** Free one-click EU compliance scan. Check HTTPS, cookies, privacy links & more on any URL.
**Category:** Developer Tools
**Price:** Free + optional Pro upgrade via eucomplypro.com

## Local development

```bash
# Reload the unpacked extension at chrome://extensions/ after every change.
# The icons are committed as PNG; regenerate them only if the mark changes,
# and keep them at 16x16, 48x48 and 128x128 — the store gate reads the
# dimensions out of the PNG header and fails on a wrong size.
```

## Files

| File | Purpose |
|------|---------|
| `manifest.json` | Chrome Extension Manifest V3 |
| `popup.html` | Popup UI |
| `popup.js` | Popup logic (calls the scanning API) |
| `background.js` | Service worker for badge management |
| `icons/` | 16x16, 48x48, 128x128 PNG icons |
| `LICENSE` | MIT — the terms the extension is actually offered under |

## License

MIT, the same terms as the scanner and the CLI. The full text is in
`LICENSE` in this folder **and** inside the published ZIP, because a ZIP is
what a reader downloads — a license that only lives in the repository is not
a license the person holding the archive has seen.

`/extension/` says "MIT licensed", not "open source", because "open source" is
a legal term of art and a promise; a name for the license is a fact you can
check. `tools/check_store_ready.py` holds both halves of that honest: the
license text must exist in the source and in the ZIP, and the published page
must name a license rather than gesture at one.

## API

Uses the same public API as the website: `https://eucomply-scan.mahope-eeb.workers.dev/scan?url=<hostname>`