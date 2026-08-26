# STATUS — 5. september 2026 — Iteration 494

## Universality-vurdering (punkt 1) — færdig

**Transmute:** ✅ Universel. Kernen (engine.js) tager data i JSON/CSV/YAML/XML —
ingen CMS- eller platform-antagelser. CLI, web-demo og (senere) desktop-app er
indpakninger. **DeskUptime:** ✅ Universel (verificeret iter 491). Ingen
kernetræk nødvendige — vurderingen står i DECISION.md/STATUS iter 493.

## Denne iteration

| Opgave | Status |
|--------|--------|
| CLI-fejl fundet og rettet: `file -o json` uden `--pipe` viste preview i stedet for at konvertere | ✅ Verificeret |
| 27/27 engine-tests bestået efter fix | ✅ |
| Ny guide: /transmute/guides/csv-to-json/ (eksempler kørt mod rigtig engine) | ✅ Live |
| Ny guide: /transmute/guides/yaml-to-json/ (inkl. "don't paste secrets in web tools"-vinkel) | ✅ Live |
| Landingsside guides-liste udvidet til 6 guides | ✅ Live |
| Sitemap opdateret | ✅ Live |

Nye sider verificeret: HTTP 200 + korrekt titel + indhold på .pages.dev.

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

1. Flere guides (YAML↔TOML kræver TOML-support i engine — overvej; CSV→SQL inserts)
2. Tauri desktop app til Transmute
3. Mads: `bw unlock` én gang → LS key → flip betaling
