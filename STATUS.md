# STATUS — 5. september 2026 — Iteration 497

## Universality-vurdering (punkt 1) — genbekræftet

**Transmute:** ✅ Universel. Kernen (engine.js) tager data i JSON/CSV/YAML/XML —
ingen CMS- eller platform-antagelser. CLI, web-demo, guides og (senere) desktop-app
er indpakninger omkring den samme motor. **DeskUptime:** ✅ Universel (verificeret
iter 491). Ingen udtrækning nødvendig — begge kerner er allerede platform-frie.

## Denne iteration

| Opgave | Status |
|--------|--------|
| Rigtig fejl fundet i gennemgangen: YAML-input som enkelt objekt (ikke liste) parsede til `[]` — rettet i engine.js | ✅ Fixet, 28/28 tests |
| **Transmute CLI udgivet: github.com/mahope/transmute (public)** | ✅ Live |
| `npx github:mahope/transmute t.csv --output json` verificeret fra ren mappe | ✅ Virker |
| README med alle eksempler kørt mod rigtig motor først (scripts/verify-readme.js) | ✅ Verificeret |
| Alle install-commands på sitet opdateret: `npx transmute` → `npx github:mahope/transmute` (den bare `transmute` på npm er en fremmed pakke fra 2014!) | ✅ Live |
| Deployet; /transmute/ + alle 8 guides svarer 200 med nye commands | ✅ Live |

**Vigtig opdagelse:** Siderne har hidtidig hævdet `npx transmute` — men den pakke
på npm ejes af en fremmed (logicalparadox, stream-transforms, ikke vores). Enhver
der fulgte guiden fik en fejl. Nu peger ALLE steder på `npx github:mahope/transmute`,
som jeg har verificeret virker ende-til-ende. npm-pakkenavn kan købes senere hvis
det bliver relevant (kræver Mads' npm-konto/token).

## Tal (ærlige)

| Metrik | Værdi | Kilde |
|--------|-------|-------|
| Salg (DeskUptime) | **0** | LS key utilgængelig |
| Salg (Transmute) | **0** | LS key utilgængelig |
| Waitlist | **0** | worker /stats |
| Scans (eksterne) | 2 | quickcheck-worker |

## Blokeret (én linje)

LS API key i Bitwarden — én `bw unlock` fra Mads → checkout på BEGGE produkter.

## Næste skridt

1. Tauri desktop app til Transmute (næste store punkt)
2. Mads: `bw unlock` én gang → LS key → flip betaling på begge produkter
