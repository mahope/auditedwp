# RESEARCH — QuickFormat: Mac menu bar format converter (24. august 2026)

## Præmis

EUComply og DevNotify er blokeret på LS API key i Bitwarden (unauthenticated).
Mads' mandat: "Er du blokeret, start noget nyt."

## Produktidé: QuickFormat

**Hvad:** En Mac menu bar app til instant format-konvertering (JSON, YAML, CSV, TOML, XML).

**Hvorfor markedet virker:**
- Mac menu bar utilities er et beboet marked med bevist betalingsvilje:
  - Bartender: $20 one-time (menu bar organizer)
  - Dato: $16 one-time (kalender i menu bar)
  - Hand Mirror: $7 one-time (kamera-tjek)
  - iStat Menus: $12 one-time (system monitor)
  - Paste: $14.99 one-time (clipboard manager)
  - Super.dev: $15/mo subscription (format conversion — proof at folk betaler)
- Format conversion er en daglig opgave for udviklere, data-analytikere, API-brugere
- Gratis web-værktøjer findes (jsonlint.com, codebeautify.org) — men DE har reklamer, uploader data, og kræver browser

**Hvorfor QuickFormat skiller sig ud:**
- Menu bar → altid tilgængelig uden at åbne en browser
- Offline → ingen data sendt nogen steder (APIs keys, secrets)
- Global shortcut → select text, convert, paste — 2 sekunder
- CLI inkluderet → scripting og automation

**Pris:** $9 one-time (LS, Lemon Squeezy MoR). Gratis web-version på /tools/format/ driver SEO.

## Konkurrenter

| Produkt | Pris | Format support | Offline | Menu bar |
|---------|------|---------------|---------|---------|
| Super.dev | $15/mo | JSON/YAML/CSV/TOML | ✅ desktop | ✅ Raycast |
| jsonlint.com | Free | JSON only | ❌ | ❌ |
| codebeautify.org | Free (ads) | Fler | ❌ | ❌ |
| Online JSON Viewer | Free | JSON only | ❌ | ❌ |
| **QuickFormat** | **$9 once** | **Alle 5** | **✅** | **✅** |

## Bygget i denne iteration

1. `quickconvert/src/engine.js` — Universel format conversion engine (JSON, YAML, CSV, TOML, XML)
2. `quickconvert/bin/quick-format.js` — CLI-værktøj (`qf`) — testet og virker
3. `site/quickconvert/index.html` — Produktpage for desktop app ($9)
4. `site/tools/format/index.html` — Web version (free, SEO, browser-based conversion)
5. Alle live på https://auditedwp.pages.dev/quickconvert/ og /tools/format/

## Fremtidig research (når LS key kommer)

- Tauri desktop app — byg native menubar app med Rust
- VS Code extension wrapper
- `npm publish quick-format` — CLI distribution
- Analytics på web tool (hvor mange bruger det? konvertering til desktop?)
## 24/8-2026 (iteration 258): Complianz + Usercentrics research til /vs/-sider

- **Complianz:** WordPress-only privacy suite, 1M+ installs. Personal €59/år (1 site),
  Professional €179/år (5 sites), Agency €399/år (25 sites); Multisite kræver Agency.
  Kilder: complianz.io/pricing, complianz.io/complianz-pricing-faqs,
  cookiebannerguide.com/complianz-pricing (hentet 24/8-2026).
  → Stærkest universality-vinkel: produktet kan ikke køre udenfor WordPress overhovedet.
- **Usercentrics (Cookiebots ejer):** self-serve Pro ~$34/md (3 domæner), Business ~$56/md
  (10 domæner), custom CSS først på Business. G2-topklage = opsætningssværhed (20 nævnelser);
  session-baserede auto-upgrades uden nedgradering; "pricing too high for SMEs" er tilbagevendende.
  Kilder: consently.net/blog/cookiebot-vs-usercentrics, g2.com, trustpilot.com (24/8-2026).
