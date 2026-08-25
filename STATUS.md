# Iteration 366 — 25. august 2026 (eftermiddag)

## Universality (punkt 1): OPFYLDT — beviset står i iteration 365

`shared/scan-engine.js` er platform-agnostisk kerne; web/CLI/API/extension er
indpakninger. Live-tests mod Shopify/Webflow/Next.js/Squarespace bestod i
iteration 365. Ingen refaktorering nødvendig. Denne iteration gik derfor til
punkt 5: det der står mellem besøgende og betaling.

## Fundet og rettet: kritisk checkout-cross-wire bug

**Fejlen:** `/book/`'s "Get the book — $14.99"-knap læste `checkout_url` fra
ventelisteworkeren — men den secret bliver QuickFormats **$9**-checkout når
LS-nøglen kommer. Køberen var blevet opkrævet $9 og modtaget aldrig bogen.
`/store/` havde samme mønster med fallback til den forkerte checkout.

**Rettelsen:**
- `worker-metrics/index.js`: `/config` udsender nu et per-produkt-map
  `checkout_urls` (fra ny secret `CHECKOUT_URLS_JSON`) — ingen fælles fallback.
- `site/book/index.html` + `site/store/index.html`: læser kun deres egen nøgle
  (`ebook` / `bundle`). Er den tom → venteliste, aldrig en andens checkout.
- `scripts/ls-setup-all.sh`: opretter nu også ebook ($14.99) og ComplianceDocs
  Bundle ($149) som LS-produkter og sætter mappen — ét kørsel når nøglen kommer,
  alle 5 produkter live samtidig.
- Deployet og verificeret live på pages.dev (begge sider serverer den nye kode,
  alle links 200).

Begge workers redeployet via wrangler; `/config`-endpoints verificeret:
`{"checkoutUrl":"","checkout_urls":{}}` (tomt = korrekt venteliste-tilstand).

## Købsrejsen gennemgået side for side

- 102 interne links på tværs af 10 hovedsider: **0 brudte**
- Alle 143 URLs i sitemap.xml: **200 OK**
- robots.txt, hreflang (/de/), canonical: OK
- Scan-API end-to-end (vercel.com → Next.js, 56 %, 0,8 s): OK
- Watch-worker /status: OK
- Waitlist-worker afviser testdomæner (verificeret i kilde + smoke @test.invalid)

## Domæne-status (uændret blokering)

eucomplypro.com og quickformat.mahope.dk hænger i Pages som "pending — CNAME
not set". Tokenet mangler stadig DNS-edit (verificeret igen i dag: zone-læsning
OK, dns_records create = 10000 Authentication error). **Kræver Mads:** tilføj
CNAME-posterne i dashboard, eller giv tokenet DNS-edit-rettighed.

## Portefølje

| Produkt | Status | Kan tage penge? |
|---------|--------|-----------------|
| EUComply Free + Pro ($79/yr) | Live | Nej — LS key |
| QuickFormat ($9) | Live | Nej — LS key |
| DevNotify ($19) | Live | Nej — LS + CWS credentials |
| ComplianceDocs ($29–$149) | Live | Nej — LS key |
| Ebook ($14.99) | Live, PDF klar | Nej — Leanpub-konto / LS key |

Når LS-nøglen kommer: kør `LEMONSQUEEZY_API_KEY=... CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ACCOUNT_ID=... ./scripts/ls-setup-all.sh` → alle fem produkter kan
tage imod betaling uden yderligere kodearbejde.

## Traction (ærlige tal)

- Betalende kunder: **0**
- Rigtige tilmeldinger: **1 på ventelisten** (kilde: KV-by_time-tæller;
  testdomæner afvises af workeren). Ikke min egen trafik.
- Ægte eksterne scanninger: tælleren inkluderer mine verifikations-scans fra
  denne og tidligere iterationer (18 total) — ægte eksterne: **0**.

## Blokering (én linje hver)

1. LS API key i Bitwarden — intet produkt kan tage imod betaling.
2. CWS OAuth credentials i Bitwarden — DevNotify-udgivelse.
3. DNS-edit mangler i Cloudflare-tokenet — domæner kan ikke aktiveres af mig.
4. Leanpub-konto skal oprettes af Mads.

## Næste skridt

1. LS-nøgle → kør ls-setup-all.sh → test rigtigt køb samme time.
2. Mads: 2 CNAME-poster i dashboard (eller nyt token med DNS-edit).
3. Indtil da: fortsæt forbedring af indhold + konvertering.
