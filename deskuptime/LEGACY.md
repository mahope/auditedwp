# FORÆLDET KOPI — fjernet 26. september 2026

Denne mappe lå tidligere som en **forældet kopi** af DeskUptime (51 filer,
licensklient mod den lukkede udbyder Lemon Squeezy). Kopien er **slettet**. Den
findes ikke længere i dette repo, og intet i byggingen eller publiceringen
refererer til den.

## Den rigtige app

Repoet **`mahope/deskuptime`** — https://github.com/mahope/deskuptime

Der vedligeholdes produktet, og derfra er licensen portet til Mahope-licensserveren:

```
https://mahope.tools/api/license/{activate,validate,deactivate}
```

Den publicerede produktside er `site/deskuptime/`, og den bruger allerede
Stripe-linket fra kontrakten (`deskuptime-pro`).

## Hvorfor den ikke kommer tilbage

Lemon Squeezy afviste kontoen 24. september 2026, og kontrakten siger udtrykkeligt
at den aldrig må genoplives. To kopier af samme produkts licensklient, uenige om
udbyderen, er den fælde: en bygning fra den forkerede kopi giver en **betalt vare
hvis licensaktivering kontakter en død adresse** — kunden betaler, og intet
aktiveres.

## Skal du bruge DeskUptime

Klon `mahope/deskuptime`. Kopier ikke kode herfra, og læg ikke en kopi i dette
repo igen. `tools/check_dead_providers.py` fanger det, hvis det sker: mappen
stod tidligere i `tools/dead_provider_allowlist.json` som en begrundet
undtagelse, og da slettet forsvandt linjen af sig selv. Undtagelsen er væk, så
den næste kopi giver **rødt** i stedet for at være registreret.
