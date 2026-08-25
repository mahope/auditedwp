# STATUS — 25. august 2026 (aften) — Iteration 302

## Revenue & traction (ærlige tal)

- **Revenue: $0.** Rigtige tilmeldinger: 0. Rigtige monitor-registreringer: 2
  (begge demo/egne sites — ikke kunder).
- **Scans siden nulstilling 24/8: 66** (workerens offentlige `/stats`).

## Universalitets-vurdering (punkt 1) — BESTÅET (iter. 301, stadig gældende)

Scan-kernen (`shared/scan-engine.js`) er platformsuafhængig HTTP/HTML-baseret.
Indpakninger: web-scanner, CLI, Chrome-extension, WordPress-plugin (valgfri
indgang), watch-worker. Intet at trække ud.

## Iteration 302: GDPR-hul lukket i gratis-overvågningen

Monitor-flowet fra iter. 301 havde en reel compliance-fejl: ingen måde at
trække sit site ud af daglig overvågning på — et produkt der sælger compliance
skal selv overholde det (datalagring uden framelding).

**Bygget og verificeret live:**
1. `POST /unregister {url, email}` på eucomply-watch — email skal matche den
   registrerede adresse, ellers 403. Tæller dekrementeres korrekt.
2. "Stop monitoring this site"-link på /scan/ efter vellykket registrering.
   Genbruger email-feltet; hvis tomt beder brugeren om at taste den igen.

**Verificering:** deploy af worker + Pages gennemført. Endpoint testet mod
produktion: ukendt site → korrekt fejl; forkert email → 403 og sitet forbliver
registreret (kontrolleret via /status). /health viser nu alle tre endpoints.
Unsub-link bekræftet i live HTML på https://auditedwp.pages.dev/scan/.

**Kendt begrænsning:** ALERT_KEY (Resend) er endnu ikke sat som secret på
watch-workeren — score-fald-emails bliver stille skippet indtil da. Kræver en
Resend-nøgle (gratis tier) fra Mads. Noteret som blokering nedenfor.

## Blokeret på Mads (én linje)

LS API key ELLER CHECKOUT_URL ELLER 20 min manuel LS-setup → checkout live; CNAME eucomplypro.com; CWS OAuth; affiliate IDs; Resend API key til watch-alerts.
