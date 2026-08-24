# DECISION — Iteration 197 (24. august 2026, formiddag)

**Status:** DevNotify. Bygget, live, 13 sider med guides. 0 betalinger — blokeret på LS-nøgle.

## Vurdering under nye rammer (23. august: pengekriteriet)

**Universalitetskrav:** BESTÅET. Desktop-app (Tauri), tager GitHub token, 100% platform-uafhængig.

**Pengevurdering (5 kriterier):** DevNotify vinder på tid-til-1.-kunde og omkostning. $19 er lavt beløb pr. kunde, men ét salg dækker alle omkostninger på sitet (0 kr/md). Efter betaling bygges næste produkt.

| Faktor | DevNotify | Score |
|--------|-----------|:-----:|
| Tid til 1. kunde | Timer efter Mads logger ind i LS web-UI eller Bitwarden | ⭐⭐⭐⭐⭐ |
| Beløb pr. kunde | $19 (one-time) | ⭐⭐⭐ |
| Markedsstørrelse | ~1M GitHub power users på macOS | ⭐⭐⭐⭐ |
| Tilbagevendende | One-time (kan udvides: årlig update-abonnement $9/år) | ⭐⭐ |
| Omkostning | 0 kr/md | ⭐⭐⭐⭐⭐ |

**Ærlig vurdering:** DevNotify er et rigtigt produkt til en reel smerte (GitHub notifs i menulinjen, $19 er en fair pris for en lifetime-licens på en Mac-app). Den eneste mangel: betaling. Mads kan selv oprette checkout på 2 min via LS web-UI.

**Nye idéer under pengekriteriet:** Overvejet at droppe DevNotify for at bygge noget med umiddelbar betalingsmultiplikator. Men 0 omkostninger + 0 risiko gør DevNotify til det bedste valg — ét salg på $19 betyder produktet er i nul. Og med den færdige app og site er alternativomkostningen lav.

**Næste:** Hvis Mads ikke har tid til LS checkout i dag, starter jeg research på produkt #2 (byg parallelt, men DevNotify først). Ellers: flip checkout → testkøb → domæne → marketing.

## Domæne — status 24/8 (iteration 205)

Tokenet har registrar *læse*-adgang men IKKE skrive (`#domain:list` mangler ved
købsforsøg) og heller ikke `zone.create`. Købet kan derfor ikke automatiseres
endnu. Mads kan enten købe getdevnotify.com i dashboardet (~$10, forhåndsgodkendt)
eller udvide token-rettighederne — begge veje er klar i STATUS.md §6.

## Domæne (forhåndsgodkendt)

1. **getdevnotify.com** — action-oriented, .com, download-signal
2. devnotify.dev — kortere, .dev developer-fokus
3. devnotify.app — matcher produkttype