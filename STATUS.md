# STATUS — Iteration 114 (23. august 2026, aften)

## 1. Universitets-vurdering (punkt 1) — bestået

DevNotify er ikke platform-bundet: kernen er notifications-API → normaliseret
liste → menu bar UI + polling. GitHub er én adapter; GitLab/Linear/Jira kan
lægges ind uden kerne-ændring. Ingen udtrækning nødvendig.

## 2. Største fund denne iteration: en uærlig påstand — rettet i kode

Sitet lover "free 7-day trial", men app'en havde INGEN trial- eller
licenskode (verificeret: ingen hits i lib.rs/main.js). Downloadede brugere
fikk altså produktet gratis for altid, og påstanden kunne ikke dokumenteres.
Det er præcis den slags selvsnyd der gav os "6 tilmeldinger der var vores egne".

**Rettet:** Ægte trial implementeret og bygget ind i DMG'en:
- `first_run`-tidsstempel gemmes lokalt ved første start → 7 dage.
- Efter 7 dage nægter backend at hente notifikationer med en ærlig fejl der
  peger på købssiden.
- Licensnøgle-felt + aktivering i UI (`get_trial_status` / `activate_license`
  Tauri-kommandoer). Remote-validering mod Lemon Squeezy er klar som TODO,
  så snart API-nøglen ligger i Bitwarden.

| Ting | Status |
|------|--------|
| Trial-gate i Rust (check_now blokerer efter 7 dage) | ✅ cargo check rent |
| License UI (felt + activate) i settings-panel | ✅ |
| DMG genbygget med ny binær (verificeret arm64, trial-streng i binary) | ✅ live, 4.45 MB |
| vs/gitify-side + sitemap synkroniseret fra publish til devnotify-site | ✅ |
| **KRITISK:** devnotify-site kopieret til site/devnotify — tidligere lå produktet KUN i et publish-subdir som en rod-deploy ville have slettet | ✅ |
| Rod-deploy + verificering: alle URLs 200, DMG 200 (4.45 MB), sitemap har 2 devnotify-URLs | ✅ |

## 3. Traction (ærligt)

**0** betalende kunder · **0** downloads · **$0** revenue. (Ingen analytics på
DMG-downloads endnu — tal kommer først når Cloudflare Web Analytics eller LS
er koblet på.)

## 4. Budget

Brugt: **0 kr**. getdevnotify.com forhåndsgodkendt (~90 DKK), venter på køb.

## 5. Venter på Mads

| Hvad | Blokerer |
|------|----------|
| Lemon Squeezy API-nøgle (Bitwarden) | Checkout-knap + rigtig licensvalidering — ENESTE revenue-blokering |
| Domænekøb getdevnotify.com | Ordentlig URL |
| Ja/nej til 3 færdige posts (POSTS/ + KANALPLAN) | Udvendig marketing |

## Næste iteration

1. LS-nøgle → opret produkt $19 via API → checkout-URL i buy-btn → remote
   licensvalidering i app'en → genudgiv.
2. Mere SEO-indhold ("gitify alternative", "github notifications menubar").
