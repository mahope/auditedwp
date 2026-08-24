# STATUS — Iteration 184 (24. august)

## 1. Blokering (én linje)

LS-checkout venter på Bitwarden/LS-nøglen (bw status: unauthenticated).

## 2. Universalitetsvurdering (punkt 1) — bestått

DevNotify er ikke bundet til én platform: `providers.rs` definerer en
normaliseret `NotificationItem` + provider-abstraktion (GitHub og GitLab er
adapters), UI kalder kun `fetch_notifications(provider, token)`. App bygger til
macOS/Windows/Linux. Ingen CMS-afhængighed. Intet at trække ud.

## 3. Denne iteration: kritisk download-fejl rettet

- **Fundet:** downloadsiden linkede til `DevNotify_0.2.0_universal.dmg`, som
  aldrig var blevet bygget — Mac-købere fik 404 på hoveddownloaden.
- **Retttet:** byggede den ægte universal-dmg (lipo af arm64+x64-binaries,
  ad-hoc codesign, hdiutil UDZO). Verificeret: dmg mounter, binary er
  universal (x86_64 + arm64).
- Opdaterede SHA-256 checksummen på siden, synkede staging, deployede.
- Verificeret live: universal.dmg → 200 (8,9 MB), ny checksum i serveret HTML,
  alle undersider (/devnotify/, /download/, guide, privacy, terms) → 200.
- Metrics-worker live: 1 download · 3 visits · 0 subscribers.

## 4. Traction (ærlige tal)

**0 betalende kunder · $0 · tilmeldinger: 0 · downloads: 1 · besøg: ~2**
(kilde: devnotify-metrics worker, IP-time-dedupe; mine egne tests medregnes
ikke som subscribers).

## 5. Venter på Mads (uændret)

1. Bitwarden/LS-nøgle → checkout live samme time (`CHECKOUT-GO-LIVE.md` klar).
2. Domænekøb getdevnotify.com (forhåndsgodkendt) — sig til.
3. Valgfrit: Apple Developer ($99/år) til notarization.
4. Launch-tekster klar i `devnotify-site/LAUNCH.md` — venter på ja.

## 6. Næste iteration

Købsintent-guides fortsætter; når der kommer ægte trafik, viser
visit/download-tallene hvor faldet sker mellem besøg → download → køb.
