# Spec: scanhistorik i WordPress-pluginet (Pro)

Skrevet 2026-09-26 som grundlag for opgave 5. Status: **bygget og testet i repoet,
ikke endnu udgivet som plugin-version** — se "Udgivelse" til sidst.

## Problemet

Rapporten, der er det eneste Pro-leverance kunden kan bruge i dag, beskriver
det øjeblik den trykkes på. Den kan derfor ikke svare på det en kunde eller en
bureau-klient faktisk spørger om:

- Er vi stadig compliant, eller er noget brudt siden sidste gang?
- Hvad har I rettet, og hvornår?
- Kan I dokumentere det over for min revisor eller min forsikring?

Det er præcis de tre spørgsmål, der gør et bureau kan fakturere en
videreførelse. Uden svar på dem er rapporten en skærmdump.

## Hvorfor det er billigt

Pluginen kører **allerede** en ugentlig planlagt scan (`eucomply_weekly_scan`).
Kontinuitet kræver altså ingen ny infrastruktur, ingen ny worker, ingen ny
betalingstjeneste og ingen ekstra grænseflade mod kunden: den skal bare
skrives ned, når `run_checks()` alligevel har resultatet i hånden.

Det er hele pointen med at gøre det her og ikke i den hosted overflade: den
hostede del ligger bag spørgsmål 9 (worker-deploy), og intet i den her
spec behøver den.

## Datamodellen

Én option: `eucomply_scan_history`. Nøgle = `Y-m-d` (UTC), værdi = snapshot.

```
{
  "2026-09-26": {
    "date":   "2026-09-26",
    "total":  6,
    "passed": 4,
    "warned": 1,
    "checks": { "ssl": "pass", "cookies": "warn", "forms": "fail", ... }
  }
}
```

Valgene er ikke tilfældige:

- **Per-check tri-state, ikke kun en score.** Det er samme model som den hosted
  workers historik, så de to overflader ikke divergerer, og det er den der
  kan fortelle *hvad* der brød.
- **`warn` er sin egen tilstand.** En advarsel er et delresultat. Tælles den
  som bestået, overdriver rapporten præcis den påstand, kunden betaler for at
  få lavet. Det er samme regel som i `build_report()`s overskrift.
- **Én snapshot pr. kalenderdag.** En kunde der trykker "Scan" fem gange må
  ikke få en historik der påstår fem dages arbejde. Dagens scanning
  overskriver dagens snapshot.
- **Loft på 52 entries (~1 år).** Det er det vindue en revisor eller en
  forlængelse spørger til. Loftet håndhæves både ved skrivning *og* ved
  læsning, så en truncated, håndredigeret eller gendannet option ikke kan
  rendere en ubegrænset tabel.
- **Ingen persondata.** Ingen URL, ingen e-mail, ingen check-`detail` eller
  `fix` gemt. Kun dato og de seks tilstande. Det gør historikken til
  ikke-personoplysninger.

## Præsentation

To steder, begge i eksisterende overflader — ingen ny side, ingen ny fane:

1. **Rapporten** (`build_report`) får et afsnit "Scan history" med de seneste
   12 snapshots (optionen beholder 52) og én linje om retningen:
   forbedring, uforandret eller **regression**.
2. **Ingen historik giver intet afsnit.** Ikke "0 scans on record" — en
   rapport med en tom historik-tabel er et spørgsmål til kunden, ikke en
   leverance. Retter det kunden skal huske, står i den eksisterende
   "no scan yet"-tekst.

Retningen beregnes **fra snapshots'ene ved rendering**, aldrig fra et gemt
"improvement"-tal. Et gemt tal kan glide fra de data det påstår at beskrive;
et beregnet tal kan ikke.

## Hvad bevidst ikke er bygget

- **Ingen mail.** Opbevaring og afsendelse er to forskellige beslutninger, og
  en ugentlig mail er ikke noget, kunden har bedt om.
- **Ingen eksport.** Ingen CSV, ingen rå JSON. Bureauet kan ikke bruge en
  fil, det ikke kan læse, og hver ekstra eksport er en ekstra ting at
  vedligeholde og en ekstra ting at lække.
- **Ingen fuld historik i rapporten.** 12 uger i dokumentet, 52 i optionen.
  En rapport med 52 rækker er ikke længere en rapport.
- **Ingen hosted historik.** Den er spørgsmål 9.

## Acceptkriterier

- [x] Ét scan skriver præcis ét snapshot med per-check tri-state.
- [x] `warn` tælles hverken som bestået eller som fejltalt i den gemte tilstand.
- [x] Fem scanninger samme dag giver ét snapshot, med sidste resultat.
- [x] Loftet er 52, og det er de **ældste** der falder væk.
- [x] Loftet håndhæves også ved læsning.
- [x] En korrupt option læses som tom og renderer intet afsnit.
- [x] En fjendtlig dato eller check-nøgle kan ikke injicere markup.
- [x] Rapporten med to snapshots navngiver retningen, og en regression
      rapporteres som regression — aldrig som fremgang.
- [x] `eucomply_scan_history` slettes ved uninstall, i både site- og
      multisite-option.

## Udgivelse

Ikke udgivet i denne iteration. Næste skridt er en ren udgivelsesopgave:

1. `EUCOMPLY_VERSION` 1.3.3 → 1.3.4, `readme.txt` changelog, `uninstall.php`.
2. Ny `site/assets/eucomply-1.3.4.zip`; 1.3.3 fjernes fra deploy-træet.
3. Alle fire gamle zip-redirects i `site/_redirects` → 1.3.4.
4. `update.json` + `site/update.json` → 1.3.4, `download_url` → 1.3.4.
5. `tools/check_pro_claims.py`'s `PLUGIN_VERSION` → 1.3.4.
6. `/plugin/`-sidens downloadknap.

**Copy først efter udgivelsen.** Prissiderne siger i dag, at historik er
roadmap. Det bliver først sandt, når 1.3.4 er downloadable — og da skal det
siges eksplicit *i pluginen* (ugentlig, 52 uger, lokalt), fordi spørgsmål 1
endnu er ubesvaret: den eksisterende `eucomply-pro`-nøgle må måske kun give
plugin-dokumenterne. Se `❓ Til Mads` i `IMPLEMENTATION_PLAN.md`.
