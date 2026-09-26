# EUComply-pluginen: elleve tjek i stedet for seks

Skrevet 26. september 2026, som spec til opgave 43 i `IMPLEMENTATION_PLAN.md`.
Bygget og udgivet som plugin **1.3.11** i samme iteration.

## Problemet

En kunde scannerer sin side på `eucomplypro.com/scan/` og ser **ni** tjek. Den
samme kunde installerer pluginen og ser **seks**. Pro er prisset som *mere*, og
rapporten kunden sender videre til sin egen kunde er den samme vare. Det var det
eneste sted i hele produktet, hvor det betalte produkt lignede det gratis mindre.

De to lister er heller ikke en fejl i optællingen — de er to forskellige
definitioner af, hvad et tjek er:

| | tjek |
|---|---|
| pluginens `run_checks()` før 1.3.11 | `ssl`, `cookies`, `forms`, **`backups`**, **`plugins`**, `legal` |
| den universelle motor | `ssl`, `cookies`, `forms`, `legal`, `headers`, `consent_mode_v2`, `tcf`, `trackers`, `dora` |

`backups` og `plugins` er WordPress-fakta, som intet andet af vores produkter har,
og de er ikke på den universelle ni. Fem af den universelle ni mangler i
pluginen.

## Beslutningen: elleve, ikke ni og ikke ti

Planen stillede spørgsmålet om de ni skulle blive *de ni* (og `backups`/`plugins`
flytte til en bonus-sektion), eller om pluginen skulle få seks + fem = ti.

**Svar: elleve.** Alle ni universelle tjek kører, og de to WordPress-fakta bevares.

Begrundelsen er den samme som for den permanente tællings-gate fra opgave 42: en
for lav tælling under-sælger en betalt funktion lige så falsk som en for høj. At
fjerne to tjek, der kun findes her, for at få et pænt tal ville være at slette
funktioner for at ligne det gratis produkt. Rapporten en kunde sender sin kunde
er en superset — den kan kun bevise *mere*, ikke mindre.

## De fem nye tjek

Alle fem er statisk analyse af forsiden og HTTP-headerne, altså præcis det
pluginen kan få med ét `wp_remote_get( home_url() )`:

| tjek | hvad det læser | hvorfor det er et EU-fund |
|---|---|---|
| `consent_mode_v2` | 6 signaturer i HTML'en | Google kræver Consent Mode v2 til ad-personalisering i EEA fra marts 2024 |
| `tcf` | 5 signaturer i HTML'en | TCF er konsentgrundlaget for programmatisk annoncering |
| `trackers` | 12 trackersignaturer + 20 CMP-signaturer | ePrivacy/art. 6: trackere må ikke sættes før samtykke |
| `headers` | CSP, `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options` | Manglende ramme-attribut er en dokumenteret EAA-byrde |
| `dora` | 9 tekstsignaturer | Sideoffentlig information om failover og incident response |

**Signaturerne er portet fra `eucomply-scanner/engine/index.js`, ikke genskrevet.**
Det er hele pointen: et tjek med samme navn skal betyde det samme i begge
produkter, ellers begynder de to produkter at være uenige om én hjemmeside.

## Beslutninger der er låst i koden

1. **Én hentning per scanning.** Alle fem læser samme respons. Uden cache ville
   hver scanning lave fem identiske requests — inklusive den daglige Pro-scanning.
2. **Body'en er capped** (`limit_response_size`, 512 KB). En scanning der læser
   et ubegrænset svar er måden et plugin bliver et hukommelsesproblem på det site
   det skal beskytte.
3. **Målet er ikke brugerinput.** Det er `home_url()` fra sitets egne indstillinger,
   så der er ingen adresse at blive narret til at hente, og ingen SSRF-afgørelse
   at træffe. Det er eksplicit skrevet i docblocken, fordi næste agent ellers må
   undersøge det hver gang.
4. **En side der ikke kan læses er aldrig et bestået tjek.** `unreadable()`
   returnerer `warn` med grunden i teksten. "Ingen trackere fundet" fordi hentningen
   fejlede er det værste et compliance-værktøj kan gøre.
5. **Advarsler tælles ikke som beståede.** Det var allerede sandt for rapporten
   (`build_report()`), og de nye checks har alle tre tilstande, så det gælder
   dem fra første scanning.

## Hvad der krævede en ændring uden for pluginen

- Fire `/pro/`-sider i fire sprog skrev *"hvert af de seks"* i den række, der
  beskriver Pro-historikken. De siger nu elleve. Det er ikke en
  copy-justering: `plugin_check_count_findings()` læser antallet *ud af
  `run_checks()`* og er rød i begge retninger, så denne diff ville være stoppet
  af porten hvis copyen ikke var fulgt med.
- `site/plugin/index.html` sagde *"runs six WordPress-specific checks ... not
  identical with, the nine URL checks"*. Den er nu *"the same nine URL checks
  plus two WordPress-specific ones"*, hvilket er det der nu er sandt.
- Plugin-header, `readme.txt`, begge `update.json` og `_redirects` er på 1.3.11,
  og den gamle zip er fjernet fra deploy-træet.

## Hvad der bevidst ikke er gjort

- **Ikke de ni.** `backups` og `plugins` er ikke flyttet væk. Se beslutningen.
- **Ikke PDF.** Rapporten er stadig redigerbar HTML, som den har været siden 1.3.1.
- **Ikke et live-badge.** Det kræver en worker-deploy (spørgsmål 9).
- **Ikke browseradfærd.** Ingen af de fem tjek kører JavaScript, så et site der
  først sætter Consent Mode v2 efter samtykke rapportéres som manglende. Det er
  samme ærlige begrænsning som den universelle scanner har, og den står i
  `detail`-teksten.
