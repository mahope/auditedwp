# STATUS — 5. september 2026 — Iteration 495

## Universality-vurdering (punkt 1) — stadig gyldig

**Transmute:** ✅ Universel. Kernen (engine.js) tager data i JSON/CSV/YAML/XML —
ingen CMS- eller platform-antagelser. CLI, web-demo og (senere) desktop-app er
indpakninger. **DeskUptime:** ✅ Universel (verificeret iter 491).

## Denne iteration

| Opgave | Status |
|--------|--------|
| Gennemgang af CSV→JSON-guide mod rigtig motor afslørede: guiden lovede tal-typer, motoren leverede strenge (`"age": "32"`) | ✅ Fundet |
| `coerceCSVValue()` tilføjet i engine.js: tal → Number, true/false → boolean, leading zeros (zip "0074") bevares som strenge bevidst | ✅ 28/28 tests |
| Ny test: CSV type coercion (tal, booleans, leading zeros) | ✅ Bestået |
| Guide-tekst opdateret til at beskrive den faktiske (nu korrekte) opførsel | ✅ Live |
| Deployet og verificeret på .pages.dev (200 + nyt indhold) | ✅ Live |

Lektion: guides skrevet før funktionen var bygget. Nu er dokumentationen og
motoren igen i overensstemmelse — verificeret med kørende kode.

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
2. Flere guides (CSV→SQL inserts kræver kun serializer — overvej)
3. Mads: `bw unlock` én gang → LS key → flip betaling
