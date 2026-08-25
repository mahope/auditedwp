# BUILD — korteste vej til første betalende kunde (opdateret 24/8, it. 275)

Alle 4 produkter (EUComply Pro, DevNotify, QuickFormat, ComplianceDocs) deler én
blokering: LS API key i Bitwarden. Så snart den er der: `ls-setup-all.sh` →
CHECKOUT_URL secrets → alle købsknapper live uden ny deploy.

Korteste vej til første betaling, i rækkefølge:

1. **LS-nøglen unlockes** (Mads) → checkout live på /pro/, /devnotify/,
   /quickconvert/ + store-sider samme time.
2. **npm publish af eucomply-scanner** — pakken er færdig og CI-verificeret
   (v1.0.0, 12 kB tarball). Blokeret på npm-login (Mads: `npm adduser` eller
   granular token). **Alternativ virker NU (25/8):** `npx github:mahope/eucomply-scanner`
   er verificeret end-to-end efter TDZ-fixen (commit 2773dcf) — udviklere kan
   bruge CLI'en i dag uden registry.
3. **GitHub-repo som kanal** — repoet er nu optimeret (topics, badges,
   homepage → /scan/, CI grøn, ægte sample-output). Dernæst: README-sektion
   "Pro" med link til betalt tier, så CLI-brugere konverterer.
4. **Gratis scan → pro-konversion**: /scan/ har allerede personaliseret CTA
   baseret på brugerens egen score og fejl. Måling: worker-/stats-tæller +
   subscribe-kilder.
5. **Domænet eucomplypro.com** sættes foran, når CF token-permission er på
   plads (Mads).

Hvad der IKKE bygges mere indtil kunde #1: nye guides, nye produkter,
flere universalitets-audits.
