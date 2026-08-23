# STATUS — Iteration 142 (24. august)

## 1. Universalitet (punkt 1) — vurdering

DevNotify-kernen (`devnotify/src-tauri/src/providers.rs`) er platform-uafhængig:
`Provider`-enum + `fetch_notifications(provider, token)` tager et token og
returnerer notifikationer. GitHub og GitLab er adapters; en ny platform er én ny
variant. Sitet er statisk HTML. **Ikke bundet til én platform — intet at trække
ud. Verificeret i koden denne iteration.**

## 2. Pengevurdering (punkt A)

Beslutningen holder under de fem pengekriterier: produktet er bygget og
udgivet (0 kr omkostning), $19 one-time, timer til første kunde så snart
LS-checkout åbner. Ingen ny idé slår det på tid-til-første-betaling. DevNotify
forbliver valget. BUILD.md er opdateret.

## 3. Gjort denne iteration (punkt B: forbedr købsrejsen)

- Gennemgik alle interne links på alle 7 devnotify-sider som en fremmed.
- Fandt 3 brudte ankre: `#download` fandtes ikke på landingssiden — CTAs på
  best-github-notification-apps-macos, github-token-scopes-guide og vs/gitify
  pegede i tomheden. Rettede dem alle til `/devnotify/download/`.
- Deployet og verificeret live: alle sider 200, rettelsen bekræftet i HTML.
- Købsrejsen nu: landing/guide → download-side → DMG → #buy → (venter LS).

## 4. Blokeringer (én linje hver)

1. LS API-nøgle: Bitwarden `unauthenticated` → checkout kan ikke åbnes endnu.
2. Domæne getdevnotify.com: ikke købt endnu.

## 5. Traction (ærlige tal)

**0** betalende · **$0** revenue · **0** rigtige tilmeldinger.

## 6. Venter på Mads

1. LS-nøgle i Bitwarden → LS-produkt via API + live checkout + købstest.
2. Domænekøb getdevnotify.com.

## 7. Næste iteration

Ny guide ("github notifications slack integration" eller "gitlab desktop app
alternative") + flere sammenligningssider. LS-nøglen: checkout før alt.
