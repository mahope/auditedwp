# STATUS — Iteration 125 (23. august, aften)

## 1. Universitetet (punkt 1) — bestått 8. gang

DevNotify-kernen er platform-agnostisk (`providers.rs`: GitHub + GitLab adapters).
Sitets indhold er statisk HTML — og nu flyttet til **roden** af domænet, så det er
helt CMS- og mappe-uafhængigt. Ingen udtrækning nødvendig.

## 2. Nyt denne iteration

- **Ny SEO-side: `/vs/octobox/`** — DevNotify vs Octobox (hostet web-inbox vs
  native menu bar app). Samme ærlige stil som Gitify-siden.
- **Site-struktur rettet:** alle interne links peger nu på roden (`/vs/gitify/`,
  `/privacy/`, `/terms/`) i stedet for `/devnotify/...` og `.html`. Den døde
  `publish/`-kopi i mappen er slettet. Sitemap opdateret.
- **Verificeret side for side:** forsiden, begge vs-sider, privacy, terms,
  sitemap og DMG-download svarer 200 med rigtigt indhold; link-crawler fandt
  0 døde links og intet fallback-indhold.

## 3. Blokeringer (én linje hver)

1. LS API-nøglen: Bitwarden har ingen tilgængelig vinduesflade og CLI er
   unauthenticated — Mads skal åbne appen og kopiere nøglen.
2. Domæne: `getdevnotify.com` er ledigt (RDAP-verificeret), men Cloudflare-
   tokenet mangler Registrar-skrivetilladelser (#domain:list) — køb kræver et
   token med Registrar-permissions eller at Mads klikker købet.

## 4. Traction (fra worker-metrics, ikke mine egne tests)

**0** betalende · **$0** revenue · **0** rigtige tilmeldinger.

## 5. Venter på Mads (én linje)

LS-nøgle fra Bitwarden → `LEMONSQUEEZY_API_KEY=xxx ./scripts/ls-setup.sh`;
evt. nyere Cloudflare-token med Registrar-adgang → jeg køber getdevnotify.com.

## 6. Næste iteration

1. Nøgle modtaget → ls-setup.sh → checkout-URL ind på alle sider → deploy →
   verificér.
2. Remote licensvalidering mod LS license API i appen (TODO i lib.rs).
3. Launch-poster (Product Hunt / Show HN / subreddit) skrevet færdige og klar
   til Mads' ja — ligger i POSTS/.
