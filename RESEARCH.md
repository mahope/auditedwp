# RESEARCH — Produkt #2 (24. august 2026)

## Præmis

DevNotify er bygget og live. Blokeret på LS API-nøgle. Under "start noget nyt mens du venter"-reglen research'er jeg produkt #2.

## Kriterier

1. **Kortest vej til første betaling** — helst timer, max dage
2. **Indbygget betaling foretrækkes** — så jeg ikke er blokeret på LS
3. **Lav/ingen driftsomkostning**
3. **Behøver ikke være original** — beboet marked med bevist betalingsvilje er bedre

## Kandidater

### 1. Chrome-udvidelse: GitHub Notifications Companion

**Hvad:** En simpel Chrome-udvidelse der viser unread GitHub-notifikationer i browserens toolbar. Relateret til DevNotify men som selvstændigt produkt.

**Hvorfor:** Mads har Chrome Web Store udviklerkonto. Chrome Web Store har indbygget betaling (30% cut). Ingen LS nødvendig.

**Pris:** $5 one-time (gratis kerne, betalt for avancerede features som GitLab-support, dark mode, flere accounts)

**Byggetid:** 1-2 dage (simpel Chrome extension, bruger GitHub API, ligesom DevNotify)

**Marked:** Stor — alle der bruger GitHub i browseren. ~50M+ GitHub brugere, mange bruger Chrome.

**Konkurrence:** GitHub har en officiel Chrome extension (gratis). Men den er begrænset. Mange klager over manglende features.

**Blokering:** Chrome Web Store OAuth credentials ligger i Bitwarden (samme som LS). Kan ikke udgive før disse er tilgængelige.

**Dom:** ⭐⭐⭐⭐ — hurtig at bygge, indbygget betaling, men stadig Bitwarden-blokeret

### 2. CLI-værktøj: gh-notify (npm → brew)

**Hvad:** Kommandolinjeværktøj der viser GitHub-notifikationer i terminalen. `gh notify` — viser ulæste PRs, issues, mentions. Bygget på samme kerne som DevNotify.

**Hvorfor:** Lille, fokuseret, let at distribuere via npm/Homebrew. Gratis kerne, betalt pro ($9/md) med GitLab, multi-account, filtre.

**Pris:** $9/md subscription (pro) eller $29 lifetime

**Byggetid:** 2-3 dage (CLI i Node.js eller Go, API allerede kendt fra DevNotify)

**Marked:** Developer CLI-værktøjer er populære. "gh" er all allerede Googles officielle CLI. Men der findes ikke en god "gh notify" subcommand.

**Konkurrence:** `gh` CLI (GitHub officiel) har `gh api` men ingen notification CLI. gh notify findes som community scripts men ikke som poleret produkt.

**Blokering:** LS API-nøgle (samme som DevNotify). Kan ikke sælge uden betalingssystem.

**Dom:** ⭐⭐⭐⭐ — hurtig at bygge, men kræver LS

### 3. VS Code extension: GitHub Notifications Panel

**Hvad:** VS Code extension der viser GitHub-notifikationer i en panel/sidebar. Se PR-anmodninger, issues, CI-status direkte i editoren.

**Hvorfor:** VS Code marketplace har indbygget betaling (Microsoft tager cut). Stor brugerbase (~20M+ aktive VS Code-brugere).

**Pris:** $5/md eller $49 lifetime

**Byggetid:** 1-2 uger (VS Code extensions er mere komplekse end Chrome extensions)

**Marked:** Meget stort. GitHub Pull Requests extension (officiel) findes, men den er tung og fokuserer på PRs, ikke alle notifikationer.

**Konkurrence:** GitHub Pull Requests (officiel), GitLens (delvis). Ingen fokuserer på det rene notification-problem.

**Blokering:** LS API-nøgle (VS Code marketplace har ikke indbygget betaling for alle — skal bruge ekstern payment processor). Også: Mads har muligvis ikke en VS Code publisher account.

**Dom:** ⭐⭐⭐ — god idé, men langsom at bygge, og betaling kræver stadig LS

### 4. Digitalt produkt: "DevNotify Icon Pack" — developer icons

**Hvad:** Et sæt af 100+ SVG-ikoner til developer tools (Git, GitHub, Docker, VS Code, terminal, etc.). Solgt på en marketplace med indbygget betaling.

**Hvorfor:** Én gang bygget, sælger for evigt. Ingen servere, ingen drift. Kan sælges på Gumroad (droppet), Creative Market, eller LS (når nøgle kommer).

**Pris:** $12-19 one-time

**Byggetid:** 3-5 dage (design af ikoner, SVG optimering, dokumentation)

**Marked:** Stort for ikon-pakker. Developer-ikoner er mindre konkurrenceudsat end almindelige ikoner.

**Konkurrence:** Lucide, Feather, Heroicons (alle gratis). Devicons (gratis). Betalte developer icon sets findes men få.

**Blokering:** LS API-nøgle (eller marketplace-konto)

**Dom:** ⭐⭐⭐ — lav risiko, men også lav indtjening pr. produkt

### 5. API-service: Notification Bridge

**Hvad:** En simpel API der samler notifikationer fra GitHub, GitLab, Bitbucket, Gitea og sender dem til Slack, Discord, Telegram, eller webhook. B2B-service.

**Hvorfor:** Høj betalingsvilje i virksomheder. $19/md for en service der forbinder forges med chat.

**Pris:** $19/md (1 forge), $39/md (multi-forge, team)

**Byggetid:** 1-2 uger (API + webhook-håndtering, authentication, rate limiting)

**Marked:** OK — konkurrence fra Zapier/Make ($20-30/md), men de er generelle. Specialiseret service kan være billigere og bedre.

**Konkurrence:** Zapier, Make, IFTTT (alle generelle). GitHub → Slack er indbygget. GitHub → Discord er tredjepart.

**Blokering:** LS API-nøgle + server hosting. Cloudflare Workers kan håndtere dette gratis på lavt niveau.

**Dom:** ⭐⭐⭐⭐ — god B2B-mulighed, men kræver LS + tid at bygge

## Vurdering

Ingen af kandidaterne har indbygget betaling UDEN at bruge LS eller Chrome Web Store. Chrome Web Store har indbygget betaling, men credentials ligger i Bitwarden (samme blokering som LS).

**Konklusion:** Den mest produktive vej er:
1. Få LS API-nøgle → flip DevNotify checkout → $19
2. Bagefter: byg produkt #2 (Chrome extension eller CLI) med LS til betaling

Mens jeg venter: forbedr DevNotify-sitet (SEO, guides, konvertering).

## Fremtidig research (når LS-nøgle kommer)

- Hvordan sælger man en Chrome extension via LS (licensnøgle) vs. Chrome Web Store indbygget betaling
- Hvordan licenserer man et CLI-værktøj via LS API
- Hvordan sælger man et digitalt produkt (ikoner, templates) via LS