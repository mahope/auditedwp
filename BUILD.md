# BUILD — Shortest Path to First Paying Customer

**Dato:** 2026-08-24 (iteration 60)
**Status:** Bygger videre. Holder beslutning. Blokeret på Mads' konti.

---

## Korteste vej til $1 (samlet set: ~10 min Mads' tid)

```
Mads opretter Gumroad-konto (10 min)
    → Jeg linker checkout-knapper til Gumroad-products
    → Deploy (1 min)
    → Første køb muligt samme dag
```

**Hvad skal Mads gøre:**
1. Gå til gumroad.com → "Start selling" → email + password → verified
2. Jeg sender ham EXACT product-opsætning (tekst, priser, filer) — klar til at paste
3. Han kopierer links til mig → jeg sætter dem ind på /pro/ og /store/ → deploy

**Alt andet kræver mere tid eller Mads' indblanding.**

---

## Hvad jeg kan bygge OG levere (uden Mads)

Ingen betaling betyder: ingen revenue. Men det betyder IKKE ingen værdi. Her er hvad jeg bygger nu:

### Prioritet 1: Conversion — det der står mellem besøgende og betaling
- [x] **/pro/ page** — Dedikeret salgsside for EUComply Pro ($79/yr). Hvad Pro giver ekstra, hvem det er til, prissammenligning, CTA til waitlist
- [ ] **/store/ → faktisk checkout** — Venter på Gumroad-links
- [ ] **Free vs Pro comparison table** — Inkluderet i /pro/
- [ ] **Mobile gennemgang af købsrejse** — Skal testes

### Prioritet 2: Produktet — flere checks = bedre værdi
- [ ] **Security.txt / DMARC check** — For virksomheder der skal overholde DORA
- [ ] **CSP (Content-Security-Policy) analysis** — Reel sikkerhedscheck

### Prioritet 3: Trafik — SEO-indhold
- [x] Blog post: "DORA vs NIS2 vs GDPR — What's the Difference?"
- [ ] Blog post: "How to Write a GDPR Privacy Policy for Your Website"
- [ ] Blog post: "EU Compliance Cost Calculator" (interaktiv → ville drive backlinks)
- [ ] Update sitemap — live

### Prioritet 4: Bredden
- [ ] npm package ready (code exists, needs package.json + README)
- [ ] Chrome Extension ready to publish (code exists, needs CWS account)

---

## Målepunkter

| Mål | Måling | Nuværende status |
|-----|--------|------------------|
| Scanner bruger | curl tæller | 0 (ingen analytics) |
| Waitlist emails | waitlist Worker DB | 0 (ingen traffic) |
| Blog indexering | Google search console | 0 (ingen domain) |
| $1 revenue | Gumroad | Venter på Mads |

---

## Hvad kan slå det ihjel

1. **Mads opretter aldrig Gumroad** → Ingen revenue. Produkter eksisterer, men ingen kan betale.
2. **Konkurrent bygger bedre free scanner** → Bevares, men markedet er kæmpestort. Compliance er ikke et prisfølsomt køb.
3. **Ingen organisk trafik** → Compliance-Keywords er konkurrenceprægede. SEO tager tid.

---

## Byggeplan (næste iteration)

1. Flere SEO blog posts (target: "privacy policy generator", "gdpr compliance checklist free")
2. Forbedre /pro/ CTA og mobile visning
3. Gennemgå alle sider for konsistent branding og navigation