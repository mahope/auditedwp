# Den solgte API uden en dør ind i den

Opgave 104, 28. september 2026.

## Fundet

`/vs/termly/` lovede i sin sammenligningstabel **"API access: Free API + CLI"**
for den gratis udgave. Det var det eneste sted på sitet, der lovede
API-adgang — og der var ingen dokumentation at gå ind ad.

En udvikler der gætter de URLs en dokumenteret API plejer at have:

| sti | målt 28/9 |
|---|---|
| `/api/` | findes ikke (404) |
| `/docs/` | findes ikke (404) |
| `/developers/` | findes ikke (404) |
| npm-pakken | `examples/curl.sh`, `python.py`, `node.js` — men ingen på sitet |

**Det værre var, at API'et virker.** Fire endepunkter svarer 200 i dag:

```
GET  /scan?url=webflow.com   200 application/json
GET  /stats                   200 application/json
GET  /config                  200 application/json
POST /subscribe               200 application/json
CORS                          Access-Control-Allow-Origin: *  (målt på OPTIONS-preflight)
```

Så en læser der finder vejen hjem får et virkende svar om en **gratis**
tjeneste, og en læser der ikke gør, må formode at den er uafsluttet eller
dyr. Begge fejl er dyrere end den reelle pris.

### Det var otte sider, ikke én

Planen nævnte `/vs/termly/`. Da porten målte træet, fandt den **syv**
`vs/*`-sider med samme løfte i samme tabelrække:

`vs/complianz` · `vs/cookiebot` · `vs/enzuzo` · `vs/iubenda` ·
`vs/onetrust` · `vs/termly` · `vs/usercentrics`

Alle otte skrev "Free API" i den kolonne der beskriver *vores* gratis
udgave, og ingen af dem linkede nogen sted. R2 i porten er derfor skrevet
til at ramme den **løfteform** og ikke siden — ellers ville den næste
sammenligningsside kunne love det igen uden at blive dømt.

## Rettelsen

### 1. `/api/` — dokumentation der kun siger sandheden

Siden er skrevet **kun** ud fra det der var målt live 28/9 10:00 UTC. Der
er ingen syntaks der ikke svarer, og intet om frekvensen af et kald der
ikke findes:

* Fire endepunkter, hver med sit rigtige svar målt med `curl`.
* Svartidsfeltet for `/scan` er målt: `url`, `platform`, `scannedAt`,
  `durationMs`, `score{passed,total,pct}`, `checks` (ni), `disclaimer`.
* Fejlkoderne er målt, ikke gættet: `400` (mangler `url`), `404` (anden sti),
  `422` (`/subscribe` med testadresse), `429` (over 10/min pr. IP), `502`
  (læsesitet ikke).
* Ét eksempel på et fejlet check står ordret som `checks`-objektet
  leverede det, afkortet til tre felter.

**Tre ting står der, fordi de er sande og ikke fordi de sælger:**

1. **`/stats` er ikke et brugerantal.** Tælleren trækker vores egne
   røgtests med. Målt 28/9: 578 scans, hvoraf `192.0.2.1` stod for 196,
   `198.18.0.1` for 193 og en `.invalidtld`-vært for 50 — altså omkring
   tre fjerdedele fra automatiske kørsler mod reserverede adresser. Siden
   siger det, fordi `AGENTS.md`s egen regel siger, at et tal skal kunne
   forklare hvor det kommer fra.
2. **Scoren i JSON'en er ikke den delte.** Den er `passed/total` over alle
   ni checks, inklusive de fire der kun giver mening på bestemte
   sidetyper. Den [CLI](/cli/) er den build der fortæller hvilke den ikke
   talte med. Siden siger det og peger på CLI'en i stedet for at lade
   læseren tro at 44 % er et fuldt mål.
3. **Den udgivne worker er en ældre build end motoren i repoet.** Derfor
   returnerer API'et det rå ni-tal og ikke `pct_applicable`. Det er
   sandt i dag, og det står som en forskel — ikke som et løfte om en
   næste version. Deployering af den nye worker er spørgsmål 9.

Købsvejen er **én** knap til Pro-linket fra kontrakten, i en boks der siger
hvad Pro **er** i dag: WordPress-plugin, daglig re-scan i eget WordPress,
de seneste 12 scans, mail når et check bryder, HTML-rapport. Hosted
monitoring er ikke med — samme ærlighed som `/cli/` og `/pro/`.

### 2. Syv købsveje i de otte tabeller

Celleformen `<td class="check">Free API + CLI tool</td>` blev til
`<td class="check"><a href="/api/">Free API</a> + <a href="/cli/">CLI tool</a></td>`.
"Free API" peger på dokumentationen, "CLI" på CLI'en. Cellens `.check`-stil
gælder begge links, så rækken ser uændret ud.

### 3. `GET /` svarede 404 — død kode i workeren

Fundet under målingen, ikke ved læsning af optrækket:

```js
const path = reqUrl.pathname.replace(/\/+$/, "") || "/";
...
if (request.method === "GET" && path === "") {   // ← aldrig sandt
```

`|| "/"` gjorde at `path` aldrig kunne være den tomme streng, så
informationsgrenen var død kode, og `GET /` faldt igennem til
`404 Not found`. Målt live: `GET /` → 404.

Rettelsen er at fjerne `|| "/"`. Ruterne er nu:

| sti | `path` | svar |
|---|---|---|
| `/`, `//`, `///` | `""` | service-info |
| `/scan`, `/scan/` | `/scan` | scan |
| `/stats` | `/stats` | tæller |
| alt andet | ruten | `404` |

Verificeret mod normaliseringen direkte, og `test_worker_security.mjs`
(kørende mod den udgivne worker) består de 47 checks uændret.

**Dette deployes ikke i denne iteration.** `worker-scan/` kan kun
publiceres med `wrangler deploy` = spørgsmål 9. Kilden er rettet og
porten måler kilden, så live `GET /` svarer 404 indtil et menneske deployer.
Det er derfor `/api/` **ikke** dokumenterer `GET /`.

## Porten: `tools/check_api_docs.mjs` (trin 33)

Fire regler, alle målbare mod **repoets egne filer**. Ingen ringer til den
udgivne worker, så porten dør ikke i CI af et netværkshicik.

| regel | hvad den dømmer | selftest-case |
|---|---|---|
| **R1** | Et `data-endpoint` i `<main>` på `/api/` skal være en rute i `worker-scan/index.js` | dokumenteret rute, der ikke findes |
| **R2** | Enhver side der skriver "free api" / "api access" skal linke til `/api/` | løfte uden dør |
| **R3** | `path === ""` må ikke være død kode efter normaliseringen | den `\|\| "/"`-fejl |
| **R4** | `/api/` skal stå i `PUBLIC_DIRS` | siden er ikke publiceret |

To valg der gør porten skarpere end en tekstregel:

**Endepunkter erklæres, de gættes ikke ud.** R1 læser `data-endpoint`-markører
i `<main>`, samme greb som `data-product` i `check_cta.py`. Kun `<main>`:
sidefoden indeholder BugBottles egen
`data-endpoint="https://mahope.tools/api/bugreport"`, som er et andet API
og ikke en rute i vores worker.

**R2 ser på løfteformen, ikke på ordet.** En regel der greb på `api` ville
være rød på `eucomplypro.com/api/` selv — altså på den side, der er lavet
for at fjerne fejlen.

Selftesten bygger et grønt fixture-træ og bryder én regel ad gangen.
Den grønne case er tillige rød, når den brydes; ellers kunne porten være
grøn af en grund den aldrig har efterprøvet.

`SELFTEST GRØN — alle 5 negative cases fanges`.

## Hvad der ikke er gjort

* **Deploy af workeren.** Rettelsen af `GET /` ligger i kilden og måles
  der, men live rettelsen kræver `wrangler deploy` (spørgsmål 9).
* **Oversættelse til DA/DE/FR.** `/api/` er kun EN. `check_locale_parity`
  kræver kun symmetri for `index.html`, `pro/index.html` og
  `pricing/index.html`, så porten er grøn. At en udviklerside kun findes på
  engelsk er et reelt valg om tid, ikke en forglemme — se næste iteration.
* **Skabelonernes filer.** Uændret. De ligger i Cloudflare KV og er ikke
  dette repo's sag.
