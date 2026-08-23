# STATUS

## 2026-08-23 — Iteration 30: Beslutningen holder; sitet repareret og verificeret.

### Penge-revurdering (mandat 23/8) — beslutningen STÅR
AuditedWP målt på de fem penge-kriterier:
1. **Hurtighed til første betalende kunde:** landingsside færdig + verificeret;
   checkout er mail → onboarding-samtale → Stripe. Kan ske samme uge som deploy.
2. **Beløb:** €290 setup + €29/site/md (€19 ved 26+). Ét bureau med 15 sites =
   ~€435/md tilbagevendende fra dag ét.
3. **Antal kunder:** tusindvis af EU-bureauer; white-label-modellen giver 5-20
   sites pr. kundeforhold (TREJKA/WP Supra/fixed.net beviser markedet).
4. **Tilbagevendende:** ja — månedsabonnement pr. site, naturlig retention.
5. **Leveringsomkostning:** lav — én operator + agenter + MainWP/WP Umbrella;
   concierge-MVP, ingen software bygges før første betaler.

Ingen tidligere droppet kandidat slår den på disse fem (gen-tjekket iter. 30).

### Iteration 30 — hvad der blev lavet
- **Fejl fundet og rettet:** den tyske landingsside MANGLEDE margin-beregneren,
  som BUILD.md påstod var tilføjet i iter. 27. Den er nu der (fuld DE-tekst,
  de-DE talformat). Byg-aldrig-påstande verificeres heretter.
- Script-tags flyttet ind i body på EN+DE (valideringsfejl); alle 4 sider
  (`index.html`, `de/index.html`, `sample/`, `template/`) validerer nu rent,
  JS syntakstjekket OK. Commit 1d21728.
- Deploy afprøvet: wrangler er IKKE logget ind — deploy kan først køre efter
  Mads' engangs `npx wrangler login`.

### Næste skridt
1. **Mads (engangs):** `npx wrangler login` → derefter `sh site/deploy.sh` →
   live på https://auditedwp.pages.dev.
2. Stripe Payment Links ind i pristabellen (gratis) — kræver svar på: under
   hvis navn?
3. Domæne auditedwp.com (~70 DKK, forhåndsgodkendt) sættes foran bagefter.
4. Pilot-bureauer — kun efter Mads' ja til udadvendt henvendelse.

### Blokeret på Mads (uændret)
1. Pages-deploy (login ovenfor).
2. JA/NEJ til udadvendte mails til pilot-bureauer.
3. Under hvis navn oprettes Stripe-kontoen?
4. Juridisk review af DPA/NDA før første underskrift.

### Budget
0 kr brugt. Anmodet: 1 domæne (~70 DKK, forhåndsgodkendt).
