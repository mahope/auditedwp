# BUILD.md — EUComply WordPress Plugin

## Korteste vej til første betalende kunde

```
TRIN V     TID       UDEN MADS?     AFTALE
─── ─────── ───────── ────────────── ─────────────────────
 1  Landingsside  1 dag    ✅ Ja   Cloudflare Pages
 2  Plugin Free    2 dage   ✅ Ja   PHP, klar til zip
 3  Plugin Pro     1 dag    ✅ Ja   Kode klar
 4  wp.org-submit  1 time   ❌     Kræver Mads-konto
 5  Første kunde   1-3 mdr  ✅     Organisk på wp.org
 6  Penge          1 dag    ❌     Kræver Strihe/betalingsløsning
```

## Hvad jeg bygger (i denne rækkefølge)

### Trin 1: Landingsside (nu)
- `site/plugin/index.html` — salgsside: hvad det gør, hvem det er til, priser (Free vs Pro $79/år)
- `site/plugin/features.html` — feature-detaljer
- Link fra ComplianceDocs store-side til plugin-siden
- Hostes på `eucomply.pages.dev` / Cloudflare Pages

### Trin 2: Plugin Free-version
- PHP-plugin til WordPress
- Scanner: SSL-certifikat, GDPR-formular-tjek, cookie-banner-tjek, backup-alder, WP-version
- Admin dashboard i WordPress med resultater
- Enkelt: en klasse, en admin-side, 5 simple checks

### Trin 3: Plugin Pro-version
- DPA-generator (bruger ComplianceDocs DPA-template som output)
- NIS2 vendor clause kit
- EAA statement generator 
- Kvartalsrapport (PDF via mPDF/tcpdf eller simplere: HTML)
- E-mail-notifikation

### Trin 4: Betalingskanal
- Stripe hosted checkout link (ingen Stripe-konto på mit site)
- Eller: sell Pro via Gumroad (samme konto som ComplianceDocs)
- (kræver Mads' godkendelse — én af delene)

## Hvad jeg IKKE bygger endnu
- CRM — håndteres manuelt de første 20 kunder
- WooCommerce-integration — senere
- Multisite-support — version 2
- Flere sprog — version 2

## Ressourcer
- Cloudflare Pages: gratis (site + landing pages)
- wp.org-listing: gratis
- PHP: ingen dependencies, vanilla PHP
- PDF: tcpdf (free, MIT) — kun til Pro
- Git: site/ mappen er allerede et repo