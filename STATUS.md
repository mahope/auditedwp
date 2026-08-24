# STATUS — Iteration 175 (24. august)

## 1. Blokering (én linje)

LS-checkout venter fortsat på Bitwarden/LS-nøglen (bw status: unauthenticated).

## 2. Universalitetsvurdering — bestået (20. gang)

DevNotify er en native macOS-app; sitet og alle guides er platform-agnostiske.
Ingen udtrækning nødvendig. Windows-guiden fik nu også FAQ-rich-snippets.

## 3. Denne iteration: ny Linux-guide + sitemap-reparation

1. **Ny guide:** "GitHub notifications on Linux: 4 working options" —
   browser/email/Gitify/notify-send-scripts, ærlige trade-offs, CTA til
   DevNotify, FAQ-schema. Fylder hullet i platforms-dækningen (mac ✓,
   Windows ✓, iPhone ✓, Linux → nu også ✓).
2. **Fejl fundet og rettet:** sitemap havde `github-notifications-on-windows`
   stående **to gange** (33 locs men kun 32 unikke). Deduplikeret + ny guide
   tilføjet → 34 URLs. XML valideret.
3. Cross-linket fra forsiden og Windows-guiden ("Keep reading").
4. Link-check kørt over hele sitet: 33 sider, 35 interne links, 0 brudte
   (kun forsiden og DMG-filerne, som er korrekte).
5. Deployet og verificeret live: /devnotify/ 200, linux-guiden 200 med indhold,
   sitemap indeholder linux-URL'en.

## 4. Traction (ærlige tal)

**0 betalende kunder · $0 · tilmeldinger: 0 · downloads: 1 · besøg: 2.**

## 5. Venter på Mads

1. Bitwarden-login / LS-nøgle → checkout live samme time.
2. Domænekøb getdevnotify.com (forhåndsgodkendt) — sig til.
3. Valgfrit: Apple Developer-konto ($99/år) til notarization.
4. Launch-tekster klar i `devnotify-site/LAUNCH.md` — venter på ja.

## 6. Næste iteration

Ny long-tail guide eller forbedring af købsrejsen; portefølje-produkt nr. 2
kun hvis en konkret, ikke-blokeret vej til penge findes hurtigere end DevNotify.
