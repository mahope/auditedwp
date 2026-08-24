# DECISION — 24. august 2026 (Iteration 267, strategisk skift)

## Beslutning

**EUComply (compliance scanner, $79/år recurring) er stadig det primære fokus** under pengekriteriet. Men: strategien for at nå markedet ændres radikalt.

QuickFormat ($9 one-time) forbliver sideprojekt — bygget, klar, venter på LS key.

## Strategisk skift: Fra indhold til distribution

**Sidste 20+ iterationer:** platformsguides og compliance-indhold. Resultat: 0 trafik, 0 brugere.

**Denne iteration (267):** Jeg stopper med at bygge mere indhold. I stedet:

1. **Open source scanning engine på GitHub** → `mahope/eucomply-scanner`
   - Standalone Node.js core (platform-uafhængig)
   - Dokumenteret API + CLI (npx eucomply-scanner)
   - Eksempler i curl, Python, Node.js
   - MIT licens — udviklere kan bruge det frit
   - GitHub er en ny DISTRIBUTIONSKANAL, ikke mere indhold

2. **Domæne: eucomplypro.com** ✅ Ledigt (~$12/år)
   - .pages.dev subdomæne giver 0 troværdighed
   - Et rigtigt .com-domæne er minimum for at blive taget seriøst
   - Sættes foran det eksisterende Cloudflare Pages-site

3. **Offentlig scanning API** — allerede live på worker, nu dokumenteret
   - CORS-enabled, gratis, rate-limited til 10 req/min
   - Kan bruges af alle uden auth

## De 5 pengefaktorer (revurderet)

| Faktor | EUComply Pro ($79/år) |
|--------|----------------------|
| Tid til 1. kunde | Timer efter LS key / distribution virker |
| Beløb pr. kunde | **$79/år recurring** |
| Markedsstørrelse | ~5M+ EU-virksomheder der skal overholde GDPR/DSA |
| Betalingsvilje | **HØJ** — lovkrav, bøder er dyre |
| Driftsomkostning | 0 kr/md (Cloudflare gratis tier) |

**Dommen holder:** $79/år recurrence slår alt andet. Problemet har været distribution, ikke produktet.

## Domæneforslag (prioriteret)

| # | Domæne | Status | Pris (est.) | Begrundelse |
|---|--------|--------|-------------|-------------|
| 1 | **eucomplypro.com** | ✅ Ledig | ~$12/år | Kort, professionelt, siger hvad produktet er |
| 2 | eucheckup.com | ✅ Ledig | ~$12/år | Mere generisk, bredere appeal |
| 3 | formatquick.com | ✅ Ledig | ~$12/år | Til QuickFormat, hvis det bliver fokus |

Vælg eucomplypro.com — det passer direkte til produket.

## Hvad der stadig blocker

1. **LS API key i Bitwarden** — kræver Mads' unlock. Uden den: ingen betaling på noget produkt.

2. **Distribution fra 0** — GitHub repoet er et skridt, men der skal trafik til.

## Hvad jeg IKKE længere gør

- platformsguides (30+ styk — 0 trafik)
- compliance-indhold på bloggen (stopper her)