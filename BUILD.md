# BUILD: Transmute — Desktop data transformer

## Korteste vej til første betalende kunde

**LS key skal komme** før betaling kan aktiveres. Indtil da: alt andet er bygget.

## Status: ✅ Engine, CLI, site, Tauri desktop app — ALT bygget

### ✅ Kernen (engine.js)
- Input: JSON, CSV, YAML, XML, plain text (auto-detect)
- Output: JSON, CSV, YAML, XML, table
- 12 transformationer: filter, map, pick, omit, sort, unique, group, count, head, tail, rename, flatten
- 28/28 tests passerer
- Public på GitHub: github.com/mahope/transmute

### ✅ CLI
- `npx github:mahope/transmute` — verificeret fra ren mappe
- Interactive preview, piped input, fil-til-fil, fil-til-stdout

### ✅ Site (auditedwp.pages.dev/transmute/)
- Produktside med demo, features, guides, CLI eksempler, prissætning
- 8 guides (JSON→CSV, XML→JSON, YAML→JSON, etc.) — alle eksempler verificeret mod engine
- Web-demo kører samme engine i browseren

### ✅ Tauri Desktop app (NY — denne iteration)
- **Frontend:** Egen copy af engine.js i browseren (samme transformationslogik)
- **Backend:** Rust shell med LS license key gating, free-tier (3 runs/launch)
- **Platform:** macOS, Windows, Linux (kompileret via GitHub Actions)
- **Build workflow:** `.github/workflows/build.yml` — trigger på `v*` tags eller `workflow_dispatch`

### ⏳ Mangler før betaling
1. **LS API key** (Bitwarden, ventes 24/8) — opret produkt i LS, checkout-link
2. **Push release tag** (v0.1.0) til GitHub → trigger build → .dmg/.msi/.exe klar
3. **Køb domæne** (transmute.app eller transmute.dev) — forhåndsgodkendt

## Prissætning
- **CLI**: Gratis (open-source, npm/github)
- **Desktop app**: $19 one-time (3 aktiveringer, LS license key)
- **Free tier**: 3 transformationer per launch (uden licens)