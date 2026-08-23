# STATUS — Iteration 128 (23. august, nat)

## 1. Universitetet (punkt 1) — vurderet igen: bestået

DevNotify-kernen (`providers.rs`) er platform-uafhængig (token+provider ind,
GitHub/GitLab som adapters). Sitet er statisk HTML uden binding.
**Konklusion: intet at trække ud.** Det nye guide-indhold er ligeledes
generisk (gælder alle GitHub-brugere, ikke et CMS-nichemarked).

## 2. Nyt denne iteration — hul mellem besøgende og betaling lukket

Fund ved frisk gennemgang af købsrejsen:

- **Sitet serverede stadig v0.1.0-DMG'en**, mens appen var v0.2.0 med
  LS-licensvalidering og GitLab-support. RETTET: begge 0.2.0-builds
  (Apple Silicon + **Intel**, som FAQ'et tidligere løgnagtigt kaldte "planned")
  er nu live med SHA-256-checksummer offentliggjort på siden.
- Ny SEO-side: `/guides/github-notifications-not-showing/` — long-tail
  søgetrafik ("github notifications not showing") direkte ind til produktet.
- FAQ udvidet (GitLab-support, checksum-sikkerhed), features-grid viser nu
  GitLab, sitemap opdateret.

Alle 6 kritiske URL'er verificeret live efter deploy: HTTP 200, korrekt
indhold, DMG'er i fulde størrelser (4,47/4,60 MB).

## 3. Blokeringer (én linje hver)

1. LS API-nøgle fra Bitwarden → `ls-setup.sh` → checkout-URL → deploy → købsrejse testet.
2. Domæne getdevnotify.com venter på Registrar-token/Mads' klik.

## 4. Traction (worker-metrics, ikke egne tests)

**0** betalende · **$0** revenue · **0** rigtige tilmeldinger.

## 5. Venter på Mads

LS-nøgle (Bitwarden) → én kommandokæde sætter checkout live.
Cloudflare Registrar-adgang → domæne.

## 6. Næste iteration

1. Nøgle modtaget: `ls-setup.sh` + release-build med `LS_LICENSE_API_KEY`
   + deploy + ende-til-ende købsrejse.
2. Uden nøgle: ny guide-side (fx "github email notifications not working"
   eller "how to see github notifications on mac") + klar Product Hunt/Show HN-
   tekst der venter på Mads' ja.
