# STATUS — 25. august 2026 — Iteration 279

## Kort version

**0 betalende kunder · $0 revenue · 0 rigtige brugere · Checkout-flip-pipeline verificeret end-to-end**

## Universalitets-vurdering (punkt 1) — genbekræftet

Scanner-kernen (`shared/scan-engine.js`) tager en almindelig URL og er
CMS-uafhængig. Indpakninger: web-UI, API-worker, CLI, WordPress-plugin,
Chrome-extension. BESTÅET — ingen handling.

## Denne iteration: betalingspipeline afprøvet med rigtige kald

Før LS-nøglen lander har jeg verificeret at **hele flip-mekanismen virker**,
så `ls-setup-all.sh` bare kan køres når nøglen kommer:

1. **CF API-token KAN skrive worker-secrets** — ikke via `/secrets`
   endpointet ("Method not allowed for this authentication scheme"), men via
   `PATCH .../settings` med multipart bindings. Det er testet med en
   placeholder-checkout på alle tre workers: sæt → /config viser URL →
   revert til tom. Virker.
2. **To reelle fejl fundet og rettet:**
   - `devnotify-metrics` læste `env.CHECKOUT_URL`, men bindingen hed
     `CHECKOUT_URL_PROBE` → DevNotify-checkout kunne ALDRIG være flippet.
   - `waitlist-eucomply` (QuickFormat) havde slet ingen CHECKOUT_URL-binding.
   Begge fik korrekt binding. Resterende probe-secrets slettet.
3. **`ls-setup-all.sh` omskrevet** til den virkende PATCH-metode (den gamle
   brugte det blokerede /secrets-endpoint og ville fejlet ved første kørsel).
4. Alle tre workers deployet med `.trim()` af CHECKOUT_URL (beskytter mod
   whitespace i secret). Verificeret live: alle /config svarer korrekt tom.

Konklusion: den dag LS-nøglen ligger i Bitwarden, er én kommando
(`LEMONSQUEEZY_API_KEY=... ./scripts/ls-setup-all.sh`) nok til at alle fire
produkter kan tage imod betaling.

## Domæne-status (nye fund)

- Tokenet har **Registrar + Pages + Workers + KV**, men **ikke DNS-write**
  (verificeret med konkrete 10000-fejl fra DNS endpoints).
- Custom domains `eucomplypro.com` og `www.eucomplypro.com` er tilføjet til
  Pages-projektet af mig (www via API; apex var allerede registreret).
  Status: *pending* — venter udelukkende på CNAME-recorden:
  `@ og www -> auditedwp.pages.dev (proxied)`.

## Blokeret (én linje hver)

- LS API key i Bitwarden → kræver Mads' unlock (desktop-appen kan ikke låses op programmatisk).
- npm-login til publish af eucomply-scanner v1.0.0.
- CNAME @/www på eucomplypro.com → token mangler DNS-write; Mads skal oprette den (2 min i dashboardet).

## Næste skridt

1. CNAME fra Mads → domænet går live automatisk (Pages-domænerne er allerede tilknyttet).
2. LS-nøglen → kør `ls-setup-all.sh` → checkout live samme minut.
3. Efter lancering: mål gratis-scan → pro-konversion via worker-/stats.
