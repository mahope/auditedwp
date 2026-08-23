# STATUS — Iteration 118 (23. august 2026, aften)

## 1. Universitets-vurdering — bestået (uændret)

DevNotify: kernen er notifications-API → normaliseret liste → menu bar UI.
GitHub er én adapter; GitLab/Linear kan lægges ind uden kerne-ændring.

## 2. Bygget denne iteration: købsrejsen fik fanget interessen

Før: klik på "Buy license" → død alarm-boks. Enhver interesseret besøgende
forsvandt uden spor. Nu:

| Ting | Verificeret |
|------|-------------|
| `/subscribe`-endpoint i devnotify-metrics Worker: gemmer e-mail i KV, afviser test-/example-adresser (422), 1 tælling pr. IP/time | ✅ lokalt + live testet |
| Landingsside: buy-knap åbner ærlig notify-me-formular ("checkout opens within days") | ✅ live |
| Client-side spejl af test-adresse-afvisning | ✅ |
| privacy.html: ny sektion om launch-listen (én mail, slettes ved launch) | ✅ live |
| Deploy verificeret på auditedwp.pages.dev/devnotify/ | ✅ |

## 3. Fejl fundet og rettet undervejs

- Mit eget røgtest-kald mod `/subscribe` landede i PRODUKTIONENS KV. Slettet
  (`subscriber:eagerbuyer@outlook.com`), tæller nulstillet til 0. Røgtests skal
  fra nu af KUN køres mod lokal wrangler-dev.
- `stats`-endpoint returnerede nu også `subscribers`.

## 4. Traction (ærligt)

**0** betalende · **0** downloads · **0** besøg (ekskl. egne) · **0**
notify-me-tilmeldinger · **$0** revenue.

## 5. Budget

Brugt: **0 kr**. getdevnotify.com forhåndsgodkendt (~90 DKK).

## 6. Venter på Mads (én linje)

LS API-nøgle (Bitwarden — app'en kører, men er låst med master password).
Domæne klar til køb.

## Næste iteration

1. LS-nøgle → opret produkt $19 via API → erstat notify-formular med rigtig
   checkout → send én mail til launch-listen → slet listen.
2. Licens-validering kobles på LS API (TODO i lib.rs).
3. Flere SEO-indgange ("github notifications widget mac", "tauri menubar").
