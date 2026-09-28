# En indekserbar side skal stå i sitemap.xml

**28. september 2026 · opgave 107 · `ceo/sitemap-indekserbar`**

## Fundet

`site/sitemap.xml` havde **209** `<loc>`. Det publicerede træ har **223**
sider. Der var altså 14 sider, der aldrig er blevet meldt til nogen.

13 af dem er korrekt væk, og det er ikke en fejl at de mangler:

| Side | Hvorfor den ikke skal i sitemap |
|---|---|
| `/search/`, `/da/search/`, `/de/search/`, `/fr/search/` | `<meta name="robots" content="noindex,follow">` |
| `/pro/dashboard/`, `/pro/thank-you/` | `noindex` |
| `/tools/` | `noindex` |
| `/cookie-policy-generator/`, `/privacy-policy-generator/`, `/refund-policy-generator/`, `/terms-of-service-generator/`, `/impressum-generator/` | `noindex` |
| `/deskuptime/thanks/` | `noindex` |

Den fjortede var **`/api/`** — og den har **ingen robots-meta overhovedet**.
Den er altså indekserbar, den ligger i `build_public_tree.py`s `PUBLIC_DIRS`
og bliver publiceret, og den er den eneste dokumentation af en tjeneste der
faktisk virker: fire endepunkter, `Access-Control-Allow-Origin: *`, to
færdige kodeeksempler, et JSON-eksempel taget fra den kørende service, en
købsknap til Pro og en tekst der siger hvad API'et *ikke* gør.

Det er den dør, hele API-argumentationen hænger på. Og den lå i mørket.

## Hvorfor ingen port fandt den

Der var allerede en port til præcis den overflade:
`tools/check_api_docs.mjs` (trin 34) har fire regler, bl.a. **R2** — "en
side der lover API-adgang skal linke til `/api/`" — og **R4** — "`/api/` skal
stå i `PUBLIC_DIRS`". Den er grøn, og den har gjort sit arbejde: siden findes,
linket findes, og den publiceres.

Ingen af dem spurgte det næste spørgsmål: **er den meldt til nogen?** De tre
egenskaber er uafhængige, og kun den første var dømt. Det er samme fejlklasse
som opgave 106 (konkurrentpriser): en overflade der er rigtig, men ingen der
følger den hele vejen ud til læseren.

Til værre er `/api/` heller ikke fundet på en anden måde. Den har ingen
`hreflang` og ingen locale-spejling, så en dansk, tysk eller fransk søgning
rammer den slet ikke.

## Rettelsen

**1. Én linje i `site/sitemap.xml`.** `/api/` står først, med
`<lastmod>2026-09-28</lastmod>`. Ingen `xhtml:link`-alternativer, fordi siden
ikke har nogen — og den får dem ikke ved at få en række henvisninger til
sider, der ikke findes.

**2. `tools/check_sitemap.py`, trin 36.** Fire regler, fordi begge retninger
er fejl:

| Regel |Hvad den dømmer |
|---|---|
| **R1** | En publiceret, indekserbar side skal have en `<loc>`. *Denne fangede fundet.* |
| **R2** | En `<loc>` skal være en side, der findes. En sitemap-peger på en død adresse, og den dør stille. |
| **R3** | En `<loc>` skal være præcis sidens egen `rel=canonical`. Samme side under to adresser er to sider for søgemaskinen. |
| **R4** | En `noindex`-side må ikke stå i sitemap. Ellers beder vi om at blive indekseret og forbyder det i samme linje — og de 13 korrekte undtagelser bliver umulige at skelne fra de nye fejl. |

R1 alene ville have løst dagens fund. R2–R4 er der, fordi de er den anden
retning af den samme løgn, og fordi R4 er det, der holder porten brugbar:
den 13 korrekte undtagelser er præcis dem, R1 ikke må slå alarm på.

**Sidenes liste læses fra `build_public_tree.py`s egen `PUBLIC_DIRS`**, ikke
fra en kopi her. Ellers kunne de to lister glide fra hinanden, og en
forældet kopi ville få porten til at dømme sider, der ikke engang udgives.

## Bevis

Porten var **rød på den eneste sande fejl** før rettelsen:

```
publicerede sider: 223 — 210 indekserbare, sitemap-loc: 209
FEJL R1 api/ er indekserbar men staar ikke i sitemap.xml
```

Selftesten er **5/5 negative cases**, og de er mutationer mod repoets egne
filer, ikke fixtures:

| Case | Forventet |
|---|---|
| R1 — `/api/` fjernet fra sitemap igen | fanges |
| R1 — en helt ny indekserbar side, aldrig meldt | fanges |
| R2 — `<loc>` uden side | fanges |
| R3 — `<loc>` uden trailing slash | fanges |
| R4 — `/search/` (noindex) i sitemap | fanges |

Efter rettelsen: `210 indekserbare, sitemap-loc: 210`, **SITEMAP GRØN**.

## Baseline og målepunkt

Plausible 28 d: **1 besøger**, bounce 100 %, kun Direct / None — tallet er
ikke et målepunkt for dette. Det, der *er* målbart, er indekserbarhed:
`210 → 211` sider i sitemap mod `223` publicerede, hvor forskellen på 12 er
de `noindex`-sider, der med vilje ikke er med.

Det næste synlige resultat er en `/api/`-URL i Google Search Console. Den kan
først ses efter en indeksering, og repoet har ingen Search Console-adgang, så
det bliver noteret når nogen har det.

## Hvad der bevidst ikke er gjort

- **Ingen IndexNow-ping.** `scripts/indexnow-payload.json` findes, men en
  IndexNow-kald er et skriv til en ekstern tjeneste, og det er forbudt i denne
  iteration. Skal ske som en del af næste planlagte pings.
- **Ingen locale-spejling af `/api/`.** Den er den næste reel opgave, se
  `IMPLEMENTATION_PLAN.md` punkt 3 under opgave 107. Siden har ingen DA/DE/FR
  udgave, så en `hreflang`-gruppe ville være tre henvisninger til 404.
- **Ingen sitemap-generator.** `sitemap.xml` er en håndført fil, og det er
  fortsat den rigtige løsning: den er læsbar, og 210 linjer er ikke det, der
  holder os tilbage. R1 gør den vokrende uden at den behøver genereres.
