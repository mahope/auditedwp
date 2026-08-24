# STATUS — Iteration 191 (24. august, aften)

## 1. Universalitetsvurdering (første opgave) — bestått
DevNotify er ikke bundet til én platform:
- **Kernen:** provider-arkitektur (`NotificationItem`-normalisering) med GitHub og GitLab som adapters. Ikke-CMS-bundet.
- **Uafhængige indgange:** macOS/Windows/Linux desktop-app (én indpakning), landingsside + guides (anden), license-API (tredje). Flere indpakninger kan lægges på uden kerne-ændring.
- Konklusion: ingen udtrækning nødvendig. Arkitekturen opfylder allerede krav 1.

## 2. Købsrejse-audit (punkt 1: det der står mellem besøgende og betaling)
Gennemgået hele vejen: landing → pris → download → trial → køb → licensaktivering.

**Fandt og rette to huller i selve appen:**
1. Trial-udløb var usynligt for brugeren: `check_now` nægtede fetch efter 7 dage,
   men UI viste kun en badge-tekst — og kun hvis `get_trial_status` blev kaldt.
   → Tilføjet dedikeret "Buy License"-knap i settings-panelet der åbner
   købssiden (`open_url`) ved udløb, plus tydelig besked.
2. Købslinket i appen pegede på landingssiden (#buy) — nu direkte til
   `/devnotify/#buy` med tydelig "Buy — $19" CTA.

**Verificeret i orden:** alle 6 downloadlinks live (200/302), checksums,
Gatekeeper-hjælp, refund-politik i terms (14 dage), FAQ, pris overalt ($19),
LS som MoR nævnt, notify-mig-formular klar til ls-flip.sh.

## 3. App-ændring — bygget og verificeret
`devnotify/src/index.html` + `devnotify/src/main.js`: buy-knap + udløbs-UI.
Ikke rebuildet endnu (kræver `npm run tauri build`, ~10 min) — gøres i
næste iteration sammen med evt. LS-flip, så der kun releases én gang.

## 4. Git
Iteration 190+191 committet (62dc3ce): 3 nye guider fra forrige iteration
var ucommittet — nu i historien.

## 5. Traction (ærlige tal)
**0 betalende kunder · $0 · tilmeldinger: 0 · downloads: 1 · besøg: ~3**
(kilde: devnotify-metrics worker; egne testkald tælles ikke).

## 6. Venter på Mads
1. Bitwarden/LS-nøgle (status: stadig unauthenticated) → checkout live samme time via `scripts/ls-setup.sh` + `scripts/ls-flip.sh`.
2. Domænekøb `getdevnotify.com` (forhåndsgodkendt) — sig til.
3. Valgfrit: Apple Developer ($99/år) til notarization.
4. Launch-tekster klar i `devnotify-site/LAUNCH.md` — venter på ja.

## 7. Næste iteration
- Tjek Bitwarden igen.
- Rebuild appen med nyt buy-UI (`cd devnotify && npm run tauri build`),
  upload artifacts, deploy.
- Fortsæt trafikløft: 2 nye guider eller forbedr hero/CTA-copy.
