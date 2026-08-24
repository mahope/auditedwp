# STATUS — Iteration 177 (24. august)

## 1. Blokering (én linje)

LS-checkout venter på Bitwarden/LS-nøglen (bw status: unauthenticated).

## 2. Universalitetsvurdering — bestået (22. gang)

DevNotify-kernen er en native macOS-app (Tauri) med licensvalidering mod LS
License API — ingen platform-bunden logik at trække ud. Sitet dækker
mac/Windows/Linux/iOS/Android som guides; Windows/Linux/Android-brugere er
eksplicit målgruppe i indholdet, ikke kun mac-brugere. Produktet ER kernen;
guides er indgangene. Punkt 1 opfyldt.

## 3. Denne iteration

1. **Sync-fejl rettet:** iteration 176's filer (Android-guide, sitemap,
   cross-links) lå KUN i `.deploy-staging/devnotify/`, ikke i
   `devnotify-site/` — arbejdskopien var bagefter det deployede. Synkroniseret
   så der nu er én kilde til sandhed.
2. **Reelt fund via link-gennemgang:** `github.com/watch_disabled` findes ikke
   (død ekstern link i Slack-guiden) → rettet til `github.com/watching`.
3. **Ny guide:** "GitHub notifications not showing on Windows: 7 fixes" —
   problemorienteret long-tail ("not showing"-søgninger har købsintent),
   FAQ-schema, BurntToast-script-eksempel, token-scope-fejlkilde, CTA.
4. Link-check: 0 brudte interne links (terms/privacy verificeret live 200 med
   indhold). Sitemap 34 → 35 URLs. Deployet og verificeret live: ny guide 200
   med titel, rettet URL på live-siden, sitemap tæller 35.

## 4. Traction (ærlige tal)

**0 betalende kunder · $0 · tilmeldinger: 0 · downloads: 1 · besøg: 2.**

## 5. Venter på Mads

1. Bitwarden-login / LS-nøgle → checkout live samme time (`CHECKOUT-GO-LIVE.md`
   ligger klar).
2. Domænekøb getdevnotify.com (forhåndsgodkendt) — sig til.
3. Valgfrit: Apple Developer-konto ($99/år) til notarization.
4. Launch-tekster klar i `devnotify-site/LAUNCH.md` — venter på ja.

## 6. Næste iteration

Flere "problem + fix"-guides med købsintent (den type konverterer bedre end
"options"-lister), eller forbedring af download-sidens CTA. Portefølje nr. 2
kun hvis en konkret, ikke-blokeret vej til penge er hurtigere end DevNotify.
