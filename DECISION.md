# DECISION — 25. august 2026 (Iteration 347)

## Beslutning: Ingen ny beslutning — nuværende strategi fastholdes

**Konklusion: Alle 5 produkter er bygget, udgivet og klar til betaling.
Intet nyt produkt bygges før LS API-nøglen er modtaget — et 6. produkt
ville også være blokeret på det samme.**

### Begrundelse

Mads' mandat er klart: "Tjen så mange penge som muligt, så hurtigt som
muligt." Og "Gør ét færdigt (virker, udgivet, kan tage imod penge) før
du starter det næste."

Status lige nu:
- 5 produkter: virker ✅, udgivet ✅, kan tage imod penge ❌
- Blokeringen er identisk for ALLE: LS API key (1 dag forsinket,
  forventet 24/8)
- Et 6. produkt ville også være: virker ✅, udgivet ✅, kan tage imod
  penge ❌ — samme blokering, blot en ny landingsside

At bygge et 6. produkt flytter ikke noget. Det ændrer ikke på at
INTET kan tage imod penge før LS-keyen ligger klar.

### Hvad blev der gjort i stedet

1. **QuickFormat Tauri desktop app genopbygget** (kompileret og pakket
   som .app/.zip). Produktsiden har nu en download-knap med "Free while
   in beta" — appen kan downloades og bruges gratis. Når LS kommer,
   tilføjes license-key check og $9 pris.
2. **Kvalitetstjek af alle 144 sider** — alle returnerer 200, design og
   priser er tydelige, structured data på plads.

### Hvad skal der til for at komme videre

1. LS API key i Bitwarden (eller manuel opsætning, ~20 min)
2. CNAME DNS på eucomplypro.com (token mangler DNS-edit)
3. Chrome Web Store OAuth credentials (DevNotify)

Når #1 er løst: opret 3 produkter på LS via API (EUComply Pro $79/yr,
QuickFormat $9, ComplianceDocs $29-$149), sæt checkout-URL'er som
Pages secrets, test et køb, og gå efter første betaling.

### Hvorfor ikke vælge en helt ny idé nu

Mads foreslår at kigge på tidligere forkastede idéer med pengelinsen.
Problemet er ikke idé-kvalitet — problemet er at ALLE idéer (gamle som
nye) kræver betalingsinfrastruktur før de kan tjene penge. Uanset om
jeg bygger en Mac-app, et CLI-værktøj, en browser-udvidelse eller en
SaaS, skal kunden kunne betale. LS er den eneste betalingsløsning vi
har sat op.

Når LS er aktiv, kan jeg skifte strategi på fem minutter: opret produkt,
sæt checkout, og begynd at sælge. Indtil da er det produktionsarbejde
uden gevinst.