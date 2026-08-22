# STATUS

## 2026-08-23 — Iteration 19: Radaren opgraderet og kørt (HN + GitHub) — 3 live-signaler, alle døde ved første grav

### Hvad der skete
Køreplanen fra iter. 18 er udført: `POSTS/radar.py` udvidet med HN Algolia (7 dage,
shutdown-stories) og GitHub Search (repos ≥500★ arkiveret sidste 14 dage). Kørsel 01:34:
Reddit stadig 429, IndieHackers timeout — men HN+GitHub leverede 30 signaler. Tre grave-
værdige, alle døde:
1. **InstantDB** (YC S22 realtime BaaS, lukket ~20/8): RxDB og Pylon har allerede live
   "InstantDB alternative"-sider; kategorien pakket af Supabase/Convex/Zero/PocketBase.
   Swarm på <1 uge. DØD.
2. **Whoogle** (11,6k★): kategorien dræbt af Google selv (no-JS-søgning lukket) —
   enhver efterfølger arver dødsdommen. DØD.
3. **elevenlabs-mcp**: vendor tog det in-house — konsolideringstegn, ikke hul. DØD.

Latens-målingen strammes yderligere: InstantDB's konkurrencesider var live <1 uge efter
shutdown-story'en. Selv en daglig cron ville være for langsom. Radaren er nu formelt
reduceret til indholdskilde til vej 3 (essays) — ikke idé-kilde.

### Blokeret på Mads (uændret, nu afgørende)
1. JA/NEJ til kanal (X/LinkedIn) → offentliggørelse af indlæg 1-5.
2. Valg mellem de tre veje: interviews (min anbefaling — den eneste metode der kan finde
   et ubesat marked), acceptér konkurrence, eller moat-pivot.
19 iterationer, ~90 kandidater, 15 metoder. Web-research er bevist udtømmende inkl.
realtids-signaler. Uden primærdata (interviews) eller distributionskanal er der ikke
flere iterationer der kan ændre resultatet.

### Budget
0 kr brugt. Intet anmodet.

### Næste iteration
Afhænger udelukkende af Mads' svar ovenfor. Ingen produktkode. Ingen DECISION.md —
ingen kandidat består "<2 konkurrenter"-kriteriet, og jeg ville ikke sætte egne penge
i nogen af dem.

### Hvad der skete
Reddit var stadig 429-blokeret, men Hacker News Algolia-API (gratis, ingen nøgle) gav
ferske shutdown-signaler. Jeg gravede i de fire bedste:
1. **Flowise** (55k stjerner, EOL 31/8): LLMGraph m.fl. har migrations-sider rangerende
   INDEN EOL; kategorien dør strukturelt → død.
2. **Relay.app** (lukket 16/7): 6+ alternativ-guides med pristabeller live inden
   free-account-fristen 15/8 → swarment på ~3 uger.
3. **Productiv** (SMP, sunnet på 4 dages varsel, data destrueret): Torii/SpendHound/
   Zylo/CloudNuro/Tropic osv. — 9+ konkurrencesider live inden for to uger → død.
4. **TV Time** (25M+ brugere): JustWatch lancerede migrationsværktøj 6 dage FØR shutdown;
   Trakt, Hobi ("official partner"), Simkl, Zuki + — 10+ destinationer → død.

### Den hårde konklusion
Swarm-latensen er nu målt: Stocky 6 uger → Relay 3 uger → Productiv 4 dage → TV Time:
konkurrentens migrationsværktøj lanceret FØR dødsfaldet. Graveyard-signaler med kendt
brugerbase er besat før eller samtidig med shutdown'en. En fjern-observatør (mig) kan
strukturelt aldrig vinde det kapløb — også selvom lytteposten bliver daglig.

### Status på vej 3 (distribution/moat-pivot)
Radarens mekanik virker (HN-kanal løser Reddit-429; tilføjes radar.py næste gang).
Men iteration 18 beviser at radaren alene ikke kan levere en kandidat der består
"<2 konkurrenter"-kriteriet. Vej 3 kan stadig give indhold/distribution (5 essays
klare i POSTS/) — men ikke automatisk en forretningsidé.

### Blokeret på Mads (uændret)
1. JA/NEJ til kanal (X/LinkedIn-konto) → offentliggørelse af indlæg 1-5.
2. Beslutning om de tre veje: interviews / acceptér konkurrence / moat-pivot.
   Min anbefaling efter 18 iterationer: vej 1 (interviews via dit netværk) er den
   ENSTE tilbageværende metode der kan finde et ubesat marked — web-research er bevist
   udtømt (18 iterationer, ~90 kandidater, alle besat ved første grav).

### Budget
0 kr brugt. Intet anmodet.

### Næste iteration
- Tilføj HN Algolia + GitHub archived-repos til radar.py; foreslå daglig cron.
- Ellers afventer Mads' valg (ovenfor). Ingen produktkode. Ingen DECISION.md.

## 2026-08-23 — Iteration 17: Vej 3 leverancer bygget og testet.

### Leveret denne iteration
1. **De første 5 indlæg i fuld længde** (klar-til-godkendelse, engelsk, i `POSTS/`):
   - `01-eighty-five-niches.md` — hovedautopsien (85+ kandidater, mønstret, CTA)
   - `02-graveyard-gaps-worst-opportunities.md` — hvorfor graveyard-huller er de VÆRSTE
     muligheder (GummySearch/Stocky/InkFrog/Chartable/Coverfly-data)
   - `03-six-week-swarm.md` — Shopify Stocky fra annoncering til mætning på 6 uger
   - `04-regulation-is-not-a-moat.md` — scoreboard: 7 regulatoriske bølger, 7 røde have,
     med pris- og konkurrenttabel
   - `05-signal-strength-correlates.md` — signal-styrke ↔ konkurrent-tæthed, perfekt korrelation,
     konklusionen der motiverer moat-pivot'en
2. **Lyttepost-mekanik (gratis):** `POSTS/radar.py` — RSS-overvågning af r/SaaS,
   r/EntrepreneurRideAlong, IndieHackers; dedupe + output til RADAR.md med de 4 screenings-
   kriterier. Testet med rigtige kørsler (se fund nedenfor). Ingen penge, ingen konti.

### Ærlige testresultater (radar)
- Scriptet kører og skriver RADAR.md korrekt.
- Reddit rate-limitede os (HTTP 429) ved gentagne kald fra dette miljø — kun én kilde
  kom igennem pr. kørsel; IndieHackers-feed timeout. Konsekvens: radaren skal køres som
  cron med god afstand mellem kald (fx 1×/dag) eller via andet netværk/brugeragent.
  Det er en distributionsdetalje, ikke en blokerer — mekanikken er bevist.
- Nul nye shutdown-signaler i de tilgængelige feeds ved testtidspunktet (ventet).

### Blokeret på / næste skridt kræver Mads
1. **JA/NEJ til kanal:** Mads opretter X-konto (+ evt. LinkedIn), hvorefter indlæg 1-5 kan
   publiceres. Indtil da offentliggøres INGENTING (mandatets grænse).
2. **Cron:** når kanalen er godkendt, foreslår jeg daglig radar-kørsel (lokal, gratis).
3. Evt. interviews (vej 1) kan stadig sættes i gang parallelt — interviewguide klar på ønske.

### Budget
0 kr brugt. Intet anmodet. Ingen produktkode udadtil — radar.py er internt researchværktøj.

### Næste iteration (afhænger af Mads' svar)
- Hvis JA til konto: tilpas indlæg 1 til tråd-format, offentliggør, start rytmen (2/uge),
  og lad radaren levere live-autopsy #1.
- Hvis NEJ: spor 3 er dødt → tilbage står vej 1 (interviews via Mads' netværk) eller
  vej 2 (positionering af eksisterende bureau) — begge dokumenteret i RESEARCH.md.
