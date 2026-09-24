# IMPLEMENTATION_PLAN — EUComply

Opdateret: 2026-09-25
Sidste iteration: research + prioritering, fordi planen ikke fandtes
Baseline: `main` commit `fba1971` efter `git pull --ff-only`
Mission: sælge EUComply Pro ærligt og bygge den værdige betalte oplevelse uden at svække den gratis scanner.

## Iterationsstatus

- `I GANG`: ingen. Research-iterationen er færdig.
- Næste opgave: **1 — Ret salgsløfterne til det der virker nu**.
- En opgave må markeres `I GANG`, før der laves kode. Efter to mislykkede iterationer markeres den `BLOCKED: <årsag>`, hvorefter næste opgave tages.
- Oplysninger, beslutninger og deploy-noter skal fortsat skrives her, så næste iteration kan arbejde uden hukommelse.

## Verificeret produkttruth — 2026-09-25

| Område | Det virker i dag | Det er ikke implementeret eller kan ikke sælges endnu |
|---|---|---|
| Gratis webscanner | Ni universelle URL-tjek, forslag til rettelser og et delbart resultat via `shared/scan-engine.js` og `worker-scan/index.js`. | Ingen sammenkoblet Pro-entitlement. |
| Hosted monitoring beta | `worker-watch/index.js` har cron kl. 06:00 UTC, 30 dages samlet score-historik og score-fald-mail. | Registreringen er åben og ikke knyttet til køb eller licens. `/status` er offentligt. Der gemmes kun samlet score, så pass-til-fail pr. check kan ikke implementeres ud fra historikken. |
| Gratis WordPress-plugin | seks site-/WordPress-tjek og en ugentlig planlagt scan i `plugin/eucomply.php`. | Ingen historik, ikke dagligt. |
| WordPress-plugin Pro 1.3.0 | Licensen validerer mod Mahope og låser DPA-, NIS2/DORA- og EAA-starthtml samt en rapport fra seneste scan. | Dokumenterne er redigerbare HTML, ikke PDF. Der er ingen hosted konto, historik, badge, mailflow eller flere sites. |
| Hosted Pro-dashboard | `/pro/dashboard/` er en offentlig demo. | Ikke kundedata, ikke autentificeret og uden tilføj/slet/cancel. Ved fejl dannes 30 dages historik med `Math.random()` i `site/pro/dashboard/index.html:322-336`. |
| Rapport | Plugin kan downloade HTML fra seneste scan. | Runtime-PDF og kundespecifikke rapporter findes ikke. Statisk eksempelrapport er kun en demo. |
| Footer-badge | Der ligger et statisk embed-script. | Scriptet henter ingen score og linker til `location.origin`, ikke et EUComply-resultat, i `site/assets/eucomply-badge.js:23-27,79-90`. |
| Pro-levering | Stripe-linket er live og licensen virker i plugin. | Watch-worker, dashboard og Stripe-success-flow er ikke koblet sammen. `/pro/thank-you/` lover bl.a. konto, live score, PDF, flere sites og cancel, som ikke findes. |
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
2. **Repo-tests:** repoet har ingen root-test-suite eller PHP-testkonfiguration. Den regressionstest for påstande, der tilføjes i opgave 1, bliver den nye obligatoriske test. Hvis scannerkoden ændres, køres desuden scannerens smoke-test og `npm pack --dry-run` i `eucomply-scanner/`.
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

- Status: `TODO` — første implementeringsiteration
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

- Status: `TODO`
- Fejl: 0/2
- Begrundelse: Kontraktet kræver spec før større Pro-funktioner. Uden fælles data-, adgangs- og fejlmodel bliver dashboard, alerts, rapport og badge hinanden uforenlige.
- Scope: ny `docs/eucomply-pro-spec.md` med skillet mellem gratis scanner, WordPress-plugin Pro og hosted Pro; købsflow; licens/device binding; multi-site-regel; 30 dages historik; pass-til-fail-diff; rapportformat; badge-identitet; mail; dashboard; retention; sletning; 7-dages offline grace; privacy og trusler.
- Accept:
  - Specen definerer hver af daglig re-scan, historik, kunderapport, flere sites og mail-alarmer uden overlap.
  - Alle request/response-kontrakter, KV-nøgler, rettigheder, retention og fejlkoder er eksplicitte.
  - Licensserveren 503/5xx/netværksfejl giver cached entitlement i op til 7 dage. Et definitivt ugyldigt, udløbet, tilbagekaldt eller forkert-produkt-svar låser, mens 409 kun afviser den nye enhed.
  - En belastningstestmatrix, privacy-datamappe og migrationsplan findes.
  - Specen bruger kun det eksisterende Stripe-link og `eucomply-pro`; den kræver ingen nye Stripeprodukter.

### 3. Gør hosted monitoring entitlement-sikker og ret privacy

- Status: `TODO`
- Fejl: 0/2
- Begrundelse: Enhver kan i dag skrive e-mail på en vilkårlig URL og læse offentlig status. Det er ikke en Pro-fordel, skærer privacy-politikken og kan misbruges til spam/SSRF/ressource abuse.
- Scope: valider licens før registrering; tilføj uforfalskeligt site-/owner-token; gør status privat; forhindr overskrivning af en andres email; håndtér redirect- og DNS-cases samt body-størrelse; opret reelt sletningsflow; opret public privacy-tekst ud fra faktisk dataflow.
- Accept:
  - Uden gyldig `eucomply-pro`-licens kan `/register` ikke oprette eller ændre en site.
  - Forkert nøgle, forkert product og nået enheds-/site-grænse giver deterministiske fejl.
  - En eksisterende kunde beholder cached adgang i 7 dage ved licensserver-503/5xx/netværksfejl.
  - `/status` afslører ikke email, rå URL-data eller andre kunders historie uden gyldigt owner-token.
  - Unit/integrationstest dækker register, repeat register, unregister, ownership, rate limit, redirect-mål og 503-grace.
  - Privacy-siden nævner præcist Cloudflare KV, email, Stripe, Resend, BugBottle og local storage med retentionsperioder.

### 4. Byg ægte historik og pass-til-fail-alerts

- Status: `TODO`
- Fejl: 0/2
- Begrundelse: Bureauer skal kunne dokumentere regressioner og få besked om den konkrete check, ikke få tilfældig samlet score.
- Scope: gem seneste og 30 dages per-check-resultater; diff gamle mod nye checks; én mail pr. ny fejl; deduplicér gentagne cron-fejl; link til kundens private resultatside.
- Accept:
  - Identiske scans sender ingen mail; en check, der skifter pass→fail, sender én mail med checknavn, gammel status, tidspunkt og handlingsforslag.
  - 30 dage og 50 samt 100 på hinanden følgende daglige scans er dækket af automatiske tests.
  - Ingen kundedata eller emailadresse havner i klientlog eller offentligt endpoint.
  - Copy først skrives som inkluderet, når denne gate er grøn.

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

- Status: `TODO`
- Fejl: 0/2
- Begrundelse: Pages deployer hele `site/`, som indeholder interne strategidokumenter, scripts, `deliverables/` og andre ikke-offentlige arbejder. Betalte templates i et offentligt repo er allerede eksponeret og må genovervejes som kompromitterede.
- Scope: definer en positivliste for det offentlige build; deploy kun godkendte statiske assets; fjern interne docs, paid source/PDF og driftsscripts fra deploy-artefaktet; opdatér CI til at deploye det verificerede output.
- Accept:
  - CI/deploy-manifestet indeholder ingen `*.md`, `deliverables/`, `POSTS/`, `ops/`, `.git`, credentials eller uvedkommende produkter.
  - Smoke-test mod det byggede output finder 0 interne/paid-filer.
  - Alle offentlige sider, CSS, JS, billeder og plugin-download bevarer 200.
  - Ingen ny betalt templatekopi oprettes i repoet; erstatningsforslag ligger under `❓ Til Mads`.

### 9. Gør kvalitetsgaten permanent i CI

- Status: `TODO`
- Fejl: 0/2
- Begrundelse: Nuværende deploy-workflow uploader `site/` uden PHP-lint, build eller SEO-check, så en lokal grøn gate kan regressere i CI.
- Scope: kør relevante PHP-lints før deploy; kør EUComply build + SEO fra en reproducerbar checkout af sibling-kontraktet; håndtér at kun `auditedwp` er tilgængelig; adskil verification fra selve Pages-upload.
- Accept:
  - En PR med PHP-syntaksfejl eller SEO-fejl kan ikke deploye.
  - CI logger exit code og kørte command.
  - Secrets, `.env*` og deploy credentials indgår aldrig i logs eller build-output.
  - Den lokale missionsgate og CI-kommandoer stemmer overens.

### 10. Forbedr konvertering efter ærlig baseline

- Status: `TODO`
- Fejl: 0/2
- Begrundelse: Først en sand baseline giver valide salgstal og bedre prioritering; skærefulde claims oven på en defekt købsrejse skader tillid.
- Scope: én tydelig CTA pr. localized side; fri scan → problem → Pro; fjern døde/forkerede “contact”, refund-, gratis-trial- og konto-claims; tilføj dokumenteret analytics først når privatliv og baseline er korrekt.
- Accept:
  - EN/DA/DE/FR har ingen 404, død knap eller fejl canonical.
  - Én CTA pr. side fører til det kontraktfikserede Stripe-link.
  - Baseline metrics kan skelne egne testbrugere fra reelle kunder; rapportér 0 hvis overhovedet ikke kan dokumenteres.

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

## ❓ Til Mads

1. **Hosted Pro og plugin-Pro:** skal den nuværende `eucomply-pro`-nøgle eksplicit give både plugin-dokumenter og hosted-funktioner, eller skal plugin-dokumenterne være en del af et senere samlet Pro? Indtil dette er afklaret, sælger vi kun plugin-dokumenterne.
2. **Betalt navn:** EUComply Pro-navnet må ikke ændres. Forslag til den senere enterprise/self-service-plan: **EUComply Agency** (bureau/white-label), **EUComply Monitor** (daglig drift) eller **EUComply Bureau** (flere kundersider).
3. **Eksponerede templates:** de eksisterende betalte kilder/PDF'er har været offentlige. De bør regnes som kompromitterede; eventuelle nye eller forbedrede versioner skal udvikles i et privat repo og leveres fra CF KV. Skal de gamle produkter trækkes fra salg, eller kræver de en ny privat v1?
4. **DevNotify:** `devnotify/src-tauri/src/lib.rs` bruger fortsat Lemon Squeezy og har intet Stripeprodukt. Kræver den et nyt produkt/key før migrering?
5. **Refund-/skattecopy:** hvilken helt konkrete refund- og invoice-/OSS-proces skal de fire prissider beskrive? Stripe er ikke Merchant of Record, så den nuværende tekst skal fjernes, indtil en dokumenteret proces findes.

## Kendte lavprioritets-rester

- `deskuptime/` er en forældet kopi med gammel Lemon Squeezy-kode, selvom sitens DeskUptime-side allerede bruger Stripe. Fjern kopien fra EUComply-deploy eller markér repoet tydeligt som legacy; den rigtige app ligger i sit eget repo.
- DevNotify er et separat produkt og skal ikke blandes ind i EUComply-opgaverne; venter på Mads' Stripe-kontrakt.
- Gamle root-manifester, 1.2.0-arkivet og legacy-stores skal fjernes fra offentlige/aktive paths, når deploy-hygiejnen løses.
- Ingen npm-publish, Chrome Web Store-upload, AMO/VS Code Marketplace/Homebrew-upload, git-tag eller release må ske fra agenten.

## Deploy-log

- 2026-09-25: Research-plan oprettet på commit `fba1971`; endnu ingen `site/**`-ændring og derfor ingen forventet deploy fra denne iteration.
