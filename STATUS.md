# STATUS — Iteration 178 (24. august)

## 1. Blokering (én linje)

LS-checkout venter på Bitwarden/LS-nøglen (bw status: unauthenticated).

## 2. Universalitetsvurdering — bestået (23. gang, denne gang med kodelæsning)

Tidligere vurderinger har kunset sig på sitets indhold. Denne gang er koden
læst igennem (`devnotify/src-tauri/src/providers.rs`, `lib.rs`, `src/main.js`):

- **Kernen er platform-agnostisk i sin arkitektur.** `providers.rs` definerer en
  normaliseret `NotificationItem` og et `Provider`-enum; GitHub og GitLab er to
  adapters bag `fetch_notifications()`. En tredje provider (Gitea, Bitbucket)
  tilføjes uden ændringer i tray, UI eller licenslogik.
- **Appen selv er ikke bundet til ét site** — den tager en token og taler med
  en REST-API. "Universel" her betyder: ikke kun GitHub, ikke kun macOS-funktioner
  der forudsætter GitHub. GitLab understøttes allerede i produktet.
- **Sitets indhold dækker Windows/Linux/Android/iOS/GitLab** som guides —
  platformene er målgruppe, ikke grænse.
- **Hvad der reelt ER bundet:** branding ("GitHub notifications in your Mac menu
  bar") og DMG-downloads er mac-only. Det er en go-to-market-afgørelse, ikke en
  kodeafhængighed — kernen kunne udgive til Windows/Linux uden omskrivning af
  fetch-laget (kun tray/open_url-platformkode).

**Konklusion: punkt 1 opfyldt. Ingen kerne at trække ud — det universelle lag
(providers.rs) findes allerede og er det rigtige sted.**

## 3. Denne iteration

1. **Verificeret at it. 177 faktisk er live** (memory-advarsel fulgt: tjekket
   indhold, ikke HTTP-status): ny Windows-guide 200 med indhold, forsiden
   linker til den, sitemap tæller 35 URLs. Arbejdskopi `.deploy-staging/` og
   `devnotify-site/` er identiske (undtagen CHECKOUT-GO-LIVE.md, som med vilje
   kun ligger i staging).
2. **Link-gennemgang af HELE sitet med script:** 33 lokale sider samlet, alle
   interne hrefs kontrolleret mod filsystemet → **0 manglende mål** (kun
   `/devnotify/#buy`, som er et anker på forsiden). Ingen brudte links.
3. **Købsrejse gennemgået side for side:** pris ($19) synlig i hero, price-note,
   FAQ og buy-sektion; download-side med SHA-256-checksums og "app can't be
   opened"-hjælp; trial/licens-flow i appen matcher sitets løfter (7 dage,
   remote LS-validering klar via compile-time env). Ingen pladsholdere.
4. **Universalitetsvurdering skrevet ovenfor** — baseret på kodelæsning.

## 4. Traction (ærlige tal)

**0 betalende kunder · $0 · tilmeldinger: 0 · downloads: 1 · besøg: 2.**

## 5. Venter på Mads

1. Bitwarden-login / LS-nøgle → checkout live samme time (`CHECKOUT-GO-LIVE.md`
   ligger klar i staging).
2. Domænekøb getdevnotify.com (forhåndsgodkendt) — sig til.
3. Valgfrit: Apple Developer-konto ($99/år) til notarization.
4. Launch-tekster klar i `devnotify-site/LAUNCH.md` — venter på ja.

## 6. Næste iteration

To lige veje, begge ikke-blokerede:
- **Windows/Linux-builds af kernen** — koden er klar i providers-laget; en
  Windows-DMG… altså .msi/.exe ville gøre "universelt" bogstaveligt i produktet
  og fordoble adressérbare brugere. Kræver CI-byg (GitHub Actions, gratis).
- Flere "problem + fix"-guides med købsintent (konverterer bedre end lister).

Portefølje nr. 2 først hvis en konkret, ikke-blokeret vej til penge er
hurtigere end DevNotify.
