# STATUS — Iteration 180 (24. august)

## 1. Blokering (én linje)

LS-checkout venter på Bitwarden/LS-nøglen (bw status: unauthenticated).

## 2. Universalitetsvurdering (punkt 1)

Bestået — ingen ændring siden it. 178/179. DevNotify-kernen er
platform-agnostisk (bygger til macOS/Windows/Linux i CI), og produktet er en
desktop-app, ikke et WordPress-produkt. Ingen kerne at trække ud.

## 3. Denne iteration: download-siden sælger nu alle 3 platforme

Sidst konstaterede jeg at downloadsiden kun nævnte macOS — vi solgte til ⅓ af
det marked vi kan betjene. Rettet:

- **Download-siden omskrevet** (`devnotify-site/download/index.html`): tre
  sektioner (macOS / Windows / Linux), per-platform instruktioner, SHA-256
  checksums for alle 5 artefakter, macOS-universal-DMG som primær Mac-download.
- **Artefakter lagt ud:** MSI, .deb og universal-DMG hostes på Cloudflare Pages;
  AppImage (85 MB) overskrider Pages' 25 MiB-grænse → hostes på GitHub Releases
  (mahope/auditedwp release `devnotify-v0.2.0`, gratis, permanent link).
- **Verificeret live** (ikke kun HTTP 200 — indhold + filstørrelser hentet):
  - `/devnotify/download/` → 200, viser Windows/Linux-sektioner
  - MSI → 200, 4.055.040 B · .deb → 200, 5.356.980 B · universal-DMG → 200, 8.053.662 B
  - AppImage via GitHub Releases → 200

Undervejs fejlede to deploys pga. AppImage-størrelsen (hele deploy blev afvist)
— løst ved at flytte netop den fil.

## 4. Traction (ærlige tal)

**0 betalende kunder · $0 · tilmeldinger: 0 · downloads: 1 · besøg: 2.**

## 5. Venter på Mads

1. Bitwarden/LS-nøgle → checkout live samme time (`CHECKOUT-GO-LIVE.md` klar).
2. Domænekøb getdevnotify.com (forhængsgodkendt) — sig til.
3. Valgfrit: Apple Developer ($99/år) til notarization.
4. Launch-tekster klar i `devnotify-site/LAUNCH.md` — venter på ja.

## 6. Næste iteration

Købsrejse for Windows/Linux-brugere gennemgås (landingssiden siger stadig
"Mac Menu Bar" — skal bredes ud), derefter flere købsintent-guides.
