# ComplianceDocs — Overgang fra Gumroad til Lemon Squeezy (24. august 2026)

Gumroad er droppet (Mads har ingen konto, og API'en kan reelt ikke skrive).
Mads HAR en Lemon Squeezy-konto (`mads@mahope.dk`). Denne guide erstatter
`gumroad/UPLOAD-GUIDE.md`. Produkterne er uændrede — kun kanalen skifter.

## Hvorfor LS er bedre end Gumroad
- Merchant of Record: EU-moms + US sales tax afregnes af LS.
- ~92 % payout mod Gumaroads ~87 %.
- Fuld skrive-API → produktet oprettes af agenten via kode, ikke manuelt.

## Plan A — automatisk via LS API (når "Lemon Squeezy API Key" ligger i Bitwarden)

Digital downloads i LS kræver først et **store**-objekt med filer; filer uploades
via `POST /v1/files` (base64 eller URL). Produkt + variant oprettes herefter som
i hovedplanen i `BUILD.md`.

Priser (uændrede fra Gumroad-planen):

| Fil (gumroad/products/) | Produktnavn | Pris |
|---|---|---|
| dpa-template.pdf | GDPR Data Processing Agreement (Art. 28) | $59 |
| nis2-vendor-clauses.pdf | NIS2 / DORA Vendor Clause Set | $49 |
| nda-clause-set.pdf | Mutual NDA Clause Set | $29 |
| eaa-statement-template.pdf | EAA Accessibility Statement Template | $39 |
| reportkit.zip (3 filer) | Client Compliance Report Kit | $69 |
| bundle (alle 6) | The Complete Bundle (+12 mdr. updates) | $149 |

Produktbeskrivelser: genbrug de færdige tekster i `gumroad/UPLOAD-GUIDE.md`
(afsnit "Ready-to-paste product description").

Efter oprettelse:
1. Sæt checkout-links ind i `site/store/index.html` (erstatt "Checkout opens
   soon"-banneret).
2. Deploy: `./deploy.sh site`.
3. Sandbox-test med kort 4242 4242 4242 4242.

## Plan B — manuel fallback (Mads, ~20 min i LS-dashboardet)

1. Log ind på app.lemonsqueezy.com med `mads@mahope.dk`.
2. Products → New product, én pr. række i tabellen ovenfor.
3. Upload PDF fra `gumroad/products/`, indsæt titel/besked/pris.
4. Publicér → kopier checkout-URL'erne → send dem til agenten (eller læg dem i
   Bitwarden-noten "LS checkout URLs"), så sættes de ind på /store/ og deployes.

## Efter lancering
- Fjern waitlist-banneret på /store/.
- Kør et sandbox-køb, verificer leveringsmailen indeholder PDF'en.
- Første rigtige betaling = mål #1.
