# STATUS — Iteration 120 (23. august 2026, aften)

## 1. Universitets-vurdering (punkt 1) — nu bestået I KODE, ikke kun i ord

Sidste iteration konkluderede at kernen var platform-agnostisk. Denne iteration
blev det bevist: `fetch_notifications` kaldte stadig api.github.com direkte.
Nu:

- **Ny fil `devnotify/src-tauri/src/providers.rs`:** `Provider`-enum (GitHub,
  GitLab), normaliseret `NotificationItem`, én adapter pr. platform.
  GitHub-adapter: notifications-API. GitLab-adapter: todos-API (`read_api`
  scope). Ny provider = én funktion, nul ændringer i UI/tray/trial-logik.
- **Frontend:** Platform-vælger (GitHub/GitLab) i Preferences, token-hint
  skifter pr. platform, gemmes i `provider.txt`.
- **Bygget + pakket:** release-build OK, ny aarch64-DMG lavet (Tauris
  DMG-bundler fejlede på Finder-AppleScript i baggrundskørsel — omgået med
  hdiutil direkte; checksum-verificeret).

## 2. Ny SEO-indgang: "gitlab notifications mac"

- `/devnotify/gitlab-notifications-mac/` — HowTo JSON-LD, GitLab-farvet design,
  mockup, FAQ, links til download og købsrejse. Live og 200.
- Linket fra forsidsens nav + sitemap opdateret. Verificeret live.

## 3. Traction (ærligt)

**0** betalende · **0** notify-me-tilmeldinger · **$0** revenue. Uændret.

## 4. Venter på Mads (én linje)

LS API-nøgle (Bitwarden låst med master password).

## 5. Næste iteration

1. LS-nøgle → produkt $19 via API → checkout erstatter notify-formularen.
2. Remote licensvalidering mod LS (TODO i lib.rs).
3. x64-DMG gendannes med samme hdiutil-metode (nuværende x64 er v0.1.0 uden
   GitLab-adapter — overvej version bump til 0.2.0 når begge ark er nye).
