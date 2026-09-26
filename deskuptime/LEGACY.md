# FORÆLDET — slet denne mappe

Denne mappe er en **forældet kopi** af DeskUptime. Den er ikke det produkt,
der vedligeholdes.

## Den rigtige app

Repoet **`deskuptime`**. Den har sit eget Stripeprodukt
(`deskuptime-pro`, `https://buy.stripe.com/7sY9AS9eX3Iu418fJ5bMQ01`) og sin
licensklaller mod Mahope-licensserveren:

```
https://mahope.tools/api/license/{activate,validate,deactivate}
```

## Hvorfor denne kopi er farlig

`src/license.js` og `desktop/src-tauri/src/lib.rs` i **denne** mappe kalder
stadig den lukkede udbyder:

```js
const LS_LICENSE_API = 'https://api.lemonsqueezy.com/v1/licenses/activate';
```

Lemon Squeezy afviste kontoen 24. september 2026, og kontrakten siger udtrykkeligt
at den aldrig må genoplives. Den publicerede side `site/deskuptime/` bruger
allerede Stripe, så **kun denne rodmappe** er tilbage på den lukkede udbyder.

Uden denne advarsel er fælden reel: to kopier af samme produkts licensklient,
der er uenige om udbyderen, og den i dette repo er den forkerede. En bygning
eller en ændring herfra ville give en **betalt vare, hvis licensaktivering
kontakter en død adresse** — kunden betaler, og intet aktiveres.

## Hvad der er gjort

- `site/deskuptime/` er den publicerede og korrekte kopi.
- `tools/check_dead_providers.py` holder rede på det. Kopien står i
  `tools/dead_provider_allowlist.json` med en begrundelse, så den er en
  **registreret undtagelse** og ikke en usynlig fejl. Så snart mappen er
  slettet, forsvinder linjen af sig selv.

## Anbefalet handling

Slet mappen. intet i den publiceres, og det eneste den bidrager med er en
licensklient mod en udbyder, der lukkede.
