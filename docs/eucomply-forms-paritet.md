# `forms` i pluginen mod `forms` i den universelle motor

Spec skrevet **før** kodeændringen, fordi det er et betalt tjek (opgave 50).

## Problemet, målt

Opgave 49 kørte alle elleve plugin-tjek og alle ni motortjek på de samme fixtures og
fandt, at den betalte vare svarer en **mindre streng** vurdering end den gratis
scanner om den *samme* hjemmeside:

| kilde til "der er en formular" | motoren | pluginen 1.3.15 |
|---|---|---|
| `<form>` i markup'en (håndbygget formular, shortcode i widget) | læses | læses **ikke** |
| form-plugin-signatur i markup'en | læses | læses **ikke** |
| installeret form-plugin (WordPress-tilstand) | kan ikke se det | læses |

En side med en håndbygget formular og intet privatlivslink fik derfor:

- gratis: `forms` **fejler** — *"Form(s) found, no privacy-policy link"*
- Pro: `forms` **består** — *"Nothing for this check to review"*

Det er den modsatte retning af de otte fund i opgave 44 (døde tjek i den betalte
vare): her virker tjekket og er bare *mindre* end det, kunden køber.

## Beslutning

`check_forms()` læser **begge** kilder og **unionerer** dem. Der er ingen
formular, der kan slippe forbi, fordi den er håndbygget.

### Hvad tjekket regner som en formular

1. `<form …>…</form>` i forsidens markup — motorens egen regel, uændret.
2. `<form … action="https://…">` i markup'en, også uden lukket `</form>`. Det er
   en *superset* af motorens regel: en formular der poster til en ekstern
   tjeneste (Typeform, Formspree) indsamler stadig persondata. Kun den retning
   er tilladt, hvor pluginen er **strengere** end motoren.
3. En form-plugin-signatur i markup'en — motorens `FORM_PLUGIN_SIGNATURES`.
4. Et installeret form-plugin, som 1.3.15 gør.

### Hvad tjekket regner som et privatlivslink

- **Linket i markup'en** — motorens `LEGAL_PATTERNS[0]`, uændret. Det er det, der
  afgør om *den side, formularen står på*, har en notice.
- **En privatlivsside i WordPress** (`wp_page_for_privacy_policy`) — kun
  WordPress kan se den, og den er derfor *ikke* nok til at bestå det delte
  markuptjek.

### Dommen

```
har_side_formular  (1 eller 2)  → fejler, hvis markup'en ikke linker et privatlivslink
har_formular      (1..4)        → fejler, hvis hverken link eller privatlivsside findes
intet at se                       → består: "Nothing for this check to review"
ulæselig forside                  → "kunne ikke læse", aldrig et bestået
```

Hvorfor privatlivssiden ikke erstatter linket på den side, formularen står på:
det er præcis det punkt, GDPR Art. 13 og ePrivacy-reglerne går efter — notice
**ved indsamlingen**. En privatlivsside der findes i WordPress, men som ikke
linkes fra den side formularen står på, er det fund bureauet skal tage videre
til sin kunde. Etiketten siger derfor *hvor* fundet er, så det ikke kan læses
som en påstand om hele siteet.

Enhedet er bevidst **asymmetrisk**: pluginen må aldrig bestå noget, motoren
fejler, og den må gerne fejle noget motoren består, når den har en kilde til det
(WordPress-tilstand, eller en ekstern `action=` den gratis scanner ikke tæller).
Porten `tools/check_forms_parity.mjs` håndhæver begge retninger, så en for
stram læsning ikke kan passes som "porten er grøn".

## Hvad der ikke ændres

- Ingen ny hentning. `front_page()` er allerede hentet én gang pr. scanning og
  cachelagret; `check_forms()` læser det samme svar.
- Ingen ny-afhængighed, ingen SSRF-beslutning: målet er `get_home_url()`, som det
  altid har været.
- `plugins`-tjekket, `cookies`-tjekket og rapporten røres ikke.

## Måling

`tools/check_forms_parity.mjs` kører pluginens `check_forms()` gennem
`tools/plugin_probe.php` og den universelle motor gennem `runScan()` på de samme
fixtures og kræver:

1. **R1** — pluginen består aldrig, når motoren fejler på samme HTML.
2. **R2** — pluginen fejler aldrig uden en kilde: enten formularmarkup i HTML'en
   eller et installeret form-plugin. En fejl, der kun kommer af WordPress-
   tilstand, skal kunne forklares af den fixture, porten kørte.
3. **R3** — porten skal kunne fejle i begge retninger, bevist med en negativ case
   pr. retning.
4. **R4** — en mutation mod repoets **egne** fil: fjern `markup`-grenen i
   `check_forms()`, og porten skal blive rød på den rigtige fixture.

## Copy

Ingen Pro- eller prisside lovede den gamle, smallere dækning, så ingen copy
ændres. Siger en side noget om hvor mange kilder tjekket læser, rettes den.
