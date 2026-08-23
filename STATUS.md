# STATUS

## 2026-08-23 — Iteration 29: Verificeret + deploy-klar. Venter kun på Mads' to tastetryk.

### Beslutnings-status
AuditedWP holder under penge-mandatet (revurderet iter. 28, står ved magt):
første kunde kan betale så snart siden er live + Stripe-link står;
€290 setup + €29/site/md tilbagevendende; bevist wholesale-marked; lav
leveringsomkostning. Ingen tidligere droppet idé slår den på de fem
penge-kriterier.

### Iteration 29
- Gen-verificeret: gyldig HTML på alle 4 sider, JS OK.
- `site/deploy.sh` skrevet — deploy er nu én kommando for Mads:
  `sh site/deploy.sh` (efter engangs `npx wrangler login`).

### Næste skridt (i rækkefølge)
1. **Mads:** `npx wrangler login` → `sh site/deploy.sh` → sitet er LIVE på auditedwp.pages.dev.
2. Stripe Payment Links i pristabellen (gratis) — spørgsmål: under hvis navn?
3. Domæne auditedwp.com (~70 DKK, forhåndsgodkendt) sættes foran bagefter.
4. Pilot-bureauer — KUN efter Mads' ja til udadvendt henvendelse.

### Blokeret på Mads (uændret)
1. Pages-deploy (to kommandoer ovenfor).
2. JA/NEJ til udadvendte mails til pilot-bureauer.
3. Under hvis navn oprettes Stripe-kontoen?
4. Juridisk review af DPA/NDA før første underskrift.

### Budget
0 kr brugt. Anmodet: 1 domæne (~70 DKK, forhåndsgodkendt).
