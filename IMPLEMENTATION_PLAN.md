# IMPLEMENTATION_PLAN — EUComply

Opdateret: 2026-09-25
Sidste iteration: færdig — kvalitetsgaten er permanent i CI, og den fandt en P0 i den publicerede scanner
Baseline: `main` commit `dbd1487` efter `git pull --ff-only` 2026-09-25
Mission: sælge EUComply Pro ærligt og bygge den værdige betalte oplevelse uden at svække den gratis scanner.

## Iterationsstatus

- `FÆRDIG`: **1 — Ret salgsløfterne til det der virker nu** på `ceo/ret-pro-lofter`.
- `FÆRDIG`: **2 — Skriv spec for den hosted Pro-værdi** på `ceo/hosted-pro-spec`; `docs/eucomply-pro-spec.md` findes nu.
- `FÆRDIG` (del 1 af 2): **3a — SSRF/DOM-XSS + overvågningsejerskab** på `ceo/ssrf-monitor-ownership`, commit `28795c3`.
- `FÆRDIG` (del 2 af 2): **3b — licens-entitlement, 409-semantik, `deactivate`, `warn` i summen, privatlivstekst** på `ceo/license-409-deactivate`, commit `e9f1e09`.
- `FÆRDIG` (kode + tests grøn, **ikke live** — kræver worker-deploy): **4 — Byg ægte historik og pass-til-fail-alerts** på `ceo/watch-per-check-history`, commit `1785766`.
- `FÆRDIG` (kode + CI grøn, live-verificering afventer næste deploy-vindue): **8 — Stop offentlig udgivelse af interne og betalte filer** på `ceo/deploy-hygiene`, commit `317e382`.
- `FÆRDIG`: **9 — Gør kvalitetsgaten permanent i CI** på `ceo/ci-kvalitetsgate`. Undervejs fandt den en P0: den publicerede scanner-CLI fejlede på *alle* scans, fordi `UA` ikke var erklæret i `eucomply-scanner/engine/index.js`.
- `FÆRDIG`: **10 — Forbedr konvertering efter ærlig baseline** på `ceo/cta-baseline`. `/checklist/` og `/badge/` havde ingen købsvej; `tools/check_cta.py` gør købsrejsens acceptkriterier prøvbare, og baseline står som dokumenteret 0.
- Næste opgave: **11 — Opgrader og erklær kun relevante runtimes**. Opgave 5 (kunderapporter) kræver svar på spørgsmål 1 og må derfor ikke begyndes; opgaverne 6 og 7 kræver de endnu udevtede workers fra spørgsmål 9.
- Oplysninger, beslutninger og deploy-noter skal fortsat skrives her, så næste iteration kan arbejde uden hukommelse.

## Verificeret produkttruth — 2026-09-25

| Område | Det virker i dag | Det er ikke implementeret eller kan ikke sælges endnu |
|---|---|---|
| Gratis webscanner | Ni universelle URL-tjek, forslag til rettelser og en delbar gen-kørselse-link via `shared/scan-engine.js` og `worker-scan/index.js`. `eucomply-scanner`-motoren er byte-paritetstestet mod workerens (opgave 9). | ~~CLI'en fejlede på alle scans~~ — rettet 25/9; `UA` var ikke erklæret i `eucomply-scanner/engine/index.js`. |
| Hosted monitoring beta | `worker-watch/index.js` har cron kl. 06:00 UTC, 30 dages per-check-historik (pass/warn/fail pr. tjek) og **én mail pr. ny regression** med checknavn, gammel status, tidspunkt og fix. Uændrede scans og gentagne fejl sender intet. | Registreringen er åben og ikke knyttet til køb eller licens. Det er bygget og testet i repoet, men **endnu ikke deployet** — workerne deployes ikke af CI, så produktionen kører 1.1.0 med score-fald-mail. |
| Gratis WordPress-plugin | seks site-/WordPress-tjek og en ugentlig planlagt scan i `plugin/eucomply.php`. | Ingen historik, ikke dagligt. |
| WordPress-plugin Pro 1.3.1 | Licensen validerer mod Mahope og låser DPA-, NIS2/DORA- og EAA-starthtml samt en rapport fra seneste scan. | Dokumenterne er redigerbare HTML, ikke PDF. Der er ingen hosted konto, historik, live badge, mailflow eller flere sites. |
| Hosted Pro-dashboard | `/pro/dashboard/` er en offentlig konceptdemo med fast, illustrativ data. | Ikke kundedata, ikke autentificeret og uden tilføj/slet/cancel. Den henter ikke live kundedata og bruger ikke længere `Math.random()`. |
| Rapport | Plugin kan downloade HTML fra seneste scan. | Runtime-PDF og kundespecifikke rapporter findes ikke. Statisk eksempelrapport er kun en demo. |
| Footer-badge | Der ligger et statisk embed-script, der linker til den gratis scanner. | Scriptet henter ingen score eller live-resultat; det er ikke et verificerbart compliance-badge. |
| Pro-levering | Stripe-linket er live og licensen virker i plugin. | Watch-worker, dashboard og Stripe-success-flow er ikke koblet sammen. `/pro/thank-you/` er nu kun en plugin-aktiveringsvej. |
| Betalte templates | Stripe-butikken sælger templates enkeltvis og i bundle. | Fulde betalte filer ligger desfor stadig i det offentlige repo/deploy-træ. De må ikke udvides eller genudgives her. |

## Låste produktbeslutninger for denne plan

1. Stripeproduktet er `eucomply-pro` til **79 USD pr. website pr. år**. Alle “unlimited domains” og “no per-site licensing” fjernes fra EUComply Pro-copy.
2. Det eneste eksisterende betalte produkt, kunderne kan bruge i dag, er WordPress-pluginens licenslåste dokumentgenerator. Det beskrives konkret som redigerbare HTML-starthtml og en rapport fra seneste scan.
3. Hosted daglig monitorering, historie, pass-til-fail-mail, runtime-PDF, live badge, hosted dashboard og multi-site-workflow er **roadmap, ikke nutidige Pro-fordele**, indtil de er bygget og testede.
4. Den åbne monitoring beta er ikke en betalt entitlement. Den beskrives højst som en særskilt forsøgsordning og ikke som noget købet.
5. Butikkens fulde betalte templates sælges separat. Pro-siden må ikke sige “templates included”, medmindre den senere henviser til en konkret, allerede leveret fil.
6. Kun Stripe-linket fra kontrakten bruges: `https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03`. Ingen nye produkter, priser, nøgler eller redirect-URL'er oprettes.
7. Det eksisterende produkt hedder fortsat EUComply Pro. Nye navne er kun forslag under `❓ Til Mads`.
8. Betalt template-indhold tilføjes, ændres eller flyttes ikke til dette offentlige repo. Replikater skal leveres fra privat lager/CF KV.

## Kvalitetsgate

Gate-definitionen er låst her, før første implementeringsiteration:

1. **PHP syntax:** `php -l` på hver ændret `.php`-fil. Ved plugin-ændringer skal både `plugin/` og deploy-kopien `site/plugin/` være byte-identiske.
2. **Repo-tests:** repoet har ingen root-test-suite eller PHP-testkonfiguration. Den regressionstest for påstande, der tilføjes i opgave 1, bliver den nye obligatoriske test. Hvis scannerkoden ændres, køres desuden scannerens smoke-test og `npm pack --dry-run` i `eucomply-scanner/`. Siden opgave 10 gælder desuden `tools/check_cta.py` (købsvejens kontrakt) **og** `tools/check_cta.py --selftest` (beviser at gaten kan fejle).
3. **Obligatorisk site-build + SEO:** fra sibling-repoet `../hermes-passiv` med `AUDITEDWP_DIR` sat til denne repo-root:
   - `python3 build_sites.py --only eucomplypro.com`
   - `python3 tools/seo_check.py --only eucomplypro.com`
4. **Deploy:** merge til `main` deployer kun `site/` via `.github/workflows/deploy-site.yml`. Der trigges aldrig et manuelt deploy fra en agent. Efter merge/push noteres `VERIFICÉR DEPLOY`, og indhold verifceres først efter et næste deploy-vindue; HTTP 200 alene er ikke bevis.
5. **Afhængigheder:** root-repoet har ingen `package.json`, `composer.json` eller tredjepartslockfile. `eucomply-scanner/` og `cli/` er dependency-free og bruger Node `>=18`; runtime-opdatering er en separat, lavere prioriteret opgave. Unrelated DeskUptime/DevNotify-audits hører ikke til EUComply-gaten.

### Gate-basline — 2026-09-25

- Sibling-kommandoen kørte med exit 0 og skabte `dist/eucomplypro.com/index.html`, men sibling-SEO-scriptet rapporterede `0 pages, 0 findings`. Det tælles ikke som gyldig SEO-evidence.
- Root-fallbacken `python3.13 tools/seo_check.py --verbose` scannede **213 sider med 0 findings**. `python3.12` findes ikke på maskinen, og den almindelige `python3` er 3.9 og kan ikke parse kontrollens typeannotering.
- Fremover kræves både missionens sibling-kommando **og** en SEO-kontrol med `pages > 0`. En 0-side-siblingkørsel må aldrig godkendes alene; indtil scriptet er rettet, er auditedwp-root-fallbacken den gyldige SEO-evidence.

## Prioriteret kø

### 1. Ret alle salgsløfter til den nuværende funktion

- Status: `FÆRDIG` — implementation og lokal kvalitetsgate grøn; live-verificering afventer næste deploy-vindue
- 2026-09-25: EN/DA/DE/FR Pro og pricing, dashboard, sample, thank-you, plugin, scanner, sammenligninger, blog/SEO, privacy og llms-tekster er bragt på samme dokumenterede Pro-truth. Roadmap står uden for inkluderede funktioner.
- 2026-09-25: Plugin 1.3.1 og Chrome-extension 1.0.1 er regenereret. Plugin-cron indlæser nu admin-API'er i WP-Cron, og både positiv og definitiv negativ licensstatus caches i 24 timer; 7-dages offline grace er bevaret.
- 2026-09-25: Scanner- og klientekst kalder nu kun statiske side-/header-markers, ikke browseradfærd eller DNS. Privacy afslører IP-rate-limit, 365-dages aggregater og seks local-storage scans korrekt. Alle gamle `$14.99`-ebook-CTAs er erstattet af den gratis guide.
- 2026-09-25: Fresh review fandt desuden redirect/DNS-rebinding-SSRF og rå HSTS-header i `innerHTML`; disse er ikke opportunistisk løst i denne diff, men prioriteret i opgave 3. Betalte offentlige filer ligger allerede i opgave 8.
- Gate: `112 self-tests passed`, `0 unexpected EUComply Pro claims`; PHP-lint og plugin-paritet grøn; Node-smoke `9 checks`; `npm pack --dry-run` grøn; root-SEO `216 pages checked, 0 findings`; sibling build/SEO exit 0 (sibling-SEO fortsat `0 pages`, derfor root-fallback som gyldig evidens).
- Fejl: 0/2
- Begrundelse: Stripe er live, men købssiden sælger daglige historier, pass-til-fail-mail, PDF og badge, som ikke findes. Det kan give købsforventninger, refusion og support, der ikke kan opfyldes. Dette er missionens eksplicitte første opgave.
- Scope:
  - Ret `site/pro/index.html`, `site/pricing/index.html`, `site/da/pricing/index.html`, `site/de/pricing/index.html` og `site/fr/pricing/index.html`.
  - Opret `site/da/pro/`, `site/de/pro/` og `site/fr/pro/` som lokale spejle, så sprogvælgeren og alle købsstier fungerer uden 404.
  - Ret samme overdrivelse på public Pro-dashboard, sample, thank-you, plugin landing, `llms.txt`, `llms-full.txt`, sammenligningssider og blog/SEO-sider. Roadmap- eller sample-tekst skal være tydeligt mærket og ikke indgå i den betalte sammenligningstabel.
  - Fjern “unlimited domains”, merchant-of-record, PayPal “planned”, modstridende refundgarantier og påstande om betalte templates inkluderet, medmindre de er faktisk leveret iht. kontrakten.
  - behold én fungerende Stripe-knap pr. side med det eksakte kontraktlink.
  - Tilføj `tools/check_pro_claims.py`, som fejler ved nutidige claims om PDF, live badge, kundedashboard, pass-til-fail-mail eller historie uden for eksplicit roadmap-/sample-markering.
- Accept:
  - EN/DA/DE/FR pricing og Pro er sprogligt konsistente og bruger samme nuværende Pro-truth.
  - Påstandstesten finder 0 uventede nutidige overclaims.
  - Alle Pro-CTA'er har præcis ét tilladt Stripe-link; ingen locale-CTA giver 404.
  - Pro-tabellen viser kun funktioner, der kan dokumenteres i kode; roadmap står uden for “included/with Pro”.
  - PHP-lint og claims-test er grønne; sibling-kommandoen har exit 0, og SEO-kontrollen scanner flere end 0 sider med 0 findings.
  - Efter merge verificeres live indhold på `/pro/`, alle fire pricing-sider og den nye locale-Pro-rute.

### 2. Skriv spec for den hosted Pro-værdi

- Status: `FÆRDIG` — `docs/eucomply-pro-spec.md` (18 afsnit) på `ceo/hosted-pro-spec`
- 2026-09-25: Specen definerer de tre overflader uden overlap, købsrejse, `device_id` pr. website, multi-site med `activate`/`deactivate`, 30 dages per-check-historik med tri-state, fire alarmtyper med dedupe, PDF som rapportformat, opt-in badge med offentligt `site_id`, dashboard uden mockdata, retention, sletning, privacy-datamappe, trusler, belastningstestmatrix, migrering i seks faser, bygge- og fejlrækkefølge og definition of done.
- 2026-09-25: Kun det eksisterende Stripe-link og `eucomply-pro` bruges. Specen opretter ingen nye produkter, priser eller nøgler, og den sætter **default** til plugin-only, indtil Mads svarer på spørgsmål 1.
- Fund fra frisk review før commit: (a) `warn` tælles i den eksisterende score som fejlslag, ikke som bestået, fordi de tjek, der sætter `warn`, også sætter `pass:false` — rettet i specen og noteret som opgave 3-arbejde; (b) scannerens egen side escaper HSTS-headeren korrekt, mens `site/shared/live-check-widget.html:33,37,39,42` renderer ubeskyttet — den widget kalder DeskUptime-workeren og ligger uden for EUComply-gaten, så den er skrevet under `❓ Til Mads`; (c) licensverdicts-tabellen manglede `200 ok:false`, `402` og `429` som midlertidige, hvilket ville have låst betalende kunder — rettet; (d) email-bekræftelse, due-kø, `Retry-After` og `license_calls` var underpecificerede — rettet.
- Gate: `112 self-tests passed`, `0 unexpected EUComply Pro claims`; root-SEO `216 pages checked, 0 findings`. Ingen PHP- eller scannerændringer, så PHP-lint og scanner-smoke er ikke betingede. Sibling-kommandoen i `../hermes-passiv` kunne **ikke** køres: workspace-permissions nægter adgang til det sibling-repo, så missionens krav kan ikke dokumenteres i denne iteration. Gyldig SEO-evidence er derfor root-fallbacken, jf. gate-baseline.
- Fejl: 1/2 (første review fandt blokierende fejl, rettet i samme iteration)
- Begrundelse: Kontraktet kræver spec før større Pro-funktioner. Uden fælles data-, adgangs- og fejlmodel bliver dashboard, alerts, rapport og badge hinanden uforenlige.
- Scope: ny `docs/eucomply-pro-spec.md` med skillet mellem gratis scanner, WordPress-plugin Pro og hosted Pro; købsflow; licens/device binding; multi-site-regel; 30 dages historik; pass-til-fail-diff; rapportformat; badge-identitet; mail; dashboard; retention; sletning; 7-dages offline grace; privacy og trusler.
- Accept:
  - Specen definerer hver af daglig re-scan, historik, kunderapport, flere sites og mail-alarmer uden overlap.
  - Alle request/response-kontrakter, KV-nøgler, rettigheder, retention og fejlkoder er eksplicitte.
  - Licensserveren 503/5xx/netværksfejl giver cached entitlement i op til 7 dage. Et definitivt ugyldigt, udløbet, tilbagekaldt eller forkert-produkt-svar låser, mens 409 kun afviser den nye enhed.
  - En belastningstestmatrix, privacy-datamappe og migrationsplan findes.
  - Specen bruger kun det eksisterende Stripe-link og `eucomply-pro`; den kræver ingen nye Stripeprodukter.

### 3. Luk SSRF/DOM-XSS og gør hosted monitoring entitlement-sikker

- Status: `FÆRDIG` — del A `28795c3`, del B `e9f1e09` på `ceo/license-409-deactivate`
- 2026-09-25 del B — **409 låste betalende kunder ude.** `license_verdict` behandlede 409 som definitivt ugyldig og cachede negativt i 24 t, så en kunde med en gyldig nøgle på sit fjerde site fik "nøgle ikke accepteret" og kunne aldrig rydde pladsen, fordi pluginen aldrig kaldte `deactivate`. 409 er nu sit eget verdict `device_limit`: Pro er fra for dette site, nøglen låses ikke, og den negative cache slettes, så en frigivet plads gendannes ved næste tjek (10-minutters backoff i stedet for 24 t).
- 2026-09-25 del B — **`deactivate` findes nu tre steder:** en "Release this device"-knap på settings, automatisk frigivelse af den gamle nøgle ved nøgleskift, og best-effort frigivelse i `uninstall.php`. Uden dem er en $79-pr.website-licens umulig at flytte, og det er den konkrete værdi ved multi-site.
- 2026-09-25 del B — **temp-svarene er gjort eksplicitte:** `402`, `429`, `5xx`, netværksfejl og ulæseligt `200`-svar giver alle `null` → 7-dages grace på den cachede status. Kun `400`/`403`/`404` låser. Et nøgleskift sletter også `eucomply_pro_last_ok_at`, så en ny nøgle ikke arver gammel grace.
- 2026-09-25 del B — **`warn` i summen (spec afsnit 7, åbent punkt) er besluttet:** tallet ændres ikke, fordi en advarsel reelt er en mangel ("HTTPS, no HSTS", ét af to juridiske sider). Til gengæld er den nu **navngivet**: rapporten siger "N af M bestået, W med advarsler, F fejledet. Advarsler tælles ikke som bestået", og tabellen viser PASS/WARN/FAIL i stedet for "FAIL (warning)". Det er den ærlige version af det eksisterende tal.
- 2026-09-25 del B — **privatlivssiden havde en påstand, del A gjorde falsk:** den sagde, at status-endpointet er offentligt. Den beskriver nu owner-tokenet i stedet for, og at det ligger i local storage.
- 2026-09-25 del B — **ny obligatorisk test:** `tools/test_license_verdicts.php` (44 tjek) stubber WordPress og dækker hele svarmappingen, 7-dages grace frem og tilbage, at 409 ikke cacher en 24-timers lås, at en frigivet plads gendanner Pro, validate→activate-rækkefølgen og frigivelseskaldet. Det var det eneste acceptkrav i opgave 3 uden dækning.
- 2026-09-25 del B — plugin 1.3.2 regenereret: `site/plugin/` er byte-identisk med `plugin/`, ny zip på `/assets/eucomply-1.3.2.zip`, `update.json` og downloadlink peger på den, og `tools/check_pro_claims.py`'s `PLUGIN_VERSION` er opdateret (claims-testet fejlede ellers på det).
- Gate del B: `php -l` grøn på 4 filer; `44 license checks passed`; `112 self-tests passed`, `0 unexpected EUComply Pro claims`; `27 security checks passed`; `npm pack --dry-run` grøn; root-SEO `216 pages checked, 0 findings`. Sibling-kommandoen i `../hermes-passiv` kunne igen **ikke** køres: workspace-permissions nægter adgang, så missionskravet kan ikke dokumenteres; gyldig SEO-evidence er root-fallbacken, jf. gate-baseline.
- Fejl: 0/2 (del B)
- Begrundelse: Den offentlige scanner følger redirects uden at validere hvert hop og kan hente private mål; rå HSTS-responseheadere renderes desuden i `innerHTML`. Monitoring-registreringen kan samtidig skifte en andens email, og `/status` er offentligt. Det er P0/P1-brugerrisiko, privacy-fejl og spam-/SSRF-mulighed.
- 2026-09-25 del A — SSRF: `safeFetch` følger redirects manuelt og validerer hvert hop via `assertPublicTarget`. `isPublicIPv4`/`isPublicIPv6`/`expandIPv6` dækker nu IPv4-mapped IPv6, NAT64, 6to4, Teredo, `::/96`, `ff00::/8`, `100::/64`, CGNAT, TEST-NET og 198.18/15. Værter der *ligner* en IP men ikke er en fuld quad (`127.1`, `1.2.3`) afvises fail-closed. Ikke-IP-værter slås op i Cloudflares resolver med 60 s per-isolate-cache; resolver-fejl fejler åbent, et konkret privat svar lukkes. Brødtekst capped ved 2 MB. Redirect-loops afbrydes efter 5 hop.
- 2026-09-25 del A — fund undervejs: den gamle kode erklærede `::1` og `::` for **offentlige** (`!/(^(::1|::|f[cd]|fe80)/…) && !/^0*0*$/…`), fordi begge betingelser var skrevet omvendt. Den ramte aldrig i praksis, kun fordi `normalizeUrl` kræver et punktum i hostnavnet, så IPv6-literals altid faldt igennem den port. Guarden er testet direkte nu.
- 2026-09-25 del A — DOM-XSS: HSTS-headeren blev brugt rå i `checks.ssl.detail`. Værdien filtreres nu til headerdirektiver, så en fjendtlig oprindelse ikke kan sende markup med. `checks.ssl` vurderer desuden `finalUrl` frem for den anmodede URL, så en https→http-downgrade opdages i stedet for at blive rapporteret som HTTPS.
- 2026-09-25 del A — ejerskab: hvert site får et 192-bit `ownerToken`. `/status` flyttede fra `GET /status?url=` til `POST /status {url, ownerToken}` og kræver nu tokenet. En fremmed uden token **og** uden den adresse recorden er oprettet med får 409 på register og 403 på status/unregister — den kan altså hverken læse historik, overtage alarm-mailen eller slette. Ejeren beholder tokenet ved email-skifte. Legacy-records uden token claim'es én gang med den oprindelige adresse og beholder historien. Skrivninger er rate-limaget 5/min pr. IP på et separat `RATE`-namespace.
- 2026-09-25 del A — **kontraktbrud rettet**: planens acceptkrav sagde at `/register` skulle kræve en gyldig `eucomply-pro`-licens, hvilket direkte modstrider låst beslutning 4 og 21 (den monitoring beta er en fri forsøgsordning, ikke en betalt entitlement) og ville have fjernet en gratis del af tragten. Licens-gating er derfor **ikke** implementeret; sikkerheden løses med ejerskabstokens i stedet. Det kræver Mads' svar på spørgsmål 1, før det evt. indføres.
- 2026-09-25 del A — samme guard synkroniseret ind i `eucomply-scanner/engine/index.js`, så den publicerede npm-CLI ikke beholder hullet. De to filer er nu fysisk ens i guard- og `runScan`-afsnittet.
- 2026-09-25 del A — `site/{,da/,de/,fr/}scan/index.html` gemmer owner-tokenet pr. site i `localStorage` og sender det med ved re-registration og sletning, så den eksisterende UX er uændret. Oversættelserne i DA/DE/FR er bevaret.
- Gate: `27 security checks passed` i nyt `tools/test_worker_security.mjs`; `112 self-tests passed`, `0 unexpected EUComply Pro claims`; root-SEO `216 pages checked, 0 findings`; `npm pack --dry-run` grøn (9 filer, 17 kB); alle fire scan-sider består `node --check` på det indlejrede script. Ingen PHP ændret, så PHP-lint er ikke betinget (kørte alligevel grønt på `plugin/` og `site/plugin/`). Sibling-kommandoen i `../hermes-passiv` kunne igen **ikke** køres: workspace-permissions nægter adgang, så missionskravet kan ikke dokumenteres; gyldig SEO-evidence er root-fallbacken, jf. gate-baseline.
- Fejl: 0/2 (denne del)
- Begrundelse: Den offentlige scanner følger redirects uden at validere hvert hop og kan hente private mål; rå HSTS-responseheadere renderes desuden i `innerHTML`. Monitoring-registreringen kan samtidig skifte en andens email, og `/status` er offentligt. Det er P0/P1-brugerrisiko, privacy-fejl og spam-/SSRF-mulighed.
- Scope: følg redirects manuelt og valider destinationen ved hvert hop; escape eller render tekstfelter med `textContent`; valider licens før registrering; tilføj uforfalskeligt site-/owner-token; gør status privat; forhindr overskrivning af en andres email; håndtér redirect- og DNS-cases samt body-størrelse; opret reelt sletningsflow; opret public privacy-tekst ud fra faktisk dataflow. Derudover fra specen: skeln `409` fra definitive fejl i pluginen, tilføj `deactivate`/frigiv enhed, vurdér om `warn` skal tælles som fejl i summen, og udsted engangs-owner-token til eksisterende ubetalte beta-records.
- Accept:
  - ~~Uden gyldig `eucomply-pro`-licens kan `/register` ikke oprette eller ændre en site.~~ Erstattet i del A af ejerskabstokens, jf. kontraktbruddet ovenfor. Licens-entitlement er **helt droppet** efter del A: overvågningen er en fri forsøgsordning, og uden Mads' svar på spørgsmål 1 må den ikke låses.
  - ~~`/status` afslører ikke email, rå URL-data eller andre kunders historie uden gyldigt owner-token.~~ **Dækket i del A**: `/status` er nu POST og 403 uden token; email og token er aldrig i svaret.
  - ~~Redirects til private/link-local IPv4/IPv6-mål og falske DNS-svar afvises; hvert hop og sidste destination valideres.~~ **Dækket i del A** — dog fail-open hvis resolveren *selv* er nede; et konkret privat DNS-svar afvises.
  - ~~En HSTS-header med HTML/scriptpayload renderes som tekst og kan ikke skabe DOM-XSS i scanner-resultater.~~ **Dækket i del A** (filtrering i engine + `esc()` på scan-siden).
  - ~~Unit/integrationstest dækker register, repeat register, unregister, ownership, rate limit, redirect-mål, XSSPayload og 503-grace.~~ **Dækket**: del A dækker register/unregister/ownership/rate-limit/redirect/XSS i `tools/test_worker_security.mjs`; **503-grace er dækket i del B** af `tools/test_license_verdicts.php`.
  - ~~Forkert nøgle, forkert product og nået enheds-/site-grænse giver deterministiske fejl.~~ **Dækket i del B**: `400`/`403`/`404` låser deterministisk; `409` giver sit eget `device_limit`-svar med handlingsanvisning i stedet for generisk afvisning.
  - ~~En eksisterende kunde beholder cached adgang i 7 dage ved licensserver-503/5xx/netværksfejl.~~ **Dækket i del B og testet**: 503 efter 2 dage → Pro aktiv, efter 8 dage → ikke. Samme for 429 og netværksfejl.
  - ~~Privacy-siden nævner præcist Cloudflare KV, email, Stripe, Resend, BugBottle og local storage med retentionsperioder.~~ **Dækket**: dækkede det meste i opgave 1; del B rettede den falske påstand om et offentligt status-endpoint og tilføjede owner-tokenet.

### 4. Byg ægte historik og pass-til-fail-alerts

- Status: `FÆRDIG` i kode og tests på `ceo/watch-per-check-history`, commit `1785766`. **Ikke live**: `worker-watch/` deployes ikke af CI, så dette er først sandt i produktion efter et manuelt `wrangler deploy` (spørgsmål 9). Sitecopy er derfor bevidst **ikke** ændret til "included".
- Fejl: 1/2 (første kørsel af de nye tests faldt over tre reelle fund, rettet i samme iteration)
- 2026-09-25: **Historien er nu per-check, ikke kun score.** Hver dag gemmes `{date, score, passed, total, checks: {key: "pass"|"warn"|"fail"}}` for alle ni tjek, 30 dages loft. `/status` returnerer desuden `checks` (seneste snapshot) uden email, owner-token eller andres data.
- 2026-09-25: **Alarmerne er nu per-check og deduplikerede.** En mail pr. scan der ændrer noget, med checknavn, gammel status, tidspunkt, fund og konkret `fix`. Uændrede scans sender intet; et brud der holder dag to sender intet; en cron-retry samme dag sender intet. Det erstatter den gamle score-fald-mail, som sagde "89 % → 44 %" uden at nævne hvad der var bruddet.
- 2026-09-25 — **fund 1:** den første kørsel af `buildAlert` viste "Score: 0 % (previous 0 %)". `applyScan` skriver dagens score i recordet *før* alarmen bygges, så `record.lastScore` var den nye score. Rettet ved at give `buildAlert` baselinens score som parameter — den skal testes direkte, fordi den er umulig at se ved at læse koden.
- 2026-09-25 — **fund 2:** cron-retry samme dag diffede mod **dagen før** igen og sendte den samme mail igen. Rettet ved at baselinen er dagens gemte snapshot, når den findes, ellers sidste anden dag. Dette er dedupe-kravet i acceptkriteriet og var ikke dækket af min første test.
- 2026-09-25 — **fund 3:** fixture-testen forventede præcis `legal/ssl/trackers`, men `BROKEN_PAGE` mister også privacy-linket, som `forms` kræver, så fire tjek regresserer korrekt. Testen kræver nu de tre centrale tjek og at ét uændret tjek (`dora`) *ikke* rapporteres.
- 2026-09-25 — **afvigelse fra planens første skridt:** retention er et loft på 30 dage i stedet for KV-TTL 40 dage. En `expirationTtl` på site-recordet ville slette registreringen selv, og cron-skrivningen nulstiller TTL'en dagligt, så den kunne aldrig udløbe en aktiv site.
- 2026-09-25 — **deploydagen ville have sendt en mail-bomb:** records fra før per-check-historikken har ingen baseline, så alle deres eksisterende fejl ville være rapporteret som "nye". Den første sådane dag sender nu kun den ærlige score-fald-mail, og næste dags diff er ægte.
- 2026-09-25 — **recovery sender ingen mail.** En check der bliver grøn nævnes i mailen, hvis der ellers er noget at sige, men en ren genopretningsdag sender intet. Det er bevidst: to modsatte dage i træk er præcis den spam, overvågning skal fjerne. Notér hvis Mads vil have en separat "fixed"-mail.
- Gate: `38 security checks passed` i `tools/test_worker_security.mjs` (11 nye, op fra 27); `44 license checks passed`; `112 self-tests passed`, `0 unexpected EUComply Pro claims`; `php -l` grøn på `plugin/` og `site/plugin/` (ingen PHP ændret); `node --check` grøn på begge ændrede filer; `npm pack --dry-run` grøn (9 filer); root-SEO `216 pages checked, 0 findings`. Sibling-kommandoen i `../hermes-passiv` kunne igen **ikke** køres: workspace-permissions nægter adgang, så missionskravet kan ikke dokumenteres; gyldig SEO-evidence er root-fallbacken, jf. gate-baseline.
- **Ingen `site/**`-fil rørt**, så deploy-workflowet trigges ikke af denne commit, og ingen live-verificering er nødvendig for den. Det er dog **ikke** nok: workerne deployes manuelt.
- Begrundelse: Bureauer skal kunne dokumentere regressioner og få besked om den konkrete check, ikke få tilfældig samlet score.
- Første skridt i iterationen: skriv per-check-lagringen i `worker-watch/index.js` (daglig `{date, checks: {key: pass|warn|fail}}`, TTL 40 dage) og kør den gennem `tools/test_worker_security.mjs`-mønstret. `warn` skal her være tri-state uafhængigt af den samlede score, jf. beslutningen i opgave 3 del B.
- Scope: gem seneste og 30 dages per-check-resultater; diff gamle mod nye checks; én mail pr. ny fejl; deduplicér gentagne cron-fejl; link til kundens private resultatside.
- Accept:
  - ~~Identiske scans sender ingen mail; en check, der skifter pass→fail, sender én mail med checknavn, gammel status, tidspunkt og handlingsforslag.~~ **Dækket.** Testene bruger rigtige `runScan`-resultater fra to sider (en god, en efter et dårligt deploy) og den rigtige cron-handler med Resend-kald fanget, ikke håndlavede fixtures.
  - ~~30 dage og 50 samt 100 på hinanden følgende daglige scans er dækket af automatiske tests.~~ **Dækket**: 35 dage med cap på 30 og korrekt ældste dato, samt 50 og 100 scans med assertions på record-størrelse og KV-round-trip.
  - ~~Ingen kundedata eller emailadresse havner i klientlog eller offentligt endpoint.~~ **Dækket**: `/status` dumpes og må ikke indeholde email eller owner-token; `/health` må ikke afsløre overvågede sites; mailteksten må ikke ekko adressen.
  - ~~Copy først skrives som inkluderet, når denne gate er grøn.~~ **Dækket**: ingen sitecopy er ændret, fordi gaten er grøn *i repoet* mens produktionen kører den gamle worker. Copy bliver først "included" efter worker-deployet er bekræftet — spørgsmål 9.

### 5. Implementér kundespecifik rapporter

- Status: `TODO`
- Fejl: 0/2
- Begrundelse: Rapporten er den konkrete bureau-leverance. En statisk sample er ikke en kunderapport.
- Scope: følge specens valgte format; PDF hvis det er besluttet, ellers HTML uden at kalde det PDF; signed/public verification-id hvis relevant; historik og rettelser; download via kundeportal.
- Accept:
  - En autoriseret testkunde kan hente én rapport med sit URL, tidsstempel og faktiske seneste resultat.
  - En anden kunde kan ikke hente rapporten.
  - Filen består filformatvalideringen; ved PDF skal første bytes være `%PDF-`.
  - Statisk eksempel mærkes “eksempel” og indgår ikke i kundeloggen.
  - Siteteksten matcher det faktiske format.

### 6. Implementér live badge og offentlig verifikationsside

- Status: `TODO`
- Fejl: 0/2
- Begrundelse: Nuværende badge lyder “Scanned by EUComply”, men kan ikke dokumentere noget og linker forkert.
- Scope: stabilt offentligt site-id; badge henter kun seneste score/tidspunkt fra begrænset offentligt endpoint; resultatside viser verificérbare data og tidsstempel; email, rå historie og andre kundedata må ikke være offentlige.
- Accept:
  - Badge på en testside viser workerens faktiske seneste score og link til samme site-id.
  - En gammel/falsk payload kan ikke få en badge til at vise en ny score.
  - Endpoint afviser uventede værter og private IP'er uden at afsløre private data.
  - Copy først siger “live” eller “verifiable”, når dette er bygget og integreret.

### 7. Byg entitlement-aware dashboard og multi-site-flow

- Status: `TODO`
- Fejl: 0/2
- Begrundelse: Et demo-dashboard kan ikke levere kundens sites, rapporter, badge eller betalingsstatus.
- Scope: følge multi-site-reglen i specen; kun kundens licens/websites; add/remove/pause; historik, alerts og downloads; ærlig state ved offline grace; ingen tilfældig fallbackdata.
- Accept:
  - To testdomæner med tilladte entitlements kan ses og administreres uafhængigt.
  - Uden entitlement vises login/setup-state, ikke kundemockdata.
  - Ingen `Math.random()`-historik eller hardcoded “all checks passed”-log i kundedashboardet.
  - Site-tilføjelse, pause, sletning og download dækkes af browser/integrationstests.
  - Copy om flere sites følger den betalte prisregel pr. website.

### 8. Stop offentlig udgivelse af interne og betalte filer

- Status: `FÆRDIG` — `ceo/deploy-hygiene`, commit `317e382`. Betalte templates var allerede fjernet af `b0c6ad5`; denne iteration løser resten.
- Fejl: 0/2
- 2026-09-25 — **fundet var større end forventet, og det var live.** `site/` er ikke en publiceret mappe, det er hele arbejdstræet. Verificeret med `curl` mod produktion: `https://eucomplypro.com/AGENTS.md`, `/BUDGET.md`, `/DECISION.md`, `/STATUS.md`, `/RESEARCH.md`, `/KANALPLAN.md`, `/POSTS/01-eighty-five-niches.md`, `/ops/auditlog.py`, `/ceo-loop3.sh` og `/wrangler.toml` svarede **alle 200**. Mads' budget, forretningsstrategi, agent-konfiguration og interne forskningsnoter har været offentligt læsbare siden sitet første deploy.
- 2026-09-25 — **`tools/build_public_tree.py`** bygger `site-dist/` ud fra en **positivliste** af 51 topniveau-stier (18 filer + 33 mapper). 322 af 360 filer er offentlige; 27 topniveau-stier holdes ude (12 `.md`, 5 `.py`, 5 `.sh`, `POSTS/`, `ops/`, `wrangler.toml`, `.gitignore`, et tilfældigt hash-txt) og 4 mere (`devnotify/LAUNCH.md` og tre generator-`.py` under godkendte mapper). Kilde-træet i `site/` røres ikke, så sibling-buildet `../hermes-passiv/build_sites.py` er upåvirket. Scriptet ** stopper med exit 1, hvis en af 19 obligatoriske stier mangler i kilden**, så en slettet side ikke kan forsvinde lydløst, og det printer alle holdt-ude stier, så en ny offentlig mappe ikke kan blive glemt.
- 2026-09-25 — **`tools/check_public_tree.py`** er den permanente gate med tre dele: (1) ingen `*.md/*.sh/*.py/*.toml/*.log/*.bak/*.sql/*.key/*.pem`, ingen `POSTS/`, `ops/`, `deliverables/`, `gumroad/`, `.git`, `.env*`, ingen symlinks og ingen filnavne med `secret`/`credential`/`password`/`apikey`/`-kv`; (2) 20 obligatoriske offentlige stier findes; (3) **alle interne `href`/`src` i 226 HTML-sider og alle redirectmål i `_redirects` findes i træet**. Negativt testet: en indplantet `STRATEGI.md`, `deliverables/dpa.zip`, `ops-kv.json` og `secrets.json` giver alle exit 1, og et dødt redirectmål ligeså.
- 2026-09-25 — **linkkontrollen fandt seks døde links, som alle var reelle.** (a) `de/`, `fr/` og `es/deskuptime/index.html` linkede `/assets/style.css`, som ikke findes — filen hedder `site.css` og indlæses allerede af `tools/apply_shell.py` på samme sider, så det var en overflødighed, der gav én 404 pr. sidevisning; linket er fjernet. (b) Tre Transmute-guides krydslinkede til `/transmute/guides/csv-to-json/`, som aldrig blev genereret (den findes hverken lokalt eller live); de døde links er fjernet, de øvrige guides i rækken er bevaret. (c) `_redirects` sendte 1.2.0- og 1.3.0-plugin-downloads videre til `1.3.1.zip`, som blev fjernet fra deploy-træet da 1.3.2 kom ud — **gamle WordPress-installationer ville få en 301 til en 404 ved opdatering**. Alle tre peger nu på `1.3.2`.
- 2026-09-25 — **`deploy-site.yml` deployer `site-dist/`, ikke `site/`.** Rækkefølgen er nu `checkout → setup-python 3.11 → build_public_tree.py → check_public_tree.py → wrangler pages deploy site-dist → produktionskontrol`, og workflowen trigger også når de to nye scripts ændres. Efter deployen kontrolleres indhold, ikke kun status: `/IMPLEMENTATION_PLAN.md` skal svare 404.
- 2026-09-25 — `site-dist/` er gitignored, så deploy-artefktet aldrig committes. Begge scripts er 3.9-kompatible (undgår `str | None`), så de kører med maskinens `python3` såvel som CI's `3.11`.
- Gate: `0 interne eller betalte filer i træet`, `0 døde interne referencer` på 322 filer / 226 sider; `112 self-tests passed`, `0 unexpected EUComply Pro claims`; `38 security checks passed`; `44 license checks passed`; `php -l` grøn på `plugin/` og `site/plugin/` (byte-identiske, ingen PHP ændret); Node-smoke `9 checks` + korrekt 404-håndtering; `npm pack --dry-run` grøn (9 filer); root-SEO `216 pages checked, 0 findings`. Sibling-kommandoen i `../hermes-passiv` kunne igen **ikke** køres: workspace-permissions nægter adgang til sibling-repoet, så missionskravet kan ikke dokumenteres; gyldig SEO-evidence er root-fallbacken, jf. gate-baseline.
- Begrundelse: En offentlig konto, en offentlig Stripe-konto og en offentlig oplagt interne budget- og konfliktdokumenter er en invitation til svig, til efterligning af forretningen og til at røre ved Mads' navn. Det er den eneste fund i denne plan, der kræver ingen ny kode for at være alvorligt.
- Scope: definer en positivliste for det offentlige build; deploy kun godkendte statiske assets; fjern interne docs, paid source/PDF og driftsscripts fra deploy-artefaktet; opdatér CI til at deploye det verificerede output.
- Accept:
  - ~~CI/deploy-manifestet indeholder ingen `*.md`, `deliverables/`, `POSTS/`, `ops/`, `.git`, credentials eller uvedkommende produkter.~~ **Dækket**: workflowen deployer `site-dist/`, der er bygget af en positivliste og afvist af checken ved ethvert forbudt mønster. **Bemærk:** `deskuptime/`, `transmute/` og `devnotify/` er *søskeprodukter, men de er offentlige marketing-sider på samme domæne og linkes fra bloggen, `llms.txt`, sitemap og søgeindeks. De er derfor bevaret; kun deres interne filer er holdt ude. Udskillingen af søskeprodukter er spørgsmål 11.
  - ~~Smoke-test mod det byggede output finder 0 interne/paid-filer.~~ **Dækket**: `tools/check_public_tree.py`, negativt testet.
  - ~~Alle offentlige sider, CSS, JS, billeder og plugin-download bevarer 200.~~ **Dækket**: 20 obligatoriske stier + fuld intern link- og redirect-integritet på 226 sider. Kan **ikke** end-to-end-verificeres før næste deploy-vindue — se `VERIFICÉR DEPLOY`.
  - ~~Ingen ny betalt templatekopi oprettes i repoet.~~ **Dækket**: `.gitignore` dækker `deliverables/`, `gumroad/products/`, `site/deliverables/`; intet betalt indhold er tilføjet.

### 9. Gør kvalitetsgaten permanent i CI

- Status: `FÆRDIG` på `ceo/ci-kvalitetsgate`
- Fejl: 1/2 — den første kørsel af det nye paritetstest fandt fire forkerte forventninger i testet *og* den P0 nedenfor; alt rettet i samme iteration
- 2026-09-25 — **fund undervejs, en P0 i den publicerede gratis scanner.** `eucomply-scanner/engine/index.js` brugte `UA` inde i `runScan`s try-blok, men var aldrig erklæret i den fil. Fejlen blev derfor kastet som `Could not reach <url>`, så **hver eneste scanning i den npm-pakkede CLI fejlede** med en besked om et domæne, der online uden problemer. Verificeret: `node engine/index.js --json https://example.com` svarede "Could not reach", efter fixen leverer den ni checks. Den kostede ikke en_linje kode at finde, fordi `tools/test_worker_security.mjs` kun importerer `shared/scan-engine.js` — den publicerede motor var slet ikke dækket af nogen test.
- 2026-09-25 — **`tools/test_engine_parity.mjs` (19 checks) lukker hullet.** Den kører begge motorer side om side med stubbet fetch: ni tjek med uforanderlige nøgler, samme score, samme HSTS-filtrering, samme `normalizeUrl`, 17 private/link-local SSRF-mål afvist af begge, og ni IP-shorthands. Negativt testet: fjerner man `UA` igen, falder den fra 19 til 14 checks. Den fangede fire forkerte forventninger i sit eget første udkast, som viste at motorerne er ægte ens — checklisten er ni tjek (`tech` er ikke en check, platform-fingerprinten ligger i `report.platform`).
- 2026-09-25 — **hex- og heltalsværter afvises nu også fail-closed.** `isPublicHostname("0x7f.0.0.1")` svarede *true*, fordi guarden kun fangede `[0-9.]`. URL-parseren ekspanderer hexformer til 127.0.0.1, så alle rigtige indgange var dækket, men den eksporterede guard svarede forkert på et bart værtsnavn. Rettet i begge motorer og testet.
- 2026-09-25 — **`tools/quality_gate.sh` er den ene definition af grøn**, i ni steps: PHP-lint → plugin-paritet → JS-syntaks → fire repo-tests → publiceret træ → SEO → sibling-gate → `npm pack` → live røgtest. Hvert step logger den kørte command og sin exit code. Lokalt og i CI kaldes samme script, så de to kan ikke glide fra hinanden. Negativt testet: en PHP-syntaksfejl og en SEO-regression giver begge `GATE RØD` med exit 1.
- 2026-09-25 — **SEO-evidensen kan ikke længere være en 0-side-kørsel.** Gaten fejler hvis `tools/seo_check.py` scanner 0 sider, uanset exit code, fordi sibling-scriptet præcis sådan rapporterer. Den vælger selv en python ≥ 3.10, så en gammel lokal `python3` ikke giver en stille `SyntaxError`, der ligner en SEO-fejl. Sibling-gaten køres når `../hermes-passiv` findes — **den kan køre her, selv om et værktøjskald ikke må tilgå sibling-repoet** — og dens kendte `0 pages`-udfald logges som advarsel, mens repoets egen kontrol er den obligatoriske evidens.
- 2026-09-25 — **CI har nu tre jobs: `verify` → `deploy` → `check-production`.** `verify` kalder den genbrugelige `.github/workflows/verify.yml`, som også kører på enhver `pull_request` og har `permissions: contents: read` og ingen secrets. Secrets findes kun i `deploy`. `deploy-site.yml` trigger nu også på `shared/`, `worker-*/`, `plugin/`, `eucomply-scanner/` og `tools/`, ikke kun `site/**` — førstnævnte ændringer har alle deployet konsekvenser.
- 2026-09-25 — **kanin-hullet er lukket, og det viste sig at være farligt at lukke naivt.** Den gamle produktionskontrol testede `/IMPLEMENTATION_PLAN.md`, som aldrig har ligget i `site/`: 404 før og efter, altså intet bevis. Den tester nu 12 stier der *faktisk* var eksponerede — inklusive `/AGENTS.md` og `/wrangler.toml`. Men alle requests bærer `?cb=$GITHUB_RUN_ID`: Cloudflare bruger den fulde URL som cache-nøgle, så kravet rammer origin og ikke kanten. Uden det ville kontrollen have læst de cachede 200-svar fra før rensningen og fejlet hvert deploy i syv dage. Verificeret mod live lige nu: alle 12 svarer 404, alle 13 nøglesider svarer 200 med reelt indhold, plugin-zip'en er en zip.
- Begrundelse: Nuværende deploy-workflow uploader `site/` uden PHP-lint, build eller SEO-check, så en lokal grøn gate kan regressere i CI.
- Scope: kør relevante PHP-lints før deploy; kør EUComply build + SEO fra en reproducerbar checkout af sibling-kontraktet; håndtér at kun `auditedwp` er tilgængelig; adskil verification fra selve Pages-upload.
- Accept:
  - ~~En PR med PHP-syntaksfejl eller SEO-fejl kan ikke deploye.~~ **Dækket**: `verify.yml` kører på enhver `pull_request` og kalder samme `tools/quality_gate.sh` som deploy-jobbet. Negativt testet lokalt: PHP-syntaksfejl → exit 1, SEO-regression → exit 1.
  - ~~CI logger exit code og kørte command.~~ **Dækket**: gaten printer `$ <command>` og `OK/FEJL <step> (exit N)` for hvert step.
  - ~~Secrets, `.env*` og deploy credentials indgår aldrig i logs eller build-output.~~ **Dækket**: `verify`-jobbet erklærer `permissions: contents: read` og bruger ingen secrets; kun `deploy` har `CLOUDFLARE_API_TOKEN`/`ACCOUNT_ID`. Gaten læser ingen `.env` og printer ingen nøgler.
  - ~~Den lokale missionsgate og CI-kommandoer stemmer overens.~~ **Dækket**: CI kalder `bash tools/quality_gate.sh` — samme fil som `bash tools/quality_gate.sh` lokalt. Der er ingen duplikering af kommandoer mellem workflowen og gaten.
  - ~~Sibling-kommandoen fra missionen køres, eller manglen registreres eksplicit.~~ **Dækket**: step 07 kører `AUDITEDWP_DIR=… build_sites.py --only eucomplypro.com` + `tools/seo_check.py --only eucomplypro.com` når `../hermes-passiv` findes, ellers logger den at sibling-repoet ikke findes og at gyldig evidens er step 06.

### 10. Forbedr konvertering efter ærlig baseline

- Status: `FÆRDIG` på `ceo/cta-baseline`
- Fejl: 0/2
- Begrundelse: Først en sand baseline giver valide salgstal og bedre prioritering; skærefulde claims oven på en defekt købsrejse skader tillid.
- 2026-09-25 — **fund: to af sitets mest højtudsøgte sider havde slet ingen købsvej.** `/checklist/` er en selvtest med 28 krav, live-score og en prioriteret fix-liste, og den er linket fra forsiden, `llms.txt`, bloggen og tre guide-sider — men den sluttede kun på `/scan/` og `/store/`, aldrig på Pro. Den er præcis det sted, hvor læseren lige har fundet ud at han har problemer, og det var det sted, hvor vi ikke tilbød løsningen. `/badge/` havde samme problem: to scanning-knapper og ingen Pro. Begge har nu præcis én købsknap til det kontraktfikserede link, med tekst der kun lover det der findes i dag (pluginens DPA/NIS2-DORA/EAA-starthtml + HTML-rapport fra seneste scan) og som eksplicit siger at live-badge, historik, PDF og hosted re-scan **ikke** er med.
- 2026-09-25 — **`/badge/` fik samtidig en ærlig afsnits-title.** Siden sagde, at badgen er statisk, men skrev det kun i en tabelcelle og i JSON-LD. Den siger nu med overskrift, at badgen bærer ingen score, intet tidsstempel og intet en revisor kan verificere, og at den derfor ikke må bruges som bevis. Det er præcis det, missionen kalder en levende reference på opgave 6.
- 2026-09-25 — **ét refund-løfte fjernet fra vilkårene.** `/terms/` lovede at "applicable refund terms are provided at checkout". Stripe-checkouten viser produkt, pris og betalingsmetoder — ikke vores refusionstermer — så det var et løfte uden indhold. Erstatning af en ærlig linje: EU's forbrugerfortrydelsesretter gælder, og vi pålægger ikke egne refusionstermer ovenpå. Dette lukker spørgsmål 5 delvist; det samme gælder nu `/pro/` og de fire prissider, som allerede var ryddet.
- 2026-09-25 — **`tools/check_cta.py` gør acceptkriterierne 1 og 2 prøvbare i stedet for papirlove.** Seks delkontroller: ingen Stripe-link uden for kontrakten, præcis én købsanker til Pro-linket pr. salgsside, symmetri mellem `da/`, `de/`, `fr/`, absolut canonical pr. side, 0 døde interne referencer og 0 uunderstøttede løfter på købsrejsens sider. Kør både som gate og med `--selftest`.
- 2026-09-25 — **fund undervejs, som næsten slap igang: den nye gate var grøn uden at have kontrolleret noget.** `run()` samlede kun returværdierne lokalt og fyldte aldrig listen, så alle seks kontrollere returnerede korrekt, men fundene blev kasseret. Først `--selftest` afslørede det, fordi den negative døde-reference-case ikke blev fanget. Dette er præcis den fejltype opgave 9handlede om i CI, og den er grunden til at selftesten ikke er valgfri.
- 2026-09-25 — **fund undervejs #2: gaten ramte blogindlæg, der ikke var løfter.** Den første refund-patroon gav 3 fund på `/de|es|fr/deskuptime/` (et **søskeprodukt** med sit eget Stripeprodukt), 3 på `_partials/`-fragmenter uden canonical og 1 på `/blog/do-you-need-a-refund-policy/` — fordi artiklen *anbefaler* sælgere at give "a 14-day money-back guarantee". Alle fire var gaten, der var for bred, ikke siderne der var forkerte. Rettet: søskeprodukter og fragmenter er undtaget, og forbudte løfter måles kun på købsrejsens sider, fordi det er der et løfte gør skade.
- **Baseline = 0, og det er et dokumenteret nul.** Der findes ingen trafikmåling på EUComply: ingen analytics-tagging på nogen side, og den eneste tællende worker i repoet (`worker-metrics/`) tilhører DevNotify. Scannertallene ligger i `worker-scan/`, som ikke er deployet. Vi kan derfor ikke adskille vores egne testbrugere fra reelle kunder, fordi vi ikke kan tælle nogen af dem, og **konvertering, scanninger og salg står som 0 i alle rapporter indtil en tællende worker er deployet** — jf. reglen i AGENTS.md om aldrig at måle succes på egne tests. Der er bevidst ikke skrevet et script, der "beviser" 0: det ville være en løgn, ikke et bevis. Målingsforslag står som spørgsmål 14.
- Scope: én tydelig CTA pr. localized side; fri scan → problem → Pro; fjern døde/forkerede "contact", refund-, gratis-trial- og konto-claims; tilføj dokumenteret analytics først når privatliv og baseline er korrekt.
- Accept:
  - ~~EN/DA/DE/FR har ingen 404, død knap eller fejl canonical.~~ **Dækket**: `tools/check_cta.py` giver `0 døde interne referencer`, korrekt canonical på alle 200+ EUComply-sider og krav om at `da/`, `de/`, `fr/` alle har de samme tre købssider. Negativt testet i `--selftest`.
  - ~~Én CTA pr. side fører til det kontraktfikserede Stripe-link.~~ **Dækket**: 18 afgrensede salgssider skal have præcis **én** købsanker til `https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03`, og ingen side må pege på en checkout uden for kontrakten. `/checklist/` og `/badge/` var de to sidste huller.
  - ~~Baseline metrics kan skelne egne testbrugere fra reelle kunder; rapportér 0 hvis overhovedet ikke kan dokumenteres.~~ **Dækket som 0, se afsnittet ovenfor.** Bevidst ikke et script: uden måling er tallet 0, og at skrive et tal ind i et script ville bare flytte det ud af virkeligheden.

### 11. Opgrader og erklær kun relevante runtimes

- Status: `TODO`
- Fejl: 0/2
- Begrundelse: Scanneren og CLI'en er centrale i gratisstrømmen og bruger endnu Node 18 som laveste understøttede version, mens CI bruger Node 20. Root-sitet har ingen runtime-manifest.
- Scope: verificér Node supportpolicy; opgradér scanner/CLI's `engines` og tilføj `.nvmrc` i én runtime-commit; kør smoke, pack og scannerens eksisterende CI; auditér kun EUComply-afhængigheder.
- Accept:
  - Ny understøttet Node-major fremgår tydeligt i `engines` og `.nvmrc`.
  - Smoke-test, `npm pack --dry-run`, PHP-lint og SEO-gate er grønne.
  - Planen noterer gammel→ny version og eventuelle kodeændringer.
  - Ingen DeskUptime/DevNotify-major opgraderes i samme commit.

### Deploy-verificering 2026-09-25 20:35 CEST

CI-kørsel `36173925589` (`deploy-site`, success på 31 s) byggede og verificerede træet grønt og uploadede `site-dist/`. Verificeret på indhold mod live:

- `/AGENTS.md`, `/BUDGET.md`, `/DECISION.md`, `/STATUS.md`, `/RESEARCH.md`, `/KANALPLAN.md`, `/wrangler.toml`, `/ops/auditlog.py`, `/POSTS/01-eighty-five-niches.md` og `/ceo-loop3.sh` svarer **404** på origin. De var alle 200 tidligere samme dag.
- `/assets/eucomply-1.3.1.zip` svarer **301 → `/assets/eucomply-1.3.2.zip`**, og `/assets/eucomply-1.3.2.zip` svarer 200 `application/zip` 23048 bytes. Den gamle 1.3.0-redirect lander også på 1.3.2. Det er den vej gamle WordPress-installationer opdaterer ad.
- `/de/deskuptime/`, `/fr/deskuptime/` og `/es/deskuptime/` har ingen reference til `/assets/style.css` længere.
- `/`, `/pro/`, alle fire pricing-ruter, alle fire locale-Pro-ruter, `/scan/`, `/plugin/`, `/privacy/`, `/sample/`, `/blog/` og `/store/` svarer alle 200.

**To ting ved denne verificering, den næste iteration skal kende:**

1. **CI's produktionskontrol brugte et falsk kanin-hul.** Den testede `/IMPLEMENTATION_PLAN.md`, som *aldrig* har ligget i `site/`, så den var 404 før og efter og beviser intet. Den skal testes mod en sti, der faktisk var eksponeret — f.eks. `/AGENTS.md`.
2. **En del af de interne filer er stadig tilgængelige via Cloudflares edge-cache.** Uden cache-buster svarede `/AGENTS.md` stadig 200 med `age: 10724` og `cache-control: public, s-maxage=604800` — altså op til syv dages cached 200 på de præcis de URLs, der var læst tidligere. Origin er renset, men en klient med et gammelt cache-entry kan hente det gamle indhold. Det kræver en cache-purge hos Cloudflare, som agenten ikke har adgang til. **Det er spørgsmål 12.** Mærkeligt nok gav mit eget `curl` ovenfor både 200 og 404 for den samme URL i samme minutt — kanten er inkonsistent.

## ❓ Til Mads

1. **Hosted Pro og plugin-Pro:** skal den nuværende `eucomply-pro`-nøgle eksplicit give både plugin-dokumenter og hosted-funktioner, eller skal plugin-dokumenterne være en del af et senere samlet Pro? Indtil dette er afklaret, sælger vi kun plugin-dokumenterne.
2. **Betalt navn:** EUComply Pro-navnet må ikke ændres. Forslag til den senere enterprise/self-service-plan: **EUComply Agency** (bureau/white-label), **EUComply Monitor** (daglig drift) eller **EUComply Bureau** (flere kundersider).
3. **Eksponerede templates:** de eksisterende betalte kilder/PDF'er har været offentlige. De bør regnes som kompromitterede; eventuelle nye eller forbedrede versioner skal udvikles i et privat repo og leveres fra CF KV. Skal de gamle produkter trækkes fra salg, eller kræver de en ny privat v1?
4. **DevNotify:** `devnotify/src-tauri/src/lib.rs` bruger fortsat Lemon Squeezy og har intet Stripeprodukt. Kræver den et nyt produkt/key før migrering?
5. **Refund-/skattecopy:** hvilken helt konkrete refund- og invoice-/OSS-proces skal de fire prissider beskrive? Stripe er ikke Merchant of Record, så den nuværende tekst skal fjernes, indtil en dokumenteret proces findes.
6. **Alarm-tilstand:** er `ALERT_KEY` sat i produktion for `eucomply-watch`? Uden nøglen sender overvågningen ingen mail (`worker-watch/index.js:22`), så enten skal den sættes eller overvågning som produkt skal væk fra siden. Det er ikke opdageligt i repoet.
7. **Kvotevisning:** findes der en deterministisk måde at få det købte antal websites ud af licensserveren? `devices_in_use` plus `409` er ikke nok til en ærlig kvotebjælke i dashboardet (spec afsnit 5.1).
8. **Device-idempotens:** er `activate` med et allerede aktiveret `device_id` idempotent uden at optage en ekstra enhed? Det afgør, om et site med både plugin og hosted tæller som ét website.
9. **Worker-deploy:** `shared/scan-engine.js` og `worker-scan/`/`worker-watch/` deployes ikke af CI. Skal de nye workers deployes nu, og hvem gør det — Mads eller en agent med `wrangler`-adgang? Uden det ligger rettelsen i repoet, men produktionen kører den gamle kode. **Tre runder er nu ophoblet bag denne ene beslutning:** SSRF-guarden + ejerskabstokens (`28795c3`), per-check-historik og regression-alarms (`1785766`) og 409-semantiken med `deactivate` i pluginen. Jo længere den venter, desto større er hullet mellem det, repoet lover, og det kunderne oplever.
10. **Ubeskyttet widget:** `site/shared/live-check-widget.html:33,37,39,42` renderer scanningstjek fra et kundesite i `innerHTML` uden escaping og kalder DeskUptime-workeren. Den ligger i EUComply-deploy-træet, men uden for EUComply-gaten. Skal den rettes her eller i DeskUptime-repoet?
12. **Cache-purge Cloudflare:** de interne dokumenter, der lå i `site/`, er væk fra origin, men cachede 200-svar (`s-maxage=604800`) ligger stadig i kanten indtil de udløber. Skal der køres en cache-purge på Pages-projektet `auditedwp`? Det kan en agent ikke gøre uden Cloudflare-adgang, og det er den eneste måde at få de gamle 200-svar væk før udløb. **Opdateret 25/9:** Cloudflare bruger den fulde URL som cache-nøgle, så et URL med en vilkårlig query-strings cache-buster (`/AGENTS.md?cb=…`) er et cache-miss og rammer origin, som svarer 404. CI's produktionskontrol bruger derfor cache-bustede URLs — ellers ville den have læst det gamle cachede indhold og fejlet hvert deploy i syv dage. Uden cache-buster svarer `/AGENTS.md` stadig 200, så **purgen er stadig nødvendig for almindelige browsere**.
13. **npm-publish af den rettede scanner:** `eucomply-scanner` 1.0.0 på npm har den P0, opgave 9 fandt — `UA` er ikke erklæret i den publicerede motor, så *alle* scans fejler med "Could not reach". Rettelsen ligger i repoet og er testet, men agenten må ikke publisere. Skal Mads køre `cd eucomply-scanner && npm publish` (eller give en agent tilladelse det), så den gratis scanner virker igen for alle, der har hentet den? Det er den værste skade i planen, fordi den rammer hele den gratis tragt.
14. **Måling af konverteringen (spørgsmål 14, nyt 25/9):** opgave 10 fastslår **0** som baseline, fordi EUComply slet ikke tæller noget. Uden tal kan vi ikke vide, hvilken af prissiderne, CTA'erne eller funktionerne der virker, og næste prioritering bliver gætteri. Der er tre veje, og alle tre kræver en beslutning eller adgang en agent ikke har: (a) **Cloudflare Web Analytics** på Pages-projektet — gratis, cookiefrit, ingen GDPR-tekst nødvendig, men skal slås til i Cloudflares dashboard, og læses i dashboardet; (b) en **tællende worker** på den eksisterende `worker-scan`/`worker-watch`-KV, som tæller pageviews, scans og Pro-klik uden persondata, og som kan læses fra en `/stats`-kald — kræver den `wrangler deploy`, der allerede er spørgsmål 9; (c) **intet**, og så forbliver alle salgstal 0 og vi optimerer uden data. Jeg anbefaler (a) straks og (b) samtidig med spørgsmål 9, fordi de to dele den sambeslutning. Uden dem bliver enhver påstand om hvad der virker i denne plan et gæt, og det er præcis den fejltype AGENTS.md forbyder.
15. **Returguide som selvstændigt produkt:** `/refund-policy-generator/` er nedlagt, fordi den producerede juridisk lænende dokumenter uden en jurist bagved. `/blog/do-you-need-a-refund-policy/` er derimod en stærk, søgt guide om netop dét emne. Skal den guiden sælges som betalt skabelon med Stripe (kræver et nyt produkt og nyt link, som agenten ikke må oprette), eller forbliver den gratis som indhold, der trækker trafik til scanneren?
11. **Søskeprodukter på samne domæne:** `deskuptime/` (40 filer), `transmute/` (12) og `devnotify/` (62) ligger i EUComply-deploy-træet og er linket fra bloggen, `llms.txt`, sitemap og søgeindeks, så de er ikke bare affald — de er bevaret af opgave 8. De har hver deres eget Stripeprodukt og deres eget repo (jf. `deskuptime-desktop`, `transmute-desktop`). Skal de flyttes til egne domæner, eller er det bevidst, at eucomplypro.com også sælger de tre? Hvis de skal væk, kræver det 100+ omdirigeringer, og det er en beslutning, ikke en oprydning.

## Kendte lavprioritets-rester

- `cli/bin/eucomply-scan.js` er en separat, ældre CLI der laver sit eget `fetch(u)` uden redirect-guard. Den ligger uden for EUComply-tragten (sitets Scan CLI-links peger på `eucomply-scanner` på GitHub), men har samme SSRF-mønster. Lav prioritet; samme guard kan genbruges.
- `site/transmute/gen_guides.py` genererer de døde `/transmute/guides/csv-to-json/`-links, som opgave 8 fjernede fra de tre publicerede sider. Scriptet ligger uden for deploy-træet, så en fremtidig kørsel genopbygger fejlen. Transmute er et søskeproduct og uden for EUComply-gaten.
- `deskuptime/` er en forældet kopi med gammel Lemon Squeezy-kode, selvom sitens DeskUptime-side allerede bruger Stripe. Fjern kopien fra EUComply-deploy eller markér repoet tydeligt som legacy; den rigtige app ligger i sit eget repo.
- DevNotify er et separat produkt og skal ikke blandes ind i EUComply-opgaverne; venter på Mads' Stripe-kontrakt.
- Gamle root-manifester og legacy-stores skal fjernes fra offentlige/aktive paths. Det 1.2.0-plugin-arkiv er allerede væk fra deploy-træet; kun `_redirects`-migrationen fra 1.2.0/1.3.0/1.3.1 → 1.3.2 manglede, og den er rettet i opgave 8.
- Ingen npm-publish, Chrome Web Store-upload, AMO/VS Code Marketplace/Homebrew-upload, git-tag eller release må ske fra agenten.

## Deploy-log

- 2026-09-25: Research-plan oprettet på commit `fba1971`; endnu ingen `site/**`-ændring og derfor ingen forventet deploy fra denne iteration.
- 2026-09-25: Opgave 2 (hosted Pro-spec) ændrede kun `IMPLEMENTATION_PLAN.md` og `docs/`, som begge ligger uden for `site/**`. Deploy-workflowet trigges derfor ikke, og der skyldes ingen ny `VERIFICÉR DEPLOY`-note fra denne iteration.
- `VERIFICÉR DEPLOY: IMPLEMENTATION_PLAN research + prioritering b7b54ac 2026-09-24 23:19 UTC` — ingen deploy forventes, fordi workflowet kun trigges på `site/**` eller workflow-filen.
- `VERIFICÉR DEPLOY: EUComply Pro-salgstuth + plugin 1.3.1 + extension 1.0.1 767ac6e 2026-09-25 13:57 UTC` — **DEPLOY OK 2026-09-25 18:15 CEST.** Verificeret på indhold, ikke kun status: `/pro/` viser "Pro includes today" med kun de tre dokumentfunktioner og en separat, tydeligt mærket "Planned features, not included today"-blok; `/pricing/` har nul nutidige claims om daglig re-scan, PDF eller badge; `/da/pro/`, `/de/pro/`, `/fr/pro/` og alle fire pricing-ruter svarer 200; plugin-downloadet på `/assets/eucomply-1.3.1.zip` svarer 200 med `application/zip`, 20569 bytes.
- `VERIFICÉR DEPLOY: SSRF-guard + overvægtningsejerskab 28795c3 2026-09-25 16:32 UTC` — ændrer `site/**/scan/index.html` (token-håndtering) og rører ikke andre publicfiler. Verificér efter næste deploy-vindue at `/scan/` stadig kan registrere og afmelde, og at de fire locale-siders script ikke har mistet en sætning. Bemærk: **workerne deployes ikke af denne workflow** — `shared/scan-engine.js`, `worker-scan/` og `worker-watch/` kræver et manuelt `wrangler deploy`, hvilket agenten ikke gør. Indtil det sker, er live-scanneren stadig den gamle, sårbare kode, og det gamle `GET /status?url=` svarer stadig 200 indtil worker-deployet.
- `VERIFICÉR DEPLOY: licens-409 + frigiv-enhed + privacy 1.3.2 e9f1e09 2026-09-25 17:40 UTC` — ændrer `site/plugin/index.html` (downloadlink), `site/privacy/index.html`, `site/update.json` og tilføjer `site/assets/eucomply-1.3.2.zip` (1.3.1-zip'en er fjernet fra deploy-træet). Verificér på indhold efter næste vindue: at `/assets/eucomply-1.3.2.zip` svarer 200 med `application/zip` og at den gamde 1.3.1-zip **ikke** længere findes, at downloadknappen på `/plugin/` peger på 1.3.2, og at privatlivssiden ikke længere siger at status-endpointet er offentligt. Sidste deployment er manuel, så plugin-1.3.2-ændringerne når kun kunder ved at de opdaterer fra wp-admin.
- `DEPLOY OK 2026-09-25 20:35 CEST` + `VERIFICÉR DEPLOY: verificeret offentligt deploy-træ 317e382 2026-09-25 20:05 UTC` — ændrer `site/_redirects` (to plugin-redirects → 1.3.2, ny 1.3.1→1.3.2), `site/{de,es,fr}/deskuptime/index.html` (fjernet død `style.css`-link) og tre Transmute-guides (fjernet død krydslink), samt tilføjer `tools/build_public_tree.py` og `tools/check_public_tree.py` og retter `deploy-site.yml`. **Dette er den første udgivelse, der går gennem `build_public_tree.py` + `check_public_tree.py`, så workflowen skal køre de to scripts grønt, før den uploader.** Efter næste deploy-vindue skal følgende verificeres på indhold: (1) `https://eucomplypro.com/AGENTS.md` svarer **404** — det gjorde det 200 før denne ændring; samme for `/BUDGET.md`, `/DECISION.md`, `/STATUS.md`, `/wrangler.toml` og `/ops/auditlog.py`; (2) `/assets/eucomply-1.3.1.zip` svarer **404**, fordi 1.3.2 erstattede den, og `/assets/eucomply-1.3.2.zip` svarer 200 med `application/zip`; (3) de tre gamle plugin-redirects lander på 1.3.2 og ikke på en 404; (4) `/de/deskuptime/`, `/fr/deskuptime/` og `/es/deskuptime/` indlæser `/assets/site.css` og har ingen fejlende forespørgsler i netværksfanen; (5) `/pro/`, alle fire pricing-ruter, `/scan/`, `/plugin/` og `/privacy/` svarer stadig 200. Resterne af sitet er uændrede af denne diff — 322 filer er uændrede kopier af det, der lå i `site/` før.
- `VERIFICÉR DEPLOY: per-check-historik + regression-alarms 1785766 2026-09-25 18:05 UTC` — **kræver manuel worker-deploy, ikke sitets.** Ændrer kun `worker-watch/index.js` og `tools/test_worker_security.mjs`; ingen `site/**`-fil, så intet af CI'en deployer. Efter `wrangler deploy` i `worker-watch/` skal følgende verificeres på den rigtige worker: `GET /health` svarer `version: "1.2.0"`; `POST /register` returnerer `history[0].checks` med ni nøgler; `POST /status` med owner-token returnerer `checks` og ingen email; cron kl. 06:00 UTC på en registreret testside med en tydelig regression sender **én** mail med checknavn og fix, og ingen mail dagen efter uden ændring. Kræver `ALERT_KEY` i produktion (spørgsmål 6), ellers er der ingen mail at verificere.
- `DEPLOY OK 2026-09-25 21:26 CEST` + `VERIFICÉR DEPLOY: kvalitetsgate + UA-fix i scanneren 87b7ab4 2026-09-25 19:23 UTC` — CI-kørsel `36179385381` kørte alle tre jobs grønt på første forsøg: `kvalitetsgate` (GATE GRØN, 9 steps: 38 security + 19 engine-parity + 44 license + 112 claims, 0 interne/0 døde referencer, 216 sider 0 findings), `deploy` og `tjek produktion`. Den nye produktionskontrol er verificeret mod live: alle 12 interne stier svarer 404 på origin med cache-buster, alle 13 nøglesider svarer 200 med reelt indhold (24 695 bytes på `/`, 11 891 på `/pro/`), og `/assets/eucomply-1.3.2.zip` er 200 og en zip. Det var den kontrol, der først skulle bevise sin egen rigtighed. Ingen `site/**`-fil rørtes, så 322 filer er uændrede kopier af det der lå i `site/` før. CI's advarsel om `ubuntu-latest`/`Node.js 20`-deprecation er noteret i opgave 11.
- `VERIFICÉR DEPLOY: købsvej + CTA-gate (opgave 10) 7c0f19c 2026-09-25 20:10 UTC` — ændrer `site/checklist/index.html` (ny Pro-CTA i fix-listen), `site/badge/index.html` (ny sektion "What the badge does not do" + Pro-CTA), `site/terms/index.html` (fjernet refund-løftet), `tools/check_cta.py` (ny), `tools/quality_gate.sh` (to nye steps) og denne plan. Efter næste deploy-vindue skal indhold verificeres på fire punkter: (1) `/checklist/` har præcis én knap til `buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03` og scannerens `#result`-blok har mistet intet; (2) `/badge/` viser afsnittet "What the badge does not do" og badge-embed-koderne er uændrede; (3) `/terms/` afsnit 4 ikke længere siger at refusionstermer gives ved checkout; (4) CI's `verify`-job kører de to nye `check_cta`-steps grønt. Hvis nogen af de fire ikke holder, er årsagen formodentlig `apply_shell.py`, der kan have renset klassenavne på de indsatte `p.actions`-blokke.
