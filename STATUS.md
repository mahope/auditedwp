# STATUS — 24. august 2026 — Iteration 250

## Kort version

**0 betalende kunder · $0 revenue · 0 rigtige tilmeldinger · 4 besøg / 1 download (metrics-worker, egen trafik ikke filtreret fra — behandl som ~0)**

Denne iteration: **konverteringsreparation på det der står mellem indhold og betaling.**
Universalitets-vurderingen bestod i iteration 249 og gentages ikke.

## Fundet og rettet denne iteration

Gennemgang af købsrejsen med friske øjne fandt **ét alvorligt problem**:

1. **Blog-indeksen havde NUL links til de 27 artikler.** Alle blogindlæg var kun
   tilgængelige via sitemap.xml — Google crawler dem måske, men mennesker der landede
   på /blog/ så bare en tom overskrift. Rettet: indeksen genereret på ny med 27 kort
   (titel, beskrivelse, dato), alle links verificeret mod filsystemet (0 brudte).

2. **Ingen af blog-siderne linkede til /pro/ ($79/år-produktet).** Trafik kunne komme
   ind på en guide og dø uden at se produktet. Rettet: "Pro"-link i navigationen på
   blog-indeksen + 23 artikler; de 4 artikler med alternativt navn (Abmahnung m.fl.)
   fik et fremhævet "Pro — $79/yr"-link.

Deployet og verificeret live (cache-bustet curl): /blog/ viser 27 kort + Pro-link,
artiklerne peger på /pro/.

## Konstateringer (ikke handlet endnu)

- Bing-indeksering via r.jina.ai gav uklart svar (1 hit) — reelt indekseringsantal ukendt.
  Kan først måles ordentligt når domæne + Search Console er sat op.
- Trust-signaler på /pro/ er ok: money-back, secure checkout, cancel anytime, pris overalt.
- npm publish kræver login → ny blokering ud over Bitwarden (npm-token findes ikke).

## Blokeringer (én linje hver)

1. LS API key + CWS OAuth credentials i Bitwarden — kræver manuel unlock af Mads.
2. npm-token for quick-format publish — samme Bitwarden.

## Næste skridt

1. **Mads (2 min):** unlock Bitwarden → flip CHECKOUT_URL → første betaling mulig samme time.
2. Mig: fortsæt konverteringsarbejde uden blokering — næste kandidat er
   cross-linking fra /vs/-siderne (6 konkurrent-sider) til /pro/ og scanneren.
3. Domæne: quickformat.com vurdering står i DECISION.md; køb klar når Mads siger go.

## Lærdom (fast)

Verificér JS-adfærd, ikke kun 200'er — og gå selv købsrejsen igennem som en fremmed:
bloggen har haft 27 usynlige artikler i flere iterationer uden at nogen tjek bemærkede det.
