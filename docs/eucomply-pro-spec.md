# EUComply Pro — spec for den hosted betalte oplevelse

Kilde: missionen af 25. september 2026, `IMPLEMENTATION_PLAN.md` opgave 2, og audit af koden i
commit `19f1aa5`.

Status: **spec, ikke implementeret.** Alt markeret `ROADMAP` er ikke bygget, ikke testet og må
ikke sælges, før gateen i afsnit 17 er grøn for den pågældende evne.

## 1. Formål og regler

Specen definerer, hvad EUComply Pro skal være for et bureau eller en virksomhed, og gør de seks
betalte evnegrupper til ubeddede, testbare dele: daglig re-scan, 30 dages historik, kundespecifik
rapport, flere sites, mail-alarmer og live badge.

Regler, der ikke kan forhandles:

- **Ét produkt.** `product` er `eucomply-pro`. Ingen nye Stripe-produkter, priser, nøgler eller
  redirect-URL'er. Betalingslinket er udelukkende
  `https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03` (79 USD pr. website pr. år).
- **Ingen Stripe-nøgler i kode, sider eller workers.** Kunden bruger kun betalingslinket og
  licens-API'et.
- **Licensen er sandheden.** Entitlements afledes alene af svar fra
  `https://mahope.tools/api/license/{activate,validate,deactivate}`. Lokal cache er en
  nødbremse, aldrig en selvstændig kilde til Pro-status.
- **Ingen løfter før kode.** `tools/check_pro_claims.py` dækker alle kundende flader
  (`site/**/*.html`, `llms.txt`, `llms-full.txt`, plugin-readme) og skal udvides, så en
  `ROADMAP`-evne ikke kan omtales som nutidig der. Specen selv beskriver roadmap, så den skal
  ikke lægges ind i claims-scanningsfladen.
- **Ingen betalt skabelonindhold i dette offentlige repo.** Levering fra privat lager/CF KV.

## 2. Tre produktoverflader, uden overlap

| Overflade | Kunde | Betalt i dag | Bevis i kode |
|---|---|---|---|
| Gratis scanner (web + CLI) | Alle | Nej. Ét resultat pr. kald, ingen historik, ingen konto. Lokalt gemmes kun 6 seneste scanninger i browseren. | `shared/scan-engine.js:194-448`, `worker-scan/index.js:110-154`, `site/assets/site.js:301-337` |
| WordPress-plugin Pro | WordPress-sites | Ja. Licensen giver redigerbare HTML-starthtml til DPA/NIS2-DORA/EAA plus en HTML-rapport fra seneste **lokale** WP-scan. | `plugin/eucomply.php:966-1109`, `:824-964` |
| Hosted Pro (`ROADMAP`) | Bureauer og virksomheder | Nej. Denne spec. | Mangler; se afsnit 16 |

Adskilnelsen er skarp, fordi den betalte værdi er forskellig:

- **Plugin Pro** er lokalt: intet forlader sitet, ingen historik, intet hosted, intet badge.
- **Hosted Pro** er drift: historik, alarmer og rapporter om kundens *egen* website.
- **Gratis scanner** er funnelen og forbliver ubetalt. Den må ikke miste de ni tjek, og den må
  ikke få en del af Pro-kapaciteten lagt i vejen for nye brugere.

**Samme site med plugin og hosted:** De to er uafhængige. Pluginen scanner selv lokalt en gang
om ugen (`plugin/eucomply.php:101-104`), og hosted scanneren en gang pr. døgn. Begge henter
sitet, og det er forventeligt. Reglen er, at **kun hosted-workeren skriver i hosted-historikken**,
og at pluginens lokale HTML-rapport og hosted-PDF'en aldrig blander data. Dashboardet skal sige
det, når et site er dobbeltregistreret, så kunden ikke tror, at de betaler for det samme to
gange.

**Ukendt, låst til Mads (`❓ Til Mads` punkt 1).** Om den nuværende nøgle skal give både
plugin-dokumenter og hosted-funktioner. **Default er plugin-only**, fordi det er det eneste
betalte produkt, der virker i dag. Denne spec beskriver den hosted del under den forudsætning, at
Mads bekræfter, at samme nøgle også giver hosted-funktioner. Hvis svaret bliver "split", kræver
det et nyt Stripeprodukt og dermed en ny beslutning fra Mads — det er ikke noget, en agent kan
opfinde.

## 3. Licens- og enhedsbinding

### 3.1 Kundenes købsrejse

1. Kunden læser `/pro/` eller `/pricing/` (EN/DA/DE/FR) og trykker den ene købsknap.
2. Stripe-linket sælger `eucomply-pro`. Antal websites vælges ved køb ifølge kontrakten; det er
   en antagelse fra kontrakten og ikke verificeret i repoet, fordi Stripe-konfigurationen ikke
   findes her.
3. Efter betaling lander kunden på `https://mahope.tools/thanks?session_id=…`, som viser
   licensnøglen, og den sendes også pr. mail fra Stripe.
4. Kunden indsætter nøglen i pluginens indstillinger og/eller i det hosted dashboard.

Repoet indeholder ingen Stripe-session-, webhook- eller nøgleudstedelseskode. Leveringen af
nøglen er Stripe-side og uden for denne specs kodeansvar. Det er en **ukendt afhængighed**: hvis
`session_id` ikke rent faktisk viser nøglen, skal `/pro/thank-you/` sige det og pege på mailen.

### 3.2 Binding

- `license_key` er 32 hex-tegn (`/^[a-f0-9]{32}$/`), trimmet og lowercase før afsendelse.
- `device_id` er **ét website = én enhed**. Værdien er det fulde, lowercase værtsnavn uden port og
  uden sti, højst 128 tegn, præcis som pluginen gør i dag (`plugin/eucomply.php:1010-1016`).
- Hvis kunden har både plugin og hosted overvågning på samme site, skal dashboardet vise præcis
  det `device_id`, der bruges, så der ikke optages to enheder for ét website. Det afhænger af, om
  licensserveren behandler en ny `activate` med et allerede aktiveret `device_id` som idempotent
  uden at optage en ekstra plads. Det er uverificeret og står i `❓ Til Mads` punkt 6.
- Nøglen lagres **aldrig** i KV, i loggen eller i en URL. Workers har kun `keyHash =
  SHA-256(license_key)`, som bruges som account-id.
- Klienten sender nøglen i header `X-EUComply-License` på hvert kald, aldrig i query-streng, så
  den ikke havner i tilgængelighedslister eller analytics.

### 3.3 Verdict-modellen (skal deles af plugin og workers)

Pluginens `license_verdict()` (`plugin/eucomply.php:1094-1109`) er i dag eneste implementering.
Den skal flyttes til `shared/license-client.js` og genbruges af plugin, hosted worker og
dashboard, så de tre ikke kan drive fra hinanden.

| Licensserver-svar | Betydning | Klientens handling |
|---|---|---|
| `200` + `ok:true` + `valid:true` (validate) / `activated:true` (activate) | Gyldig | Pro aktiv, `lastOkAt = nu` |
| `200` + `ok:true` + forventet flag falsk | Ugyldig/udløbet | Lås, negativ cache 24 t |
| `200` med `ok` falsk, manglende svarfelt eller ulæseligt svar | Ukendt | **Midlertidig.** Grace, ingen lås |
| `400` | Forkert format | Lås |
| `403` | Udløbet, tilbagekaldt eller forkert produkt | Lås |
| `404` | Ukendt nøgle | Lås |
| `409` | Enhedsgrænsen nået | **Låser ikke nøglen.** Afvis kun den nye enhed/site, se 3.4 |
| `402`, `429`, `503`, andre `5xx`, timeout, netværksfejl | Midlertidig | Grace, se 3.5 |

Rækken af midlertidige svar skal afspejles ordret i implementeringen. En klient, der låser på et
`200 ok:false` eller et `429` fra licensserveren, låser betalende kunder ude — det er et
pungssynspunkt, ikke en detalje.

### 3.4 409 er en fejl i nutidens plugin

Pluginen behandler `409` som definitivt ugyldig (`plugin/eucomply.php:1105-1107`) og cacher
negative svar i 24 t. Det gør det umuligt at rydde en enhed og prøve igen, fordi pluginen aldrig
kalder `deactivate`. Før hosted Pro ships, skal pluginen:

1. skelne `409` fra de øvrige definitive fejl,
2. vise en handlingsanvisning — "enhedsgrænsen er nået, frigiv en maskine" — i stedet for den
   generiske "nøgle ikke accepteret",
3. få et `deactivate`-kald ved afinstallation eller eksplicit "frigiv denne enhed",
4. slette den negative cache, så re-check sker med det samme.

Det er en del af opgave 3 og en hård forudsætning for flere sites.

### 3.5 Offline-grace på 7 dage

- Positivt svar caches i 24 t.
- Ved `402`/`429`/`503`/andre `5xx`/netværksfejl bruges den cachede Pro-status i op til **7 dage**
  siden `lastOkAt`. Efter 7 dage går hosted Pro til read-only med en tydelig besked om fejlende
  licensserver. **Ingen data slettes, intet site fjernes** ved udløb — kunden skal kunne
  genoprette adgangen ved at prøve igen.
- Et definitivt ugyldigt svar låser med det samme, uafhængigt af grace. Grace må aldrig forlænge
  en udløbet licens.
- Gentagne fejl får en 1-times backoff, som pluginen allerede har
  (`plugin/eucomply.php:987-989`), så en nede server ikke gør hvert admin-kald til en
  10-sekunders timeout.

## 4. Multi-site-regel

- **Pris:** 79 USD pr. website pr. år. Ét website = én licensenhed = ét `device_id`.
- Tilføjelse: `activate` mod sitets værtsnavn, derefter skrives sitet. Ved `409` får kunden
  besked om, at planens antal er brugt, og at et site skal fjernes eller en enhed frigives først.
- Fjernelse: `deactivate` mod værtsnavnet, derefter sletning af site-data. Uden `deactivate`
  bliver enheden optaget, så UI'en skal sige "frigiv enheden", før sletningen bekræftes.
- Pause: bevaring af data og licensenhed, ingen scanninger og ingen alarmer. Pauser sites tæller
  med i kundens kvota.
- Canonicalisering: værtsnavn lowercases. `www.` fjernes **ikke** i `device_id`, fordi pluginen
  bruger det fulde værtsnavn. Til gengæld normaliseres registreringen, så den samme side ikke kan
  optages to gange med forskellig skrivemåde, og dashboardet viser altid den anvendte
  `device_id`.
- Hver konto må ikke overstige 200 sites uanset købt antal. Det er et misbrugsstop, ikke en pris.

## 5. Data- og adgangskontrakter

Alle kald er `POST` (undtagen offentlig badge og rapportdownload) med `Content-Type:
application/json`. CORS er **ikke** `*`: kun `https://eucomplypro.com` og de fire locale-rødder
tillades, og kun med `Content-Type` + `X-EUComply-License`. Fejl svarer altid med
`{ "error": "<kode>", "message": "<kort tekst>", "retryable": true|false }`.

### 5.1 Licensstatus

`POST /v1/license/status`

- Request: nøglen i header `X-EUComply-License`.
- `200`: `{ ok, product, plan, expires_at, devices_in_use, entitlement, grace_expires_at|null, checked_at }`
- `entitlement` er `hosted_pro` eller `plugin_only`, baseret på licensserverens `plan`. Det er
  *én* samlet rettighed, fordi licens-API'et ikke har felt-per-evne. Delvise rettigheder kan derfor
  ikke repræsenteres, og det skal ikke lade som om de kan.
- Det købte antal findes ikke i licens-API'et. `devices_in_use` er det nærmeste, og resten af
  kvoten afledes fra, hvornår `activate` svarer `409`. Det er ikke deterministisk nok til en
  kundevenlig kvotevisning, så indtil licensserveren udsteder antallet, viser dashboardet
  "købte websites brugt: N" og **ikke** en bar der påstår at være komplet. Dette er
  `❓ Til Mads` punkt 7.

### 5.2 Sites

| Kald | Request | Success |
|---|---|---|
| `POST /v1/sites` | `{ url, alert_email? }` | `201 { site_id, device_id, status, activated_at, license_calls, alert_email_status }` |
| `GET /v1/sites` | — | `200 { sites: [ … ] }` |
| `GET /v1/sites/{site_id}` | — | `200 { site, latest, history: [ …30 dage… ] }` |
| `POST /v1/sites/{site_id}/pause` | `{ paused: bool }` | `200 { site }` |
| `POST /v1/sites/{site_id}/alerts` | `{ enabled, email }` | `200 { site, alert_email_status, verify_token_sent: true }` |
| `POST /v1/alerts/confirm` | `{ token }` | `200 { ok, alert_email_status: "verified" }` |
| `POST /v1/sites/{site_id}/badge` | `{ enabled }` | `200 { badge: { site_id, snippet, verify_url } }` |
| `DELETE /v1/sites/{site_id}` | `{ release_device: true }` | `200 { ok, freed_device, purged_keys }` |
| `GET /v1/sites/{site_id}/report.pdf` | — | `200 application/pdf` |

- `license_calls` er `1` ved tilføjelse. Et `activate` med et allerede aktiveret `device_id`
  regnes som idempotent og optager ingen ekstra plads, forudsat at licensserveren opfører sig
  sådan (uverificeret, `❓ Til Mads` punkt 6).
- `alert_email_status` er `none` | `pending` | `verified` | `disabled`.
- En ukendt `site_id` eller en `site_id`, der ikke tilhører `keyHash`, giver `404 not_found` —
  aldrig `403`, så nøglens gyldighed ikke lækkes ved hjælp af id-formatet.

### 5.3 Alarmadresse skal bekræftes

Uden bekræftelse kan enhver sende mail til en fremmed adresse gennem vores afsender. Derfor:

1. `POST /v1/sites/{id}/alerts` med en ny adresse gemmer den som `pending` og sender en mail med
   et bekræftelseslink.
2. Linket er `POST /v1/alerts/confirm` med `{ token }`. Token er 32 hex-tegn, gemmes kun som
   SHA-256 i `pro:pending:{tokenHash}` med TTL 7 dage, bruges én gang og slettes ved brug.
3. Før bekræftelse sendes **ingen** alarmer for sitet, og dashboardet viser
   "afventer bekræftelse af mailadresse".
4. Bekræftede adresser kan ikke bruges til at sende til tredjeparter: de skal matche den adresse,
   kunden har bekræftet, og kvoten pr. konto deklareres eksplicit.

### 5.4 Rapportdownload

Rapporten er autentiseret på samme måde som alt andet: `X-EUComply-License` skal matche
`keyHash` for sitet. Serveren genererer filen ved forespørgsel fra hosted historik. Kunden skal
kunne hente sin egen rapport; en anden nøgle skal få `404`.

### 5.5 Offentlig badge

`GET /badge/{site_id}.json` — ingen nøgle, ingen email, ingen historie.

- `200 { site_id, host, score: { passed, total, pct }, last_scan_at, checks: { …9 korte statusser… }, disclaimer, verify_url }`
- `404 badge_disabled` når badge er slået fra, sitet er slettet eller licensen har udløbet.
- `429` med `Retry-After` ved over rate-limit.

Scoren kommer **kun** fra KV. Klienten sender aldrig en score ind, og payload'en indeholder ingen
rød URL-sti, ingen check-detaljer, ingen email og ingen historik. Værten er offentlig, fordi
badgen netop skal stå på sitet; opt-in er derfor påkrævet, før noget offentliggøres. Et gammelt
eller forfalsket payload kan derfor ikke få en badge til at vise en ny score — den hentes altid
fra workeren med `cache: "no-store"`.

### 5.6 Fejlkoder

| HTTP | `error` | Betydning |
|---|---|---|
| 400 | `invalid_request` | Mangler felt, dårlig URL, `device_id` for lang |
| 403 | `license_invalid` | Definitivt ugyldig, udløbet eller tilbagekaldt |
| 403 | `product_mismatch` | Nøglen tilhører et andet produkt |
| 404 | `not_found` | Ukendt site, ukendt `site_id` eller ikke-ejer |
| 404 | `badge_disabled` | Badge slået fra eller sitet slettet |
| 409 | `already_registered` | Samme site findes aller på kontoen. Prøves **før** kvotetjekket, fordi det er det mest forventede svar |
| 409 | `device_limit_reached` | Købt antal brugt. Låser **ikke** nøglen |
| 410 | `site_deleted` | Slettet site; genoprettelse kræver nyt `activate` |
| 422 | `url_not_public` | Privat, loopback, link-local eller ikke-HTTP(S) |
| 409 | `email_unverified` | Alarmer kan ikke slås til, før adressen er bekræftet |
| 429 | `rate_limited` | Slå rate-limit fra, prøv igen senere. Altid med `Retry-After` |
| 503 | `license_temporarily_unavailable` | Licensserver nede; grace gælder |
| 503 | `scan_backend_unavailable` | Scanmotor utilgængelig; seneste data vises med advarsel |

## 6. Daglig re-scan

- Ét scan pr. aktivt site pr. 24 t ± 4 t jitterspredning, så lasten ikke falder i ét spike.
- Nye sites får et førstescan ved tilføjelse, så dashboardet ikke er tomt i en dag.
- Cronen scanner højst `SCAN_BATCH` sites pr. invocation. Uden batchning kører dagens cron i
  `worker-watch/index.js:125-126` alle sites parallelt i én invocation, hvilket på en
  Workers-gratsplan kan afbrydes af subrequest-grænsen. Det er ikke acceptabelt for betalt drift.

### 6.1 Due-kø

`SCAN_BATCH` afhænger af Workers-planens faktiske grænser, som skal verificeres og noteres, før
den sættes. Selve køen er en del af designet, ikke et navn:

| Nøgle | Værdi | TTL |
|---|---|---|
| `pro:due:{YYYYMMDDHH}:{keyHash}:{site_id}` | `{ url, device_id, due_at, attempts }` | 3 dage |
| `pro:claim:{site_id}` | `{ keyHash, slot, claimed_at }` | 10 min |

Cronen lister `pro:due:` med cursor, tager op til `SCAN_BATCH` nøgler og **claimer** hver enkelt
med `pro:claim:{site_id}` før scanning. Claim-nøglen forsvinder af sig selv, hvis workeren dør, så
et site ikke kan sidde fast. Efter scan skriver workeren næste time-slot med TTL 3 dage, så
forsinkelse ikke spiser plads. KV har ingen atomisk pop, så claim er best-effort; derfor er
skrivningen af dagens resultat **idempotent** — samme dag og samme site giver samme nøgle, og den
skrives med samme indhold. En dobbeltscan på grund af tabt claim er derfor harmløs og tæller
kun én dagshistorik.

## 7. Historik: 30 dages per-check

**Målet er eksplicit: dagens gemmer kun `{date, score, passed, total}`**
(`worker-watch/index.js:68-69`, `:132-133`). Uden per-check-status kan hverken historik med
regressioner eller pass-til-fail findes. Derfor:

- Dagscoren bliver pr. døgn (`YYYY-MM-DD` UTC), 30 dages historik, TTL 40 dage.
- Hver dagscanning gemmer alle ni checks med tri-state: `pass` | `warn` | `fail`.
- Den eksisterende samlede score ændres ikke. Den tæller i dag kun `pass`, og de tjek, der sætter
  `warn`, sætter typisk også `pass: false` (`shared/scan-engine.js:232-233`, `:296-297`,
  `:318-319`, `:396-397`), så en advarsel tæller i summen som et fejslag. Det er en
  forhåbentlig unædig hensigt, som opgave 3 skal vurdere særskilt. **Indtil da** forbliver
  summen uændret, og alarmer samt historik bruger tri-state uafhængigt af den.
- Aggregatet `pct` er fortsat kun til visning og rapporter.
- Dashboard og rapport får pr. dag: score, antal bestået, og listen af checks, der skiftede til
  `fail` siden forrige dag.
- 30 dage betyder 30 **kalenderdage**. En manglende dag vises som en mangel, ikke som en gammel
  dags gentagne. Det er en bevidst korrektion af `slice(-30)`, som i dag tæller poster.
- Ingen kundedata eller email i klientlog eller på et offentligt endpoint.

## 8. Mail-alarmer

Fire alarmtyper, alle kun til en **verificeret** adresse, alle deduplikerede pr. dag:

| Type | Udløser | Indhold |
|---|---|---|
| `check_failed` | Ét check går fra `pass`/`warn` til `fail` | Checknavn, gammel status, tidspunkt, sidste rettelse, link til sitets private resultatside |
| `site_down` | To scanninger i træk fejler | Sidste succes, fejlårsag, link til kundens dashboard |
| `scan_stale` | To planlagte scanninger er sprunget over | "Vi har ikke kunnet scanne dit site" med seneste tidspunkt |
| `recovered` | Et tidligere fejlet check består igen | Kort kvittering. Valgfri pr. site, standard slået fra |

Regler:

- Én mail pr. ny fejl. Gentagne cron-fejl sender ikke flere.
- Dedupe-nøgle: `pro:alertsent:{keyHash}:{site_id}:{type}:{check}:{YYYY-MM-DD}`, TTL 45 dage.
- Plain text med URL til den private resultatside. Ingen vedhæftninger.
- `List-Unsubscribe` skal sættes, hvis Resend-kontoen understøtter det; ellers skal hver mail
  indeholde et link til at slå alarmer fra.
- Hver mail indeholder kundens website og tidspunkt, så en modtager, der har adgang til flere
  konti, kan se hvilken den er.
- Rektangulære fejl: `ALERT_KEY` mangler i dag (`worker-watch/wrangler.toml:16-18`), og
  `sendAlert`-resultatet kasseres (`worker-watch/index.js:138`). Begge rettes, og der sendes en
  synlig tilstand i dashboardet, så en kunde aldrig tror han overvåger noget, der ikke kører.

## 9. Kundespecifik rapport (formatvalg: PDF)

**Valg: PDF**, fordi bureauets leverance er den fil, kunden sender videre. Pluginens HTML-rapport
er en anden leverance og forbliver uændret.

- Servergenereret i workeren fra hosted historik, ikke fra pluginens lokale WP-state.
- Filen består filformatvalideringen: første fire byte er `%PDF-`, og svaret er
  `application/pdf`. Hvis vi en dag bruger et PDF-bibliotek, skal det være en afhængighed med
  egen audit, ikke en cdnext-ét.
- Rapporten indeholder: kundens brand, website, rapport-id, genereret tidspunkt, dagens ni
  resultater, 30 dages scorekurve, listen af checks der gik til `fail` i perioden med
  rettelsestekst, og den eksisterende "ikke juridisk rådgivning"-tekst.
- Kun den seneste tilgængelige historik; rapporten er et øjebliksbillede, ikke et løbende
  dokument.
- Mønstret `/pro/sample-report/` er et statisk koncept, ikke en kunderapport, og skal mærkes
  "eksempel" og holdes uden for kundeloggen.
- Filnavn: `eucomply-{host}-{YYYY-MM-DD}.pdf`.

## 10. Badge og offentlig verifikationsside

- Stabilt offentligt `site_id`, 32 hex-tegn, tilfeldigt og uforudsigeligt. Det er en offentlig
  verifikations-id, ikke en adgangsnøgle.
- Badgen er opt-in pr. site. Uden opt-in findes ingen offentlig nøgle, så endpointet heller ikke
  afslører, om en adresse er kunde.
- Embed-scriptet `site/assets/eucomply-badge.js` henter kun `GET /badge/{site_id}.json` og
  renderer **kun** score, tidspunkt og link. Det må aldrig falde tilbage på lokale, hardcoded
  eller URL-styrede værdier — det er den nuværende widgets fejl.
- Den offentlige verifikationsside `/verify/{site_id}/` viser samme data med sidste
  scanningstidspunkt og sidste tjekstatus.
- **Før dette er bygget, forbliver badge-siden på "illustrativ"**, som den gør i dag.

## 11. Dashboard

`/pro/dashboard/` bliver fra konceptdemo til kundedashboard. Kravene:

- Ingen hårdkodede tal, ingen `Math.random()`, ingen eksempelrækker i kundemodus. Alt kommer fra
  `worker-watch`.
- Adgang: kunden indsætter licensnøglen, som holdes i `sessionStorage` (aldrig `localStorage`)
  og sendes i headeren på hvert kald. Der er ingen adgangskode og ingen ny konto.
- Visninger: sites med seneste score, seneste scanningstidspunkt og `scan_status`; 30 dages
  historik pr. site; nye fejl med rettelsestekst; alarmer pr. site; rapportdownload; badge-snippet.
- Handlinger: tilføj, sæt på pause, slet, slå alarmer til/fra, slå badge til/fra.
- Ved licensserverfejl vises cached adgang med udløbsdato og `read-only`-tilstand. Når grace er
  udløbt, vises login/setup-state, ikke kundemockdata.
- Uden gyldig entitlement vises login/setup-state, ikke kundedata.
- Den eksisterende demo bliver bevaret som et separat, tydeligt mærket koncept, så den fortsat kan
  bruges i salgsmateriale uden at forveksles med et kundedashboard.

## 12. Retention, sletning og privatliv

### 12.1 Retentionsperiode

| Data | Butik | Retention |
|---|---|---|
| Licensstatus/cache | `pro:ent:{keyHash}` | 24 t cache, `lastOkAt` tilbageholdes til sletning |
| Kontometa | `pro:acct:{keyHash}` | Til sletning. Efter licensudløb ryddes sitene efter 30 dage, jf. 15.5 |
| Site | `pro:site:{keyHash}:{site_id}` | Til sletning |
| Dagens scanninger | `pro:day:{keyHash}:{site_id}:{YYYY-MM-DD}` | TTL 40 dage |
| Alarm-dedupe | `pro:alertsent:…` | TTL 45 dage |
| Due-kø og claim | `pro:due:…`, `pro:claim:…` | TTL 3 dage hhv. 10 min |
| Rate-limit | `pro:rl:…` | TTL 60-300 s |
| Ubekræftet email | `pro:pending:{tokenHash}` | TTL 7 dage |
| Offentlig badge | `pro:badge:{site_id}` | Til slå fra/sletning |

### 12.2 Sletning

- `DELETE /v1/sites/{id}` frigiver først enheden (`deactivate`), sletter derefter site, dags-,
  due-, dedupe- og badge-nøgler i én bevægelse, og svarer med antal slettede nøgler, så kunden kan
  dokumentere det.
- Kontodeletion sletter alle sites og efterlader kun en talt, ikke-identificerbar kontoindgang. Den
  skal kunne ske på mail til Mads, indtil en selvbetjeningsvej findes, og det skal stå på
  privatlivssiden.
- Der er ingen rå kundedata i klientlog. Keys, emailadresser og fulde URL-stier må ikke logges.

### 12.3 Privacy-datamappe

| Datakategori | Formål | Retsgrund | Modtager | Retention |
|---|---|---|---|---|
| Licensnøglens hash, værtsnavn, site-id | Leverance af betalt tjeneste | Kontrakt | Cloudflare KV | Til sletning |
| Scanresultater og historik | Leverance af overvågning og rapporter | Kontrakt | Cloudflare KV | 40 dage |
| Verificeret alarmadresse | Alarmer | Kontrakt | Cloudflare KV, Resend | Til sletning |
| Ubekræftet alarmadresse | Bekræftelsesmail | Samtykke | Cloudflare KV, Resend | 7 dage |
| Adressens IP ved rate-limit | Misbrugsforebyrgelse | Legitim interesse | Cloudflare KV | 60-300 s |
| Eksisterende: 365-dages scanaggregater pr. værtsnavn | Statistik, ikke leverance | Legitim interesse | Cloudflare KV (`RATE`) | Op til 365 dage |
| Eksisterende: e-mail på scannerens `/subscribe` | Nyhedsbrev, ikke leverance | Samtykke | Cloudflare KV (`SUBSCRIBERS`) | Uden TTL i dag — skal have en |
| Stripe-køb | Betaling og faktura | Kontrakt, lovpligt | Stripe | Stripe-vilkår |
| Licensserver-kald | Entitlement | Kontrakt | mahope.tools | Deres policy |
| Feedback via BugBottle | Support | Samtykke | jsDelivr, mahope.tools | Deres policy |

Både de to eksisterende rækker skal have en retention-periode, før hosted Pro åbner. Den
eksisterende privatlivsside skal desuden ophæve den modsigelse, at footeren siger "no trackers",
mens BugBottle indlæses fra jsDelivr på hver side, og den skal nævne de to nye KV-butikke,
verificeret email og hvordan et site slettes.

**Åbent juridisk spørgsmål (`❓ Til Mads`):** EUComply henter kundens website automatisk. For
kundens eget site er det en processoropgave, men scanneren kan ramme tredjepartsdomæner under
research. Det kræver en vurdering, før hosted Pro åbner, og det kan ikke afgøres af en agent.

## 13. Trusler og modstande

| Trussel | I dag | Krav til den hosted udgave |
|---|---|---|
| SSRF via redirect | Følger redirects uden at validere hvert hop (`shared/scan-engine.js:203-207`) | Valider destination ved hvert hop og opløst IP; afvis privat/loopback/link-local/CGNAT, også ved DNS-rebinding |
| Upassende renderede serverværdier | Scannerens egen side escaper `c.detail` (`site/scan/index.html:222-224`). Derimod renderer `site/shared/live-check-widget.html:33,37,39,42` `finalUrl`, `statusText` og `error` i `innerHTML` uden escaping, og de værdier kontrolleres af det scannede site | Escape eller `textContent` overalt. Widgeten kalder desuden DeskUptime-workeren og ligger uden for EUComply-gaten, så den tages op som egen opgave med Mads, ikke som en del af opgave 3 |
| Email-overtagelse | `/register` overskriver en andens email (`worker-watch/index.js:53-58`) | Verificeret email, ingen åben registrering, ingen ændring af ejer uden gyldig nøgle |
| Offentlig `/status` | Historie og registreringstidspunkt er offentlig | Bliver privat bag `keyHash`; kun badge-endpointet er offentligt |
| Nøglelækage | Ikke løst endnu | Aldrig i URL, log eller KV; kun SHA-256-hash; CORS-allowlist i stedet for `*` |
| Kapacitets-DoS | 200 sites globalt, ingen rate-limit på watch-workeren | Rate-limit pr. IP og pr. nøgle, batchgrænser, ingen synkron udgående hentning for uvedkommende |
| Stille cron-fejl | `catch { return; }` (`worker-watch/index.js:130`) | `scan_status`, fejlmail, synlig tilstand i dashboardet |
| Spoofet badge | Widgeten er statisk i dag | Badge læser kun workerens KV-værdi og slås opt-in |
| Supply chain | Ingen afhængigheder i dag | PDF skrives uden nye runtime-afhængigheder; ellers én ad gangen med audit |

## 14. Belastningstestmatrix

Skal køre før åbning, mod en staging-kopi af KV. Tal er krav, ikke kapacitet.

| Scenarie | Sites | Sites pr. konto | Forventet | Passkriterium |
|---|---|---|---|---|
| Enkelt kunde | 1 | 1 | Registrering + førstescan | `< 3 s` p95, ingen 5xx |
| Lille bureau | 10 | 10 | 10 aktiveringer | Alle 10 aktive, `devices_in_use` korrekt, ingen 409 |
| Stort bureau | 100 | 10 | 100 sites | 100 scanninger fordelt over dagen, ingen site tabt |
| Kvoten fuld | 1 | købt antal + 1 | 409 | Kun nyt site afvist, eksisterende sites fortsætter |
| Cron-batch | 200 | blandet | 24 t dækning | Hvert site får ≤ 1 scan/dag, p95 batch-tid under Workers-grænsen, ingen afbrudt invocation |
| Historik | 1 | 1 | 30 dage + 50 på hinanden følgende dage | 30 dage synlige, dag 31 vises ikke i 30-dages-visningen og ryddes ved TTL |
| Alarmer | 10 | 10 | 3 nye fejl samme dag | 1 mail pr. fejl, 0 dubletter, dedupe-nøgle læst |
| Licensserver nede | 10 | 10 | 503 i 7 dage | Fuld adgang alle 7 dage, read-only dag 8, ingen datatab |
| Rate-limit | 1 | 1 | 100 kald/min fra én IP | 429 med `Retry-After`, ingen skrivninger |
| Privacy | 10 | 10 | DSAR og sletning | 0 resterende kunder med nøgle, site, dagshistorik eller badge |
| Badge | 10 | 10 | 1 offentligt opslag | Kun valgte site-id svarer, ingen email eller histori i svaret |

Før hver kørsel skal Workers-planens faktiske subrequest-, CPU- og cron-grænser være verificeret
og noteret, fordi de afgør `SCAN_BATCH`.

## 15. Migrering fra den åbne beta

1. **Fase A, nu:** `/register`, `/status` og `/unregister` og deres KV forbliver uændrede, indtil
   opgave 3 leverer. Det er en ren sikkerhedsreparation på eksisterende ruter, ikke en
   migrering af dem.
2. **Fase B, opgave 3:** `/register` kræver licens. Den åbne formular på `/scan/` i alle fire
   sprog fjernes samtidig, fordi den ellers skaber gratis hosted drift. Copy-ændringen kræver en
   grøn claims-gate.
3. **Fase C, opgave 3:** `/status` bliver token-beskyttet. **Eksisterende beta-records uden
   licens** får en engangs-owner-token sendt til den email, de er registreret med, så de
   bevarer adgang til egen historik uden nøgle. Er den email ugyldig eller bounce'r, går
   recordet read-only og kan kun slettes. Det er den fairness, der gør det acceptabelt at lukke
   den åbne registrering.
4. **Fase D, opgave 4+:** Nye betalte kunder importerer deres gamle 30 dages *aggregerede*
   scorer én gang og markerer dem "historik fra beta, kun samlet score". Per-check-historikken
   starter den dag importen sker. Vi påstår aldrig, at retroaktiv historik findes.
5. **Fase E:** Efter licensudløb ryddes sitene efter 30 dage, jf. 12.1. Kunden advares i
   dashboardet 30 dage før, og rydningen logges med nøglehash og antal nøgler, uden rå
   kundedata.
6. **Fratrådning.** Den offentlige `/status` og den åbne `/register` fjernes først, når sidste
   betalte kunde er migreret og ingen ubetalte beta-records er tilbage. Fratrådningen er en egen
   opgave med egen kundekommunikation.

## 16. Bygge- og fejlrækkefølge

Rækkefølgen er låst, fordi hvert led er en forudsætning for det næste:

1. **Opgave 3** — SSRF, privat `/status`, email-overtagelse, 409-semantik og `deactivate` i
   pluginen, sletning. Uden dette er der ikke sikkert at sælge hosted drift.
2. **Opgave 4** — per-check historik og pass-til-fail-mail. Først her bliver historien reel.
3. **Opgave 5** — kundespecifik PDF-rapport.
4. **Opgave 6** — live badge og offentlig verifikationsside.
5. **Opgave 7** — entitlement-aware dashboard og multi-site.
6. Copy-opdatering som sit eget led efter hver grøn gate, aldrig før.

## 17. Definition of done for hver evne

En evne er kun "included", når alle punkter er sande:

- Funktionen er implementeret uden at røre den gratis scanners ni tjek.
- Automatisk test dækker de konkrete acceptkriterier i `IMPLEMENTATION_PLAN.md` for opgaven.
- `tools/check_pro_claims.py` er udvidet til at dække den nye evne på alle kundende flader og er
  grøn.
- Privacy-siden og belastningstestmatrixen er opdateret for de nye data og den nye last.
- EN/DA/DE/FR er konsistente, og der er præcis én købsknap med kontraktlinket pr. side.
- Deployet og verificeret på indhold, ikke på HTTP 200.

## 18. Åbne beslutninger

1. Giver `eucomply-pro` både plugin-dokumenter og hosted-funktioner, eller skal de splittes?
   Default indtil da: plugin-only.
2. Hvilken konkret refund- og fakturaproces skal prissiderne beskrive, når Stripe ikke er Merchant
   of Record?
3. Hvem er dataansvarlig for de scannede websites, og hvordan autoriseres den daglige hentning?
4. Skal de gamle, eksponerede betalte templates trækkes fra salg, eller laves nye private versioner?
5. Er `ALERT_KEY` sat i produktion for `eucomply-watch`? Uden den sender overvågning ingen mail,
   og det skal rettes eller fjernes som produktlov.
6. Er `activate` med et allerede aktiveret `device_id` idempotent uden at optage en ekstra enhed?
7. Findes der en deterministisk måde at få det købte antal websites ud af licensserveren, så
   dashboardet kan vise kvoten uden at gætte via 409?
