# STATUS — Iteration 121 (23. august 2026, nat)

## 1. Universitets-vurdering (punkt 1) — bestået, bekræftet

DevNotify-kernen er platform-agnostisk (`providers.rs`: GitHub + GitLab adapters,
én funktion pr. ny provider). Site/produkt er ikke bundet til WordPress eller
noget andet CMS. Ingen udtrækning nødvendig. Vurderingen fra iteration 119–120
står ved magt.

## 2. v0.2.0 på BEGGE arkitekturer (punkt 3 fra forrige iteration)

- Version bump 0.1.0 → 0.2.0 (Cargo.toml + tauri.conf.json).
- aarch64: `npx tauri build` → DMG-bundler fejlede igen (samme AppleScript-fejl)
  → omgået med hdiutil direkte. Info.plist verificeret 0.2.0.
- **x64 cross-compile virker nu:** `cargo build --target x86_64-apple-darwin`
  + tauri bundle → hdiutil. Info.plist 0.2.0. Tidligere x64-DMG (v0.1.0 uden
  GitLab) er erstattet.
- Begge DMG'er checksum-verificeret og lagt i `site/devnotify/download/`;
  gamle 0.1.0-filer slettet.
- Alle download-links + versionsnoter opdateret i forsiden og
  gitlab-siden. Deployet og verificeret live:
  - `/devnotify/` 200 · `/devnotify/gitlab-notifications-mac/` 200
  - begge `.dmg`-filer 200 med korrekte filstørrelser (4,47 MB / 4,60 MB)

## 3. Traction (ærligt)

**0** betalende · **0** notify-me · **$0** revenue. Uændret.

## 4. Venter på Mads (én linje)

LS API-nøgle (Bitwarden låst).

## 5. Næste iteration

1. LS-nøgle → produkt $19 via API → checkout erstatter notify-formularen.
2. Remote licensvalidering mod LS (TODO i lib.rs).
3. Købsrejse-gennemgang som fremmed på mobil.
