# STATUS — Iteration 179 (24. august)

## 1. Blokering (én linje)

LS-checkout venter på Bitwarden/LS-nøglen (bw status: unauthenticated).

## 2. Universalitetsvurdering (punkt 1) — bestått, nu bekræftet i praksis

It. 178's vurdering står ved magt: kernen (`providers.rs`) er platform- og
CMS-agnostisk. Denne iteration gjorde det bogstaveligt:

- `open_url` var den eneste mac-afhængighed i lib.rs → nu cfg-opdelt til
  macOS/Windows/Linux (`cargo check` består på mac; Windows-target kan ikke
  cross-checkes lokalt pga. llvm-rc, men bygger grønt i CI).
- Accelerators ændret fra Cmd til CommandOrControl.
- **CI-byg gennemført for ALLE tre platforme** — se nedenfor.

Konklusion: punkt 1 opfyldt. Ingen kerne at trække ud.

## 3. Denne iteration: DevNotify er nu et 3-platformsprodukt (gratis CI)

`.github/workflows/build-devnotify.yml` oprettet og kørt grønt
(run 32695480660). Verificerede artefakter (downloadet og inspiceret):

| Platform | Fil | Størrelse | Verifikation |
|---|---|---|---|
| macOS (universal) | DevNotify_0.2.0_universal.dmg | 8 MB | hdiutil verify: VALID |
| Windows x64 | DevNotify_0.2.0_x64_en-US.msi | 4 MB | file: gyldig MSI-installer |
| Linux | .AppImage (85 MB) + .deb (5 MB) | — | file: ELF / Debian pkg |

Adresserbart marked gik fra "mac-brugere" til alle desktop-udviklere uden
omkostning (GitHub Actions gratis tier).

Undervejs rettet 3 CI-fejl: forkerte bundle-navne pr. platform, dobbelte
--bundles-argumenter fra tauri-action, manglende artifact-upload.

## 4. Traction (ærlige tal)

**0 betalende kunder · $0 · tilmeldinger: 0 · downloads: 1 · besøg: 2.**

## 5. Venter på Mads

1. Bitwarden-login / LS-nøgle → checkout live samme hour (`CHECKOUT-GO-LIVE.md`
   ligger klar i staging).
2. Domænekøb getdevnotify.com (forhåndsgodkendt) — sig til.
3. Valgfrit: Apple Developer-konto ($99/år) til notarization.
4. Launch-tekster klar i `devnotify-site/LAUNCH.md` — venter på ja.

## 6. Næste iteration

Sitets download-side nævner kun macOS — skal udvides med Windows/Linux-
downloads + checksums (artefakterne findes nu), ellers sælger vi kun til ⅓ af
markedet vi pludselig kan betjene. Derefter flere købsintent-guides.
