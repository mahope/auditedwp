# STATUS — 2. september 2026 — Iteration 439

## Hvad der er sket

### 1. Desktop-build: Windows-fejl fundet og rettet
Forrige build fejlede på Windows i "Derive version"-steppet: PowerShell
ødelagde `\"`-escapes i `node -p 'require(\"./package.json\")'`. Rettet med
`shell: bash` + ren quoting (commit d3baa31 på main), nyt build kørt
(run 32914498402). Alle tre platforme kom forbi det tidligere fejlpunkt;
resultat noteres, når bygget er færdigt.

### 2. Købsrejsen gennemgået som en fremmed
- Downloads-siden linkede kun til "Latest releases" — rettet til direkte
  link til v0.2.1 (macOS arm64/intel + Windows installer), som har alle
  assets. Verificeret live.
- Sidste npm-rester på downloads-siden fjernet ("via npm" → "via curl").
- Deployet og verificeret indhold på live-siden.
- Buy Now-flowet er klar: `/deskuptime/` henter checkout-URL runtime fra
  workerens `/config` — så snart `checkout_urls.deskuptime` sættes, vises
  købsknappen uden ny deploy.

## Ærlige tal

| Metrik | Værdi |
|--------|-------|
| Salg | **0** |
| Waitlist | **0** |
| Scans | https://auditedwp.pages.dev/stats |

## Blokering (1 linje)
LS API key ligger i Bitwarden som er låst (`bw status`: unauthenticated).

## Næste skridt
1. Verificér desktop-release-assets når run 32914498402 er færdig.
2. LS key → `wrangler secret put CHECKOUT_URL` / config → Buy-knap går live.
3. Evt. npm-publicering senere hvis Mads opretter npm-token (ikke blokerende).

## Venter på Mads
- Lås Bitwarden op én gang så LS key kan hentes.
- Køb af deskuptime.com (~$10/år, forhåndsgodkendt — sig bare til).
