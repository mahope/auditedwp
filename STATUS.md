# STATUS — Iteration 124 (24. august 2026)

## 1. Universitetet (punkt 1) — bestått 7. gang

DevNotify-kernen er platform-agnostisk (`providers.rs`: GitHub + GitLab adapters),
sitets indhold er CMS-uafhængigt statisk HTML. **Ingen udtrækning nødvendig.**

## 2. Beslutningen holder på pengekriteriet

DevNotify: bygget + udgivet, $19 one-time, 0 kr/md drift. Ingen anden kandidat
kan nå en betaling hurtigere end "sæt checkout-link ind".

## 3. Blokering (én linje)

LS API-nøglen: Bitwarden desktop-app kører, men har ingen tilgængelig vinduesflade
og CLI er unauthenticated — jeg kan ikke låse boksen op selv; Mads skal åbne
Bitwarden og kopiere nøglen (eller indsætte den i `scripts/ls-setup.sh`-kaldet).

## 4. Nyt denne iteration

- **`scripts/ls-setup.sh`** klar: én kommando når nøglen findes — tjekker store,
  opretter produkt "DevNotify License" $19 one-time, variant og checkout-URL,
  idempotent (springer over hvis produktet allerede findes).
- Købssektionen på forsiden gennemgået linje for linje: alt klart, ét led mangler
  (checkout-URL erstatter notify-formularen).

## 5. Traction (fra worker-metrics, ikke mine egne tests)

**0** betalende · **$0** revenue · **0** rigtige tilmeldinger.

## 6. Venter på Mads (én linje)

Lemon Squeezy API-nøgle fra Bitwarden → kør `LEMONSQUEEZY_API_KEY=xxx ./scripts/ls-setup.sh`.

## 7. Næste iteration

1. Nøgle modtaget → ls-setup.sh → checkout-URL ind i alle 5 sider → deploy →
   verificér side for side.
2. Remote licensvalidering mod LS license API i appen (TODO i lib.rs).
3. Købsrejse-gennemgang som fremmed på mobil.
