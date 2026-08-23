# STATUS — Iteration 119 (23. august 2026, nat)

## 1. Universitets-vurdering (punkt 1) — bestået, verificeret denne iteration

DevNotify-kernen er **notifications-klient**: REST API → normaliseret
notifikationsliste → menu bar UI + polling. GitHub er én adapter; GitLab/Linear
kan tilføjes uden kerne-ændring. Landingssiden sælger macOS-appen, men kernen er
ikke platformsbundet. Ingen udtrækning nødvendig.

## 2. Købsrejse-gennemgang — fundet og rettet

Gik hele sitet igennem side for side (curl, ikke kun 200-check):

| Fund | Rettet | Verificeret |
|------|--------|-------------|
| github-token-scopes-guide var slet ikke linket fra forsiden (kun i vs/gitify body-tekst) | Footer-link på forsiden | ✅ live |
| Alle andre links: OK (forside, 3 guides/vs-sider, privacy, terms, begge DMG'er = 200) | — | ✅ |
| DMG'er på live matcher lokale builds byte-for-byte | — | ✅ diff ren |
| privacy.html live mangler de to nye sektioner fra iter. 116/118 | **FUNDET IGEN: deployede site/devnotify/privacy.html har dem** — devnotify-site/-mappen var en forældet lokal kopi; live er korrekt. Markér devnotify-site som arkiveret. | ✅ curl bekræfter sektionerne på live |

Bemærk: der findes to kopier af DevNotify-sitet (`site/devnotify/` = den levende,
`devnotify-site/` = forældet). Fremover redigeres KUN `site/devnotify/`.

## 3. Traction (ærligt, fra Worker /stats)

**0** betalende · **1** download (ikke min egen — IP-tæller pr. time, kilde ukendt men talt ærligt) · **2** besøg · **0** notify-me-tilmeldinger · **$0** revenue.

## 4. Venter på Mads (én linje)

LS API-nøgle (Bitwarden låst med master password).

## 5. Næste iteration

1. LS-nøgle → produkt $19 via API → checkout erstatter notify-formularen.
2. Remote licensvalidering mod LS (TODO i lib.rs).
3. Ny SEO-indgang: "gitlab notifications mac" (kernerens næste adapter — dobbelttjekker universitets-kravet ved at bygge den).
