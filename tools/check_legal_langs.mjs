/**
 * Kan de juridiske mønstre læse dansk, svensk og nederlandsk?
 *
 *   node tools/check_legal_langs.mjs
 *   node tools/check_legal_langs.mjs --selftest   (beviser at den kan fejle)
 *
 * Opgave 52 målte `LEGAL_PATTERNS` i de to universelle motorer med 22 rigtige
 * footer-links: **0 af 22** blev fundet. Følgen er ikke en manglende etiket,
 * men en score: en dansk butik med privatlivspolitik, handelsbetingelser og
 * cookiepolitik i footeren fik `legal` = **én** juridisk side og dermed
 * *advarsel* og et tabt point — mens den **samme** side på engelsk eller tysk
 * bestod med to. Efter opgave 51 var privatlivsmønsteret sprogneutralt, så
 * privatliv blev talt; vilkår og cookiepolitik gjorde det ikke, og de er netop
 * de to dokumenter `legal` kræver to af.
 *
 * Denne port måler det, i stedet for at læse kode. Den kører `legal` i begge
 * motorer (`shared/scan-engine.js` og den publicerede `eucomply-scanner/`) på
 * de samme fixtures og håndhæver fire regler:
 *
 *   R1  Dækket, ikke antaget. For hvert (mønster, sprog) i portens egen
 *       dækningstabel skal portens **egen** sprogliste se stænglen i
 *       fixturet, og begge motorer skal tælle mønsteret med sit **navn** i det
 *       `detail` en kunde læser. En tabelrække uden fixture er rød: det er
 *       forskellen på "målt" og "påstået", og den er hele denne opgave.
 *   R2  De to motorer er samme produkt. Identisk `pass`, `warn`, `label` og
 *       `detail` på hver fixture — ellers er den ene kopi ældre.
 *   R3  Ingen nye falske fund. En dansk, svensk eller nederlandsk **sætning**
 *       uden et juridisk link er ikke en juridisk side, og en side med ét
 *       juridisk link bliver ved med at være en advarsel. R1 alene kan ikke se
 *       det her: enhver bredere regex består R1 og taber point på kunden.
 *   R4  Samme dom på samme indhold, uanset sprog. Den danske, svenske og
 *       nederlandske side skal give præcis samme `legal`-dom som den engelske
 *       side med præcis samme dokumenter. Det er den asymmetri, opgaven
 *       begynder med, målt som en regel og ikke som en anecdote.
 *
 * Selftesten muterer repoets egne filer: for hvert af de ti mønstre fjernes de
 * nye sprog fra en kopi af hver motor, og porten skal blive rød på den fixture
 * der bærer sproget. Uden det er porten en påstand — samme fejlklasse som
 * opgave 45 fund 2 og opgave 50 fund 1.
 *
 * **Opgave 54** udvidte porten fra to mønstre til **ti**: de otte øvrige mønstre
 * i `LEGAL_PATTERNS` var målt i opgave 52 som *uden* nogen dansk, svensk eller
 * nederlandsk stængel, og målt gennem `legal` i begge motorer var de **0 af 24**
 * (mønster, sprog) fundet — den samme fejlklasse som opgave 52, en niveau længere
 * nede i listen. R1, R2, R3 og R4 kræver nu alle otte, og hvert mønster har sin
 * egen mutation mod hver motor.
 *
 * Hvad porten **ikke** dækker, og hvorfor: `LEGAL_PATTERNS` læses kun af de to
 * JS-motorer (målt: ingen forekomst i `plugin/eucomply.php`). Pluginens `legal`
 * er en anden mekanisme — den slår WordPress-sider op efter sti og titel, ikke
 * markup. Den har sit eget sproghul og er opgave 53.
 *
 * Ingen dependencies, intet netværk: `fetch` stubbes, målet er et IP-literal,
 * så `assertPublicTarget` ikke slår DNS op. Spec: `docs/eucomply-juridiske-sprog.md`.
 */

import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

import { runScan as runPublishedScan } from "../eucomply-scanner/engine/index.js";
import { runScan as runSharedScan } from "../shared/scan-engine.js";

const REPO = join(import.meta.dirname, "..");
const ENGINES = [
  ["motoren i repoet", join(REPO, "shared", "scan-engine.js"), runSharedScan],
  ["den publicerede motor", join(REPO, "eucomply-scanner", "engine", "index.js"), runPublishedScan],
];

/** Ét IP-literal: assertPublicTarget slår værter op i DNS, og porten skal ikke kræve netværk. */
const TARGET = "https://93.184.216.34/";

/*
 * Portens **egne** stængler, skrevet efter `docs/eucomply-juridiske-sprog.md` og
 * ikke kopieret fra nogen motor: en fejl i motorens liste må ikke gælde begge
 * veje, ellers kan R1 ikke se den. Kun de mønstre opgaven rettede står her —
 * en tabelrække uden fixture er rød, så den kan ikke vokse i det skjulte.
 */
const STEMS = {
  "Cookie policy": {
    // EN, uændret siden før opgave 52. Den er her, fordi tabellen også lover
    // engelsk dækning, og R1 genkender en tabelrække uden egen stængel.
    EN: "cookie[_-]?policy",
    DA: "cookiepolitik",
    SV: "kakpolicy",
    NL: "cookies?beleid",
  },
  "Terms & Conditions": {
    // EN var ikke et sprogproblem men et separationsproblem: motoren havde
    // `[_-]?`, som aldrig matcher et mellemrum, så "Terms of Service" og
    // "Terms & Conditions" var usynlige. Portens egen stængel har derfor
    // mellemrummet med.
    EN: "terms[ _-]?(?:of[ _-]?use|of[ _-]?services?|and[ _-]?conditions|&\s*(?:amp;)?\s*conditions|conditions)",
    DA: "handelsbetingelser|vilk[aå]?r[ _-]?(?:og[ _-]?)?(?:betingelser|for[ _-]?(?:brug|anvendelse|køb))",
    SV: "allm[aä]nna[ _-]?villkor",
    NL: "algemene[ _-]?(?:leverings)?voorwaarden",
  },

  /*
   * De otte øvrige mønstre, opgave 54. Samme to regler som ovenfor, og de er
   * begge målt, ikke antaget:
   *
   * - **Helt ord, aldrig fragment.** `returbetingelser` (DA) og `returvillkor` (SV)
   *   ligger i helt almindelig prosa om retur, så de er **ikke** stængler her;
   *   sidenavnene er *Retur- og forbrugerrettigheder* og *Retur och ångerrätt*.
   *   Der er fixtures på præcis begge fejltagelser.
   * - **Separatoren afgør, om det er en side eller en sætning.** `om[-_]?os`
   *   matcher stien `/om-os/`, men "om os" med mellemrum er dansk prosa for
   *   *about us*. Samme mønster som opgave 52s `[ _-]?` mod `[_-]?`.
   */
  "Imprint / Legal notice": {
    DA: "om[-_]os|virksomhedsoplysninger",
    SV: "om[-_]oss|bolagsuppgifter",
    NL: "colofon|bedrijfsgegevens",
  },
  "Accessibility statement": {
    DA: "tilg[æa]ngelighedserkl[æa]ring|tilg[æa]ngelighedspolitik",
    SV: "tillg[äa]nglighetsredog[öo]relse",
    NL: "toegankelijkheidsverklaring|toegankelijkheidsbeleid",
  },
  "Legal / Imprint": {
    // Dansk og svensk er **samme ord** — det er derfor de to rækker er
    // ens, og derfor er der to fixtures. Ét sprog, én regel.
    DA: "juridisk[ _-]?information",
    SV: "juridisk[ _-]?information",
    NL: "juridische[ _-]?informatie",
  },
  "Returns / Refund policy": {
    DA: "retur[ _-]?(?:og[ _-]?)?(?:forbrugerrettigheder|fortrydelsesret|politik)|fortrydelsesret",
    SV: "retur[ _-]?och[ _-]?[åa]ngerr[aä]tt",
    NL: "retourbeleid|retour[ _-]?voorwaarden|retourtermijn",
  },
  "Shipping policy": {
    DA: "fragt[ _-]?(?:og|&amp;?)?[ _-]?(?:levering|leverans|vilk[aå]r)|leveringsvilk[aå]r|forsendelsesvilk[aå]r",
    SV: "frakt[ _-]?(?:och|&amp;?)?[ _-]?leverans|leverans(?:villkor|information)",
    NL: "verzend[ _-]?(?:beleid|voorwaarden)|bezorg(?:informatie|beleid)",
  },
  "Data processing agreement": {
    DA: "databehandleraftale",
    SV: "personuppgiftsbitr[aä]desavtal|bitr[aä]desavtal[ _-]?f[öo]r[ _-]?personuppgifter",
    NL: "verwerkersovereenkomst|verwerkersav[aä]nk|verwerkersbeding",
  },
  "Acceptable use / Fair use": {
    DA: "acceptabel[ _-]?brug",
    SV: "rimlig[ _-]?anv[aä]ndning",
    NL: "redelijk[ _-]?gebruik",
  },
  "Environmental / Sustainability policy": {
    DA: "b[æa]redygtighedspolitik|milj[øo]politik",
    SV: "h[åa]llbarhetspolicy",
    NL: "duurzaamheids?(?:beleid|verklaring)",
  },

  /*
   * De syv sidste mønstre, opgave 55. Samme to regler, og de tre af dem er
   * **målt** frem for hæftet, fordi hverken en dansk, svensk eller
   * nederlandsk stængel fandtes: målingen gav **2 af 22** (mønster, sprog).
   *
   * Den tredje fejltagelse her er en, porten kun kan se ved at køre den:
   *
   * - **Et ord der også er prosa i et andet sprog.** Den tyske `garantie` er
   *   målt til at tælle dansk *garanti* — "Du får 2 års garanti på alle
   *   produkter" er prosa på enhver dansk butik. Derfor er den danske fixture
   *   med garanti en **R3**-fixture, ikke bare en stem.
   * - **Samme ord på to sprog er ærligt, ikke en fejl.** Dansk skriver
   *   *whistleblower*, fordi der ikke er et indarbejdet dansk ord, og
   *   `Legal / Imprint` har allerede DA == SV. Derfor er whistleblower-DA
   *   stænglen det engelske ord — målt, at den ser den danske fixture.
   */
  "Sub-processor list": {
    DA: "underbehandler(?:e)?[ _-]?(?:liste|list|oversigt)|liste[ _-]?over[ _-]?underbehandler",
    SV: "bitr[äa]desf[öo]rteckning|underbitr[äa]deslista",
    NL: "subverwerkers(?:lijst)?",
  },
  "Code of conduct": {
    DA: "adf[æa]rdskodeks",
    SV: "uppf[öo]randekodex",
    NL: "gedragcode",
  },
  "SLA / Warranty": {
    // EN er her, fordi opgave 55 fandt en fejl der **ikke** var et sprogproblem:
    // motorens `service[_-]?level[_-]?agreement` kan ikke matche mellemrum, så
    // en engelsk side med linkteksten "Service Level Agreement" blev kun
    // fundet når CMS'en tilfældigvis lavede stien med bindestreger. Samme
    // `[ _-]?`-fejl som opgave 52 fandt i `terms`.
    EN: "service[ _-]?level[ _-]?(?:agreement|overeenkomst)",
    DA: "serviceniveau",
    // **Ikke** `serviceniv[åa]` alene: målt giver det et falsk fund på
    // "Vi har en servicenivå på 99,9 procent", som står i svensk butiksprosa
    // om oppetid. Derfor kræver den sit eget dokumentord.
    SV: "serviceavtal|serviceniv[åa][ _-]?avtal",
    NL: "servicelevelovereenkomst",
  },
  "Complaints procedure": {
    DA: "klageprocedure|klage[ _-]?h[æa]ndtering",
    SV: "klagf[öo]rfarande",
    NL: "klachtprocedure|klachtenbeleid",
  },
  "Modern slavery statement": {
    DA: "moderne[ _-]?slaveri",
    SV: "modernt[ _-]?slaveri",
    NL: "moderne[ _-]?slavernij",
  },
  "Whistleblower / Hinweisgeber": {
    DA: "whistleblower",
    SV: "visselbl[åa]sare",
    NL: "klokkenluider",
  },
  "DPO / Data protection officer": {
    DA: "databeskyttelsesr[åa]dgiver",
    SV: "dataskyddsansvarig",
    NL: "functionaris(?:[ _-]?voor)?[ _-]?gegevensbescherming",
  },
};

/** (mønster, sprog) → fixture. R1 kræver, at hver af disse findes. */
const COVERAGE = [
  ["Cookie policy", "DA", "dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik"],
  ["Cookie policy", "SV", "svensk butiksfooter med integritetsskydd, allmänna villkor och kakpolicy"],
  ["Cookie policy", "NL", "nederlandsk butiksfooter met drie juridische links"],
  ["Terms & Conditions", "DA", "dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik"],
  ["Terms & Conditions", "SV", "svensk butiksfooter med integritetsskydd, allmänna villkor och kakpolicy"],
  ["Terms & Conditions", "NL", "nederlandsk butiksfooter met drie juridische links"],
  // Beviset på R4: samme tre dokumenter på engelsk, som altid har bestået.
  ["Cookie policy", "EN", "engelsk butiksfooter med privacy, terms og cookie policy"],
  ["Terms & Conditions", "EN", "engelsk butiksfooter med privacy, terms og cookie policy"],
  ["Terms & Conditions", "EN", "engelsk side hvor kun linkteksten siger Terms of Service"],
  ["Terms & Conditions", "DA", "dansk side med Vilkaar for brug og privatliv"],
  //
  // Opgave 54: hvert af de otte øvrige mønstre får **sin egen** fixture i
  // hvert af de tre sprog. R1 genkender en række uden fixture, så tabellen
  // ikke kan vokse i det skjulte — det er forskellen på "målt" og "påstået".
  // Fixtures genereres nedenfor af FLERE_MONSTRE, så de ikke kan glide fra
  // COVERAGE: hver række her har præcis én fixture med præcis dette navn.
  ["Imprint / Legal notice", "DA", "dansk side med Imprint / Legal notice"],
  ["Imprint / Legal notice", "SV", "svensk side med Imprint / Legal notice"],
  ["Imprint / Legal notice", "NL", "nederlandsk side med Imprint / Legal notice"],
  ["Accessibility statement", "DA", "dansk side med Accessibility statement"],
  ["Accessibility statement", "SV", "svensk side med Accessibility statement"],
  ["Accessibility statement", "NL", "nederlandsk side med Accessibility statement"],
  ["Legal / Imprint", "DA", "dansk side med Legal / Imprint"],
  ["Legal / Imprint", "SV", "svensk side med Legal / Imprint"],
  ["Legal / Imprint", "NL", "nederlandsk side med Legal / Imprint"],
  ["Returns / Refund policy", "DA", "dansk side med Returns / Refund policy"],
  ["Returns / Refund policy", "SV", "svensk side med Returns / Refund policy"],
  ["Returns / Refund policy", "NL", "nederlandsk side med Returns / Refund policy"],
  ["Shipping policy", "DA", "dansk side med Shipping policy"],
  ["Shipping policy", "SV", "svensk side med Shipping policy"],
  ["Shipping policy", "NL", "nederlandsk side med Shipping policy"],
  ["Data processing agreement", "DA", "dansk side med Data processing agreement"],
  ["Data processing agreement", "SV", "svensk side med Data processing agreement"],
  ["Data processing agreement", "NL", "nederlandsk side med Data processing agreement"],
  ["Acceptable use / Fair use", "DA", "dansk side med Acceptable use / Fair use"],
  ["Acceptable use / Fair use", "SV", "svensk side med Acceptable use / Fair use"],
  ["Acceptable use / Fair use", "NL", "nederlandsk side med Acceptable use / Fair use"],
  ["Environmental / Sustainability policy", "DA", "dansk side med Environmental / Sustainability policy"],
  ["Environmental / Sustainability policy", "SV", "svensk side med Environmental / Sustainability policy"],
  ["Environmental / Sustainability policy", "NL", "nederlandsk side med Environmental / Sustainability policy"],
  //
  // Opgave 55: de syv sidste mønstre. Samme målemetode som opgave 54 — hvert
  // mønster får sin egen fixture i hvert af de tre sprog, genereret nedenfor af
  // FLERE_MONSTRE, så en fixture og sin dækningsrække ikke kan glide fra
  // hinanden.
  ["Sub-processor list", "DA", "dansk side med Sub-processor list"],
  ["Sub-processor list", "SV", "svensk side med Sub-processor list"],
  ["Sub-processor list", "NL", "nederlandsk side med Sub-processor list"],
  ["Code of conduct", "DA", "dansk side med Code of conduct"],
  ["Code of conduct", "SV", "svensk side med Code of conduct"],
  ["Code of conduct", "NL", "nederlandsk side med Code of conduct"],
  ["SLA / Warranty", "DA", "dansk side med SLA / Warranty"],
  ["SLA / Warranty", "SV", "svensk side med SLA / Warranty"],
  ["SLA / Warranty", "NL", "nederlandsk side med SLA / Warranty"],
  // Beviset på at `sla` havde en fejl der ikke var et sprogproblem: den
  // engelske side med **mellemrum** i både sti og linktekst var usynlig før.
  ["SLA / Warranty", "EN", "engelsk side med SLA / Warranty"],
  ["Complaints procedure", "DA", "dansk side med Complaints procedure"],
  ["Complaints procedure", "SV", "svensk side med Complaints procedure"],
  ["Complaints procedure", "NL", "nederlandsk side med Complaints procedure"],
  ["Modern slavery statement", "DA", "dansk side med Modern slavery statement"],
  ["Modern slavery statement", "SV", "svensk side med Modern slavery statement"],
  ["Modern slavery statement", "NL", "nederlandsk side med Modern slavery statement"],
  ["Whistleblower / Hinweisgeber", "DA", "dansk side med Whistleblower / Hinweisgeber"],
  ["Whistleblower / Hinweisgeber", "SV", "svensk side med Whistleblower / Hinweisgeber"],
  ["Whistleblower / Hinweisgeber", "NL", "nederlandsk side med Whistleblower / Hinweisgeber"],
  ["DPO / Data protection officer", "DA", "dansk side med DPO / Data protection officer"],
  ["DPO / Data protection officer", "SV", "svensk side med DPO / Data protection officer"],
  ["DPO / Data protection officer", "NL", "nederlandsk side med DPO / Data protection officer"],
];

/** Sprog til det sprog navnet skriver. Kun til fejlbeskeder. */
const SPROG = { DA: "dansk", SV: "svensk", NL: "nederlandsk", EN: "engelsk" };
/**
 * Samme i lowercase, fordi fixture-navne skriver «dansk side med …». `EN` kom
 * først med opgave 55s engelske SLA-fixture — uden den hed den genererede
 * fixture `undefined side med SLA / Warranty`, og R1 gjorde porten rød med
 * præcis den fejl, fordi den læser fixture **navne** og ikke indeks.
 */
const SPROGNAVN = { DA: "dansk", SV: "svensk", NL: "nederlandsk", EN: "engelsk" };

const FIXTURES = [
  {
    name: "dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik",
    // Det er denne side der fik *én* juridisk side og en advarsel, før de nye
    // sprog kom til. Alle tre links er præcis sådan en dansk sko skriver dem.
    html: '<html><body><main><h1>Vores sko</h1><p>Fri fragt over 499 kr.</p></main>'
      + '<footer><a href="/privatlivspolitik/">Privatlivspolitik</a>'
      + '<a href="/handelsbetingelser/">Handelsbetingelser</a>'
      + '<a href="/cookiepolitik/">Cookiepolitik</a></footer></body></html>',
  },
  {
    name: "svensk butiksfooter med integritetsskydd, allmänna villkor och kakpolicy",
    // `Allmänna villkor` står med accent i den tekst læseren ser, fordi det er
    // sådan svenske butikker skriver det. href'en er ASCII-formen, som er den
    // de fleste CMS'er genererer.
    html: '<html><body><main><h1>Våra skor</h1><p>Fri frakt över 499 kr.</p></main>'
      + '<footer><a href="/integritetsskydd/">Integritetsskydd</a>'
      + '<a href="/allmanna-villkor">Allmänna villkor</a>'
      + '<a href="/kakpolicy">Kakpolicy</a></footer></body></html>',
  },
  {
    name: "nederlandsk butiksfooter met drie juridische links",
    // `Cookiesbeleid` med pluralsformen, som er den almindelige i Nederland.
    html: '<html><body><main><h1>Onze schoenen</h1><p>Gratis verzending boven €49.</p></main>'
      + '<footer><a href="/persoonsgegevens/">Persoonsgegevens</a>'
      + '<a href="/algemene-voorwaarden/">Algemene voorwaarden</a>'
      + '<a href="/cookiesbeleid/">Cookiesbeleid</a></footer></body></html>',
  },
  {
    name: "engelsk butiksfooter med privacy, terms og cookie policy",
    html: '<html><body><main><h1>Our shoes</h1><p>Free shipping over 49 EUR.</p></main>'
      + '<footer><a href="/privacy/">Privacy Policy</a>'
      + '<a href="/terms/">Terms of Service</a>'
      + '<a href="/cookie-policy/">Cookie Policy</a></footer></body></html>',
  },
  {
    name: "engelsk side hvor kun linkteksten siger Terms of Service",
    // Separatoren var `[_-]?`, som matcher bindestreg og understreg men aldrig
    // et mellemrum. Den fandt altså "terms-of-service" og ingen af de former en
    // side skriver. Denne fixture er den fejl, målt.
    html: '<html><body><main><h1>Support</h1><p>Vi svarer inden for 24 timer.</p></main>'
      + '<footer><a href="/legal">Terms of Service</a>'
      + '<a href="/legal/privacy">Privacy Policy</a></footer></body></html>',
  },
  {
    name: "dansk side med Vilkaar for brug og privatliv",
    html: '<html><body><main><h1>Om os</h1><p>Familiebutik siden 1998.</p></main>'
      + '<footer><a href="/privatlivspolitik/">Privatlivspolitik</a>'
      + '<a href="/vilkaar-for-brug">Vilkår for brug</a></footer></body></html>',
  },
  {
    name: "dansk side med kun ét juridisk link",
    // R3: én link er stadig én. En bredere regex må ikke gøre advarsel til
    // bestået, for det er den vej fejlen kommer tilbage ad.
    html: '<html><body><main><h1>Om os</h1><p>Vi er en dansk familiebutik siden 1998.</p></main>'
      + '<footer><a href="/privatlivspolitik/">Privatlivspolitik</a></footer></body></html>',
  },
  {
    name: "dansk sætning med leveringsbetingelser, intet juridisk link",
    // R3, dansk: `betingelser` er her en del af et helt andet ord. Havde
    // rettelsen brugt stænglen `betingelser`, ville denne side være fundet som
    // en vilkårside — og det er præcis den falske fund porten skal se.
    html: '<html><body><main><p>Priserne er ekskl. moms, og alle vores '
      + 'leveringsbetingelser gælder for levering til Danmark.</p></main></body></html>',
  },
  {
    name: "svensk sætning med köpvillkoren, intet juridisk link",
    // R3, svensk: `villkor` indgår i to helt andre ord. Havde rettelsen brugt
    // stænglen `villkor`, ville denne side være fundet.
    html: '<html><body><main><p>Köpvillkoren och returvillkoren framgår av '
      + 'orderbekräftelsen du fick per mejl.</p></main></body></html>',
  },
  {
    name: "nederlandse zin met voorwaarden, geen juridische link",
    // R3, nederlandsk: `voorwaarden` uden `algemene` er ikke sidenavnet.
    html: '<html><body><main><p>Onze voorwaarden voor de gratis proefperiode '
      + 'zijn niet bindend en kun je op elk moment opzeggen.</p></main></body></html>',
  },
  {
    name: "dansk side uden nogen juridisk side",
    html: '<html><body><main><h1>Kontakt</h1><p>Ring til os på 12 34 56 78.</p></main></body></html>',
  },
  {
    name: "dansk side med Imprint / Legal notice",
    // Ét juridisk link i dansk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri fragt over 499 kr.</p></main>'
      + '<footer><a href="/om-os/">Om os</a></footer></body></html>',
  },
  {
    name: "svensk side med Imprint / Legal notice",
    // Ét juridisk link i svensk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri frakt över 499 kr.</p></main>'
      + '<footer><a href="/om-oss/">Om oss</a></footer></body></html>',
  },
  {
    name: "nederlandsk side med Imprint / Legal notice",
    // Ét juridisk link i nederlandsk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Gratis verzending boven 49 EUR.</p></main>'
      + '<footer><a href="/colofon/">Colofon</a></footer></body></html>',
  },
  {
    name: "dansk side med Accessibility statement",
    // Ét juridisk link i dansk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri fragt over 499 kr.</p></main>'
      + '<footer><a href="/tilgaengelighedserklaering/">Tilgængelighedserklæring</a></footer></body></html>',
  },
  {
    name: "svensk side med Accessibility statement",
    // Ét juridisk link i svensk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri frakt över 499 kr.</p></main>'
      + '<footer><a href="/tillganglighetsredogorelse/">Tillgänglighetsredogörelse</a></footer></body></html>',
  },
  {
    name: "nederlandsk side med Accessibility statement",
    // Ét juridisk link i nederlandsk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Gratis verzending boven 49 EUR.</p></main>'
      + '<footer><a href="/toegankelijkheidsverklaring/">Toegankelijkheidsverklaring</a></footer></body></html>',
  },
  {
    name: "dansk side med Legal / Imprint",
    // Ét juridisk link i dansk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri fragt over 499 kr.</p></main>'
      + '<footer><a href="/juridisk-information/">Juridisk information</a></footer></body></html>',
  },
  {
    name: "svensk side med Legal / Imprint",
    // Ét juridisk link i svensk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri frakt över 499 kr.</p></main>'
      + '<footer><a href="/juridisk-information/">Juridisk information</a></footer></body></html>',
  },
  {
    name: "nederlandsk side med Legal / Imprint",
    // Ét juridisk link i nederlandsk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Gratis verzending boven 49 EUR.</p></main>'
      + '<footer><a href="/juridische-informatie/">Juridische informatie</a></footer></body></html>',
  },
  {
    name: "dansk side med Returns / Refund policy",
    // Ét juridisk link i dansk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri fragt over 499 kr.</p></main>'
      + '<footer><a href="/retur-og-forbrugerrettigheder/">Retur- og forbrugerrettigheder</a></footer></body></html>',
  },
  {
    name: "svensk side med Returns / Refund policy",
    // Ét juridisk link i svensk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri frakt över 499 kr.</p></main>'
      + '<footer><a href="/retur-och-angerratt/">Retur och ångerrätt</a></footer></body></html>',
  },
  {
    name: "nederlandsk side med Returns / Refund policy",
    // Ét juridisk link i nederlandsk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Gratis verzending boven 49 EUR.</p></main>'
      + '<footer><a href="/retourbeleid/">Retourbeleid</a></footer></body></html>',
  },
  {
    name: "dansk side med Shipping policy",
    // Ét juridisk link i dansk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri fragt over 499 kr.</p></main>'
      + '<footer><a href="/fragt-og-levering/">Fragt og levering</a></footer></body></html>',
  },
  {
    name: "svensk side med Shipping policy",
    // Ét juridisk link i svensk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri frakt över 499 kr.</p></main>'
      + '<footer><a href="/frakt-och-leverans/">Frakt och leverans</a></footer></body></html>',
  },
  {
    name: "nederlandsk side med Shipping policy",
    // Ét juridisk link i nederlandsk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Gratis verzending boven 49 EUR.</p></main>'
      + '<footer><a href="/verzendbeleid/">Verzendbeleid</a></footer></body></html>',
  },
  {
    name: "dansk side med Data processing agreement",
    // Ét juridisk link i dansk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri fragt over 499 kr.</p></main>'
      + '<footer><a href="/databehandleraftale/">Databehandleraftale</a></footer></body></html>',
  },
  {
    name: "svensk side med Data processing agreement",
    // Ét juridisk link i svensk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri frakt över 499 kr.</p></main>'
      + '<footer><a href="/personuppgiftsbitradesavtal/">Personuppgiftsbiträdesavtal</a></footer></body></html>',
  },
  {
    name: "nederlandsk side med Data processing agreement",
    // Ét juridisk link i nederlandsk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Gratis verzending boven 49 EUR.</p></main>'
      + '<footer><a href="/verwerkersovereenkomst/">Verwerkersovereenkomst</a></footer></body></html>',
  },
  {
    name: "dansk side med Acceptable use / Fair use",
    // Ét juridisk link i dansk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri fragt over 499 kr.</p></main>'
      + '<footer><a href="/acceptabel-brug/">Acceptabel brug</a></footer></body></html>',
  },
  {
    name: "svensk side med Acceptable use / Fair use",
    // Ét juridisk link i svensk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri frakt över 499 kr.</p></main>'
      + '<footer><a href="/rimlig-anvandning/">Rimlig användning</a></footer></body></html>',
  },
  {
    name: "nederlandsk side med Acceptable use / Fair use",
    // Ét juridisk link i nederlandsk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Gratis verzending boven 49 EUR.</p></main>'
      + '<footer><a href="/redelijk-gebruik/">Redelijk gebruik</a></footer></body></html>',
  },
  {
    name: "dansk side med Environmental / Sustainability policy",
    // Ét juridisk link i dansk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri fragt over 499 kr.</p></main>'
      + '<footer><a href="/baeredygtighedspolitik/">Bæredygtighedspolitik</a></footer></body></html>',
  },
  {
    name: "svensk side med Environmental / Sustainability policy",
    // Ét juridisk link i svensk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Fri frakt över 499 kr.</p></main>'
      + '<footer><a href="/hallbarhetspolicy/">Hållbarhetspolicy</a></footer></body></html>',
  },
  {
    name: "nederlandsk side med Environmental / Sustainability policy",
    // Ét juridisk link i nederlandsk, præcis som en butiksfooter skriver det: stien er
    // ASCII-formen, fordi det er den et CMS genererer, og den accentrede tekst
    // står i linkteksten, fordi det er den læseren ser.
    html: '<html><body><main><h1>Butik</h1><p>Gratis verzending boven 49 EUR.</p></main>'
      + '<footer><a href="/duurzaamheidsbeleid/">Duurzaamheidsbeleid</a></footer></body></html>',
  },
  /*
   * R3 for opgave 54. Fire prosa-sætninger, der **kunne** være fundet af en
   * bredere stængel. De er de fire fejltagelser porten skal se, målt og ikke
   * antaget:
   */
  {
    name: "dansk side med Om os som overskrift og prosa, intet juridisk link",
    // `om os` med **mellemrum** er dansk for *about us* og står i enhver
    // dansk butiksom-side. Stænglen er derfor `om[-_]?os`: bindestreg og
    // understreg, aldrig mellemrum.
    html: '<html><body><main><h1>Om os</h1><p>Læs mere om os under '
      + 'kontakt, eller ring til os på 12 34 56 78.</p></main></body></html>',
  },
  {
    name: "dansk sætning med returbetingelser og returret, intet juridisk link",
    // `returbetingelser` er helt almindelig prosa om retur. Havde stænglen være
    // `returbetingelser`, ville denne side få et juridisk link den ikke har.
    html: '<html><body><main><p>Du har 14 dages returret, og vores '
      + 'returbetingelser gælder for alle køb.</p></main></body></html>',
  },
  {
    name: "svensk sætning med returregler og returvillkoren, intet juridisk link",
    // Samme fejl i svensk: `returvillkor` ligger i *returvillkoren*, som står på
    // den svensk butiksside i opgave 52 allerede. Den nye fixture tilføjer
    // `returregler`, fordi det er den anden stængel, en bred rettelse ville tage.
    html: '<html><body><main><p>Du kan returnera inom 14 dagar enligt våra '
      + 'returregler; returvillkoren framgår av orderbekräftelsen.</p></main></body></html>',
  },
  {
    name: "nederlandse zin met verzendkosten, geen juridische link",
    // `verzendkosten` står i hver Nederlandsk butiksseite. `verzendbeleid` må
    // derfor kræve sit eget suffiks, ikke bare `verzend`.
    html: '<html><body><main><p>Verzendkosten worden berekend bij '
      + 'afrekenen, en levering duurt twee werkdagen.</p></main></body></html>',
  },
  /*
   * R3 for opgave 55. To prosa-sætninger, der **blev** fundet af en stængel,
   * målt i denne iteration og ikke antaget:
   */
  {
    name: "dansk sætning med garanti på produkter, intet juridisk link",
    // Den tyske `garantie` matcher dansk *garanti*, som står i hver dansk
    // butiksprosa om varer. Uden denne fixture fik den betalte rapport et
    // **falsk** juridisk link på en side uden et.
    html: '<html><body><main><p>Du får 2 års garanti på alle produkter, og '
      + 'garantien dækker reparation af fabrikationsfejl.</p></main></body></html>',
  },
  {
    name: "svensk sætning med servicenivå i prosa, intet juridisk link",
    // `servicenivå` alene er oppetid i svensk butiksprosa, ikke et dokument.
    // Derfor kræver den svenske stængel sit eget dokumentord.
    html: '<html><body><main><p>Vi har en servicenivå på 99,9 procent, och '
      + 'servicenivån mäts varje timme.</p></main></body></html>',
  },
];

/*
 * Fixtures for de otte øvrige mønstre, opgave 54. De **genereres** af den ene
 * tabel, så en fixture og dens dækningsrække ikke kan glide fra hinanden: de
 * deler navnet, og R1 genkender en række uden fixture.
 */
const FLERE_MONSTRE = [  ["Imprint / Legal notice", "DA", "/om-os/", "Om os", "Fri fragt over 499 kr."],  ["Imprint / Legal notice", "SV", "/om-oss/", "Om oss", "Fri frakt över 499 kr."],  ["Imprint / Legal notice", "NL", "/colofon/", "Colofon", "Gratis verzending boven 49 EUR."],  ["Accessibility statement", "DA", "/tilgaengelighedserklaering/", "Tilgængelighedserklæring", "Fri fragt over 499 kr."],  ["Accessibility statement", "SV", "/tillganglighetsredogorelse/", "Tillgänglighetsredogörelse", "Fri frakt över 499 kr."],  ["Accessibility statement", "NL", "/toegankelijkheidsverklaring/", "Toegankelijkheidsverklaring", "Gratis verzending boven 49 EUR."],  ["Legal / Imprint", "DA", "/juridisk-information/", "Juridisk information", "Fri fragt over 499 kr."],  ["Legal / Imprint", "SV", "/juridisk-information/", "Juridisk information", "Fri frakt över 499 kr."],  ["Legal / Imprint", "NL", "/juridische-informatie/", "Juridische informatie", "Gratis verzending boven 49 EUR."],  ["Returns / Refund policy", "DA", "/retur-og-forbrugerrettigheder/", "Retur- og forbrugerrettigheder", "Fri fragt over 499 kr."],  ["Returns / Refund policy", "SV", "/retur-och-angerratt/", "Retur och ångerrätt", "Fri frakt över 499 kr."],  ["Returns / Refund policy", "NL", "/retourbeleid/", "Retourbeleid", "Gratis verzending boven 49 EUR."],  ["Shipping policy", "DA", "/fragt-og-levering/", "Fragt og levering", "Fri fragt over 499 kr."],  ["Shipping policy", "SV", "/frakt-och-leverans/", "Frakt och leverans", "Fri frakt över 499 kr."],  ["Shipping policy", "NL", "/verzendbeleid/", "Verzendbeleid", "Gratis verzending boven 49 EUR."],  ["Data processing agreement", "DA", "/databehandleraftale/", "Databehandleraftale", "Fri fragt over 499 kr."],  ["Data processing agreement", "SV", "/personuppgiftsbitradesavtal/", "Personuppgiftsbiträdesavtal", "Fri frakt över 499 kr."],  ["Data processing agreement", "NL", "/verwerkersovereenkomst/", "Verwerkersovereenkomst", "Gratis verzending boven 49 EUR."],  ["Acceptable use / Fair use", "DA", "/acceptabel-brug/", "Acceptabel brug", "Fri fragt over 499 kr."],  ["Acceptable use / Fair use", "SV", "/rimlig-anvandning/", "Rimlig användning", "Fri frakt över 499 kr."],  ["Acceptable use / Fair use", "NL", "/redelijk-gebruik/", "Redelijk gebruik", "Gratis verzending boven 49 EUR."],  ["Environmental / Sustainability policy", "DA", "/baeredygtighedspolitik/", "Bæredygtighedspolitik", "Fri fragt over 499 kr."],  ["Environmental / Sustainability policy", "SV", "/hallbarhetspolicy/", "Hållbarhetspolicy", "Fri frakt över 499 kr."],  ["Environmental / Sustainability policy", "NL", "/duurzaamheidsbeleid/", "Duurzaamheidsbeleid", "Gratis verzending boven 49 EUR."],  ["Sub-processor list", "DA", "/underbehandlerliste/", "Underbehandlerliste", "Fri fragt over 499 kr."],  ["Sub-processor list", "SV", "/bitradesforteckning/", "Biträdesförteckning", "Fri frakt över 499 kr."],  ["Sub-processor list", "NL", "/subverwerkers/", "Subverwerkers", "Gratis verzending boven 49 EUR."],  ["Code of conduct", "DA", "/adfaerdskodeks/", "Adfærdskodeks", "Fri fragt over 499 kr."],  ["Code of conduct", "SV", "/uppforandekodex/", "Uppförandekodex", "Fri frakt över 499 kr."],  ["Code of conduct", "NL", "/gedragcode/", "Gedragcode", "Gratis verzending boven 49 EUR."],  ["SLA / Warranty", "DA", "/serviceniveau/", "Serviceniveau", "Fri fragt over 499 kr."],  ["SLA / Warranty", "SV", "/serviceavtal/", "Serviceavtal", "Fri frakt över 499 kr."],  ["SLA / Warranty", "NL", "/servicelevelovereenkomst/", "Servicelevelovereenkomst", "Gratis verzending boven 49 EUR."],  ["SLA / Warranty", "EN", "/service level agreement/", "Service Level Agreement", "Free shipping over 49 EUR."],  ["Complaints procedure", "DA", "/klageprocedure/", "Klageprocedure", "Fri fragt over 499 kr."],  ["Complaints procedure", "SV", "/klagforfarande/", "Klagförfarande", "Fri frakt över 499 kr."],  ["Complaints procedure", "NL", "/klachtprocedure/", "Klachtprocedure", "Gratis verzending boven 49 EUR."],  ["Modern slavery statement", "DA", "/moderne-slaveri/", "Moderne slaveri", "Fri fragt over 499 kr."],  ["Modern slavery statement", "SV", "/modernt-slaveri/", "Modernt slaveri", "Fri frakt över 499 kr."],  ["Modern slavery statement", "NL", "/moderne-slavernij/", "Moderne slavernij", "Gratis verzending boven 49 EUR."],  ["Whistleblower / Hinweisgeber", "DA", "/whistleblower/", "Whistleblower", "Fri fragt over 499 kr."],  ["Whistleblower / Hinweisgeber", "SV", "/visselblasare/", "Visselblåsare", "Fri frakt över 499 kr."],  ["Whistleblower / Hinweisgeber", "NL", "/klokkenluider/", "Klokkenluider", "Gratis verzending boven 49 EUR."],  ["DPO / Data protection officer", "DA", "/databeskyttelsesradgiver/", "Databeskyttelsesrådgiver", "Fri fragt over 499 kr."],  ["DPO / Data protection officer", "SV", "/dataskyddsansvarig/", "Dataskyddsansvarig", "Fri frakt över 499 kr."],  ["DPO / Data protection officer", "NL", "/functionaris-voor-gegevensbescherming/", "Functionaris voor gegevensbescherming", "Gratis verzending boven 49 EUR."],];

for (const [pat, lang, href, tekst, fyld] of FLERE_MONSTRE) {
  FIXTURES.push({
    name: `${SPROGNAVN[lang]} side med ${pat}`,
    html: '<html><body><main><h1>Butik</h1><p>' + fyld + '</p></main>'
      + `<footer><a href="${href}">${tekst}</a></footer></body></html>`,
  });
}

/**
 * Hvilke mønstre en motor fandt. Læst ud af `detail` — den tekst kunden ser i
 * rapporten — fordi `LEGAL_PATTERNS` ikke er eksporteret, og fordi det er den
 * tekst, porten skal måle: et mønster der findes i koden, men ikke i
 * rapporten, er ikke fundet for kunden.
 */
function foundNames(verdict) {
  const m = /Found on page: (.+?)\.$/.exec(verdict.detail || "");
  if (!m) return [];
  return m[1].split(", ").map((s) => s.trim());
}

/** Kør én motor mod én fixture. */
async function engineVerdict(runScan, fixture) {
  const saved = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(fixture.html || "", {
      status: 200,
      headers: { "Content-Type": "text/html", ...(fixture.headers || {}) },
    });
  try {
    const scan = await runScan(TARGET);
    assert.ok(scan.checks.legal, "motoren kender ikke tjekket legal");
    return scan.checks.legal;
  } finally {
    globalThis.fetch = saved;
  }
}

/** Hent en fixture ved navn. Navne, ikke indeks — så en ny fixture i midten ikke flytter dem. */
function fx(name) {
  const found = FIXTURES.find((f) => f.name === name);
  assert.ok(found, `porten har ingen fixture ved navn «${name}»`);
  return found;
}

/** Sprog, hvis portens egen liste ser stænglen i fixturet. */
function portSees(pat, lang, fixture) {
  const stem = STEMS[pat] && STEMS[pat][lang];
  if (!stem) return false;
  return new RegExp(stem, "i").test(fixture.html || "");
}

/*
 * De fire regler, som *kun* betinger. Porten og selftesten kalder de samme
 * funktioner, så en negativ case ikke kan blive grøn ved at forvente noget andet
 * end det porten kræver — den fejl fandt opgave 42, 45 og 50.
 */

/** R1: dækket, ikke antaget — hvert (mønster, sprog) skal findes i begge motorer. */
function contractR1(verdicts, fixture) {
  for (const [pat, lang, fixtureName] of COVERAGE) {
    if (fixtureName !== fixture.name) continue;
    assert.ok(
      portSees(pat, lang, fixture),
      `portens egen liste kan ikke se ${SPROG[lang] || lang}-formen af «${pat}» i «${fixture.name}»`
    );
    for (const [hvem, v] of verdicts) {
      assert.ok(
        foundNames(v).includes(pat),
        `${hvem} finder ikke «${pat}» på en ${SPROG[lang] || lang} side ` +
          `(rapporten siger: "${v.detail}")`
      );
    }
  }
}

/** R2: de to motorer er samme produkt og skal svare identisk. */
function contractR2(verdicts) {
  // `verdicts` er [hvem, dom]-par, så dommen er indeks 1. Destrukturerer man
  // kun det ydre par, sammenligner man `undefined` med `undefined` — og regelen
  // er grøn for enhver afvigelse. Det gjorde den i første udformning, og
  // selftesten fandt det.
  const [, a] = verdicts[0];
  const [, b] = verdicts[1];
  assert.equal(
    Boolean(b.pass),
    Boolean(a.pass),
    `de to motorer er uenige om dommen: «${a.label}» mod «${b.label}»`
  );
  assert.equal(b.detail, a.detail, `samme dom, to forskellige rapporter: «${a.detail}» mod «${b.detail}»`);
}

/** R3: en sætning er ikke en juridisk side, og ét link er stadig ét link. */
function contractR3(verdicts, fixture) {
  const forventetLinks = fixture.name === "dansk side med kun ét juridisk link" ? 1 : 0;
  for (const [hvem, v] of verdicts) {
    if (forventetLinks === 0) {
      assert.equal(
        Boolean(v.pass),
        false,
        `${hvem} består (${v.label}) på «${fixture.name}» — der er intet juridisk link på siden`
      );
      assert.equal(
        foundNames(v).length,
        0,
        `${hvem} tæller ${foundNames(v).join(", ")} på «${fixture.name}» — en sætning er ikke en juridisk side`
      );
    } else {
      assert.equal(
        Boolean(v.warn),
        true,
        `${hvem} svarer ${v.label} på en side med ét juridisk link — advarslen forsvandt`
      );
      assert.equal(
        Boolean(v.pass),
        false,
        `${hvem} består (${v.label}) på en side med kun ét juridisk link`
      );
    }
  }
}

/**
 * R1s anden halvdel: en dækningstabelrække uden egen stængel eller uden egen
 * fixture er rød. Det er forskellen på "målt" og "påstået", og det er hele denne
 * opgave. Porten **og** selftesten kalder den her, så en negativ case ikke kan
 * blive grøn ved at forvente noget andet end det porten kræver — den fejl fandt
 * opgave 42, 45 og 50.
 */
function contractCoverage(table, stems, fixtures) {
  for (const [pat, lang, fixtureName] of table) {
    const langs = stems[pat] || {};
    assert.ok(
      Object.prototype.hasOwnProperty.call(langs, lang),
      `dækningstabellen lover «${pat}» på ${SPROG[lang] || lang}, men porten har ingen stængel til den`
    );
    assert.ok(
      fixtures.some((f) => f.name === fixtureName),
      `dækningstabellen lover «${pat}» på ${SPROG[lang] || lang}, men der er ingen fixture ved navn «${fixtureName}» — ` +
        `et mønster uden fixture er påstået, ikke målt`
    );
  }
}

/** R4: samme dokumenter, samme dom — uanset hvilket sprog siden står på. */
function contractR4(verdicts) {
  const dansk = verdicts["dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik"];
  const svensk = verdicts["svensk butiksfooter med integritetsskydd, allmänna villkor och kakpolicy"];
  const nederlandsk = verdicts["nederlandsk butiksfooter met drie juridische links"];
  const engelsk = verdicts["engelsk butiksfooter med privacy, terms og cookie policy"];
  for (const [sprog, v] of Object.entries({ dansk, svensk, nederlandsk })) {
    assert.equal(
      Boolean(v.pass),
      Boolean(engelsk.pass),
      `en ${sprog} butik med de samme tre juridiske dokumenter får «${v.label}», ` +
        `mens den engelske får «${engelsk.label}» — scoren afhænger af sprog`
    );
  }
}

let passed = 0;
const failures = [];
async function test(name, fn) {
  try {
    await fn();
    passed++;
  } catch (e) {
    failures.push(`${name}: ${e && e.message}`);
  }
}

const verdicts = new Map();
for (const fixture of FIXTURES) {
  const per = [];
  for (const [hvem, , runScan] of ENGINES) per.push([hvem, await engineVerdict(runScan, fixture)]);
  verdicts.set(fixture.name, per);
}

for (const fixture of FIXTURES) {
  const vs = verdicts.get(fixture.name);
  await test(`R1 dækket, ikke antaget: ${fixture.name}`, () => contractR1(vs, fixture));
  await test(`R2 de to motorer er ens: ${fixture.name}`, () => contractR2(vs));
  if (
    fixture.name === "dansk side med kun ét juridisk link" ||
    !foundNames(vs[0][1]).length
  ) {
    await test(`R3 ingen falske fund: ${fixture.name}`, () => contractR3(vs, fixture));
  }
}

await test("R1: hver (mønster, sprog) i tabellen har en stængel og en fixture", () => {
  contractCoverage(COVERAGE, STEMS, FIXTURES);
});

await test("R4: samme tre juridiske dokumenter giver samme dom på fire sprog", () => {
  contractR4(Object.fromEntries(verdicts));
});

if (process.argv.includes("--selftest")) {
  const caught = [];
  /** Forventer at kontrakten bliver rød på dette input, og tæller det. */
  const expectRed = (name, contract, ...args) => {
    try {
      contract(...args);
      failures.push(`selftest: ${name} gav en grøn port — den kan ikke se den fejl`);
    } catch {
      caught.push(name);
    }
  };

  // 1. R1: motoren finder ikke den danske cookiepolitik.
  expectRed("R1 (motor finder ikke)", contractR1, [
    ["motoren i repoet", { pass: true, label: "3 legal pages linked", detail: "Found on page: Privacy / GDPR, Terms & Conditions." }],
  ], fx("dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik"));

  // 2. R1: portens egen liste kan ikke se stænglen, selv om motoren kan. Det er
  //    den retning, der gør tabellen ubrugelig frem for at motoren er rød.
  expectRed("R1 (portens egen liste)", contractR1, [
    ["motoren i repoet", { pass: true, label: "3 legal pages linked", detail: "Found on page: Privacy / GDPR, Cookie policy, Terms & Conditions." }],
  ], { name: "dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik", html: "<p>ingen juridisk side</p>" });

  // 3. R2: de to motorer svarer forskelligt.
  expectRed("R2", contractR2, [
    ["motoren i repoet", { pass: true, label: "3 legal pages linked", detail: "Found on page: a, b, c." }],
    ["den publicerede motor", { pass: false, label: "1 legal page linked", detail: "Found on page: a." }],
  ]);

  // 4. R3: en sætning blev talt som en juridisk side.
  expectRed("R3 (falsk fund)", contractR3, [
    ["motoren i repoet", { pass: true, warn: false, label: "2 legal pages linked", detail: "Found on page: Terms & Conditions, Cookie policy." }],
  ], fx("svensk sætning med köpvillkoren, intet juridisk link"));

  // 5. R3: ét link blev bestået.
  expectRed("R3 (ét link bestået)", contractR3, [
    ["motoren i repoet", { pass: true, warn: false, label: "1 legal page linked", detail: "Found on page: Privacy / GDPR." }],
  ], fx("dansk side med kun ét juridisk link"));

  // 6. R4: den danske side advarser, den engelske består.
  expectRed("R4", contractR4, {
    "dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik": { pass: false, label: "1 legal page linked" },
    "svensk butiksfooter med integritetsskydd, allmänna villkor och kakpolicy": { pass: true, label: "3 legal pages linked" },
    "nederlandsk butiksfooter met drie juridische links": { pass: true, label: "3 legal pages linked" },
    "engelsk butiksfooter med privacy, terms og cookie policy": { pass: true, label: "3 legal pages linked" },
  });

  /*
   * Mutationer mod repoets egne filer. For hvert mønster fjernes de nye sprog fra
   * en kopi af hver motor, og porten skal blive rød på den fixture der bærer
   * sproget. Skrevet mod den lange linje, så de fejler med "fandt ikke den linje
   * den erstatter" den dag et nyt sprog kommer til, i stedet for at lade porten
   * stå grøn på en mutation den ikke længere rammer.
   */
  const MUTATIONS = [
    {
      name: "cookie: de nye sprog forsvinder",
      before: "cookie[_-]?preferences|cookiepolitik|cookies?beleid|kakpolicy",
      after: "cookie[_-]?preferences",
      fixture: "dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik",
      pattern: "Cookie policy",
    },
    {
      name: "terms: de nye sprog forsvinder",
      before: "terms[ _-]?(?:of[ _-]?use|of[ _-]?services?|and[ _-]?conditions|&\\s*(?:amp;)?\\s*conditions|conditions)|handelsbetingelser|vilk[aå]?r[ _-]?(?:og[ _-]?)?(?:betingelser|for[ _-]?(?:brug|anvendelse|køb))|allm[aä]nna[ _-]?villkor|anv[äa]ndningsvillkor|algemene[ _-]?(?:leverings)?voorwaarden",
      after: "terms[ _-]?(?:of[ _-]?use|of[ _-]?services?|and[ _-]?conditions|&\\s*(?:amp;)?\\s*conditions|conditions)",
      fixture: "svensk butiksfooter med integritetsskydd, allmänna villkor och kakpolicy",
      pattern: "Terms & Conditions",
    },
    {
      name: "imprint: de nye sprog forsvinder",
      before: "|om[-_]?os|virksomhedsoplysninger|om[-_]?oss|bolagsuppgifter|colofon|bedrijfsgegevens|kvk[ _-]?nummer",
      after: "",
      fixture: "dansk side med Imprint / Legal notice",
      pattern: "Imprint / Legal notice",
    },    {
      name: "accessibility: de nye sprog forsvinder",
      before: "|tilg[æa]ngelighedserkl[æa]ring|tilg[æa]ngelighedspolitik|tillg[äa]nglighetsredog[öo]relse|toegankelijkheidsverklaring|toegankelijkheidsbeleid",
      after: "",
      fixture: "nederlandsk side med Accessibility statement",
      pattern: "Accessibility statement",
    },    {
      name: "legal info: de nye sprog forsvinder",
      before: "|juridisk[ _-]?information|juridische[ _-]?informatie",
      after: "",
      fixture: "svensk side med Legal / Imprint",
      pattern: "Legal / Imprint",
    },    {
      name: "returns: de nye sprog forsvinder",
      before: "|retur[ _-]?(?:og[ _-]?)?(?:forbrugerrettigheder|fortrydelsesret|politik)|fortrydelsesret|retur[ _-]?och[ _-]?[åa]ngerr[aä]tt|retourbeleid|retour[ _-]?voorwaarden|retourtermijn",
      after: "",
      fixture: "dansk side med Returns / Refund policy",
      pattern: "Returns / Refund policy",
    },    {
      name: "shipping: de nye sprog forsvinder",
      before: "|fragt[ _-]?(?:og|&amp;?)?[ _-]?(?:levering|leverans|vilk[aå]r)|leveringsvilk[aå]r|forsendelsesvilk[aå]r|frakt[ _-]?(?:och|&amp;?)?[ _-]?leverans|leverans(?:villkor|information)|verzend[ _-]?(?:beleid|voorwaarden)|bezorg(?:informatie|beleid)",
      after: "",
      fixture: "nederlandsk side med Shipping policy",
      pattern: "Shipping policy",
    },    {
      name: "dpa: de nye sprog forsvinder",
      before: "|databehandleraftale|personuppgiftsbitr[aä]desavtal|bitr[aä]desavtal[ _-]?f[öo]r[ _-]?personuppgifter|verwerkersovereenkomst|verwerkersav[aä]nk|verwerkersbeding",
      after: "",
      fixture: "svensk side med Data processing agreement",
      pattern: "Data processing agreement",
    },    {
      name: "acceptable use: de nye sprog forsvinder",
      before: "|acceptabel[ _-]?brug|rimlig[ _-]?anv[aä]ndning|redelijk[ _-]?gebruik",
      after: "",
      fixture: "svensk side med Acceptable use / Fair use",
      pattern: "Acceptable use / Fair use",
    },    {
      name: "environmental: de nye sprog forsvinder",
      before: "|b[æa]redygtighedspolitik|milj[øo]politik|h[åa]llbarhetspolicy|duurzaamheids?(?:beleid|verklaring)",
      after: "",
      fixture: "dansk side med Environmental / Sustainability policy",
      pattern: "Environmental / Sustainability policy",
    },
    {
      name: "subprocessor: de nye sprog forsvinder",
      before: "|underbehandler(?:e)?[ _-]?(?:liste|list|oversigt)|liste[ _-]?over[ _-]?underbehandler|bitr[äa]desf[öo]rteckning|underbitr[äa]deslista|subverwerkers(?:lijst)?",
      after: "",
      fixture: "svensk side med Sub-processor list",
      pattern: "Sub-processor list",
    },
    {
      name: "code of conduct: de nye sprog forsvinder",
      before: "|adf[æa]rdskodeks|uppf[öo]randekodex|gedragcode",
      after: "",
      fixture: "nederlandsk side med Code of conduct",
      pattern: "Code of conduct",
    },
    {
      name: "sla: de nye sprog forsvinder",
      before: "|serviceniveau|serviceavtal|serviceniv[åa][ _-]?avtal",
      after: "",
      fixture: "dansk side med SLA / Warranty",
      pattern: "SLA / Warranty",
    },
    {
      name: "sla: mellemrum forsvinder i den engelske stængel",
      before: "service[ _-]?level[ _-]?(?:agreement|overeenkomst)",
      after: "service[_-]?level[_-]?agreement",
      fixture: "engelsk side med SLA / Warranty",
      pattern: "SLA / Warranty",
    },
    {
      name: "complaints: de nye sprog forsvinder",
      before: "|klageprocedure|klage[ _-]?h[æa]ndtering|klagf[öo]rfarande|klachtprocedure|klachtenbeleid|klachtenafhandeling",
      after: "",
      fixture: "svensk side med Complaints procedure",
      pattern: "Complaints procedure",
    },
    {
      name: "modern slavery: de nye sprog forsvinder",
      before: "|moderne[ _-]?slaveri|modernt[ _-]?slaveri|moderne[ _-]?slavernij",
      after: "",
      fixture: "nederlandsk side med Modern slavery statement",
      pattern: "Modern slavery statement",
    },
    {
      name: "whistleblower: de nye sprog forsvinder",
      before: "|visselbl[åa]sare|klokkenluider(?:sregeling)?",
      after: "",
      fixture: "svensk side med Whistleblower / Hinweisgeber",
      pattern: "Whistleblower / Hinweisgeber",
    },
    {
      name: "dpo: de nye sprog forsvinder",
      before: "|databeskyttelsesr[åa]dgiver|dataskyddsansvarig|functionaris(?:[ _-]?voor)?[ _-]?gegevensbescherming",
      after: "",
      fixture: "nederlandsk side med DPO / Data protection officer",
      pattern: "DPO / Data protection officer",
    },
  ];

  for (const m of MUTATIONS) {
    for (const [hvem, file, ] of ENGINES) {
      const source = readFileSync(file, "utf8");
      if (!source.includes(m.before)) {
        failures.push(
          `selftest: mutationen «${m.name}» i ${hvem} fandt ikke den linje den erstatter — ` +
            `porten kan ikke længere bevise at den ser den fejl`
        );
        continue;
      }
      const dir = mkdtempSync(join(tmpdir(), "eucomply-legal-mutant-"));
      const mutant = join(dir, file.endsWith("index.js") ? "index.js" : "scan-engine.js");
      writeFileSync(mutant, source.replace(m.before, m.after));
      const mutated = await engineVerdict((await import(pathToFileURL(mutant).href)).runScan, fx(m.fixture));
      try {
        assert.ok(
          foundNames(mutated).includes(m.pattern),
          `mutationen «${m.name}» i ${hvem} fandt stadig «${m.pattern}» (${mutated.detail})`
        );
        failures.push(
          `selftest: mutationen «${m.name}» i ${hvem} gav stadig «${m.pattern}» — ` +
            `porten kan ikke se den fejl den blev skrevet til at se`
        );
      } catch {
        caught.push(`${m.name} (${hvem})`);
      }
      // Og den mutation skal gøre R1 rød, ikke blot ved at miste et navn.
      const anden = [hvem, mutated];
      const [første] = ENGINES;
      const par = verdicts.get(m.fixture).map(([h, v]) => (h === første[0] ? anden : [h, v]));
      expectRed(`${m.name} (${hvem}) i R1`, contractR1, par, fx(m.fixture));
    }
  }

  // 6b. Opgave 54: de fire prosa-fejltagelser. Samme regel som 4 og 5, men på de
  //     fixtures der bærer de nye stængler — ellers ville R3 kun være prøvet
  //     mod de to mønstre fra opgave 52.
  expectRed("R3 (dansk «om os» i prosa)", contractR3, [
    ["motoren i repoet", { pass: true, warn: false, label: "1 legal page linked", detail: "Found on page: Imprint / Legal notice." }],
  ], fx("dansk side med Om os som overskrift og prosa, intet juridisk link"));
  expectRed("R3 (dansk returbetingelser)", contractR3, [
    ["motoren i repoet", { pass: true, warn: false, label: "1 legal page linked", detail: "Found on page: Returns / Refund policy." }],
  ], fx("dansk sætning med returbetingelser og returret, intet juridisk link"));
  expectRed("R3 (svensk returregler)", contractR3, [
    ["motoren i repoet", { pass: true, warn: false, label: "1 legal page linked", detail: "Found on page: Returns / Refund policy." }],
  ], fx("svensk sætning med returregler og returvillkoren, intet juridisk link"));
  expectRed("R3 (nederlandsk verzendkosten)", contractR3, [
    ["motoren i repoet", { pass: true, warn: false, label: "1 legal page linked", detail: "Found on page: Shipping policy." }],
  ], fx("nederlandse zin met verzendkosten, geen juridische link"));
  // 6c. Opgave 55: de to prosa-fejltagelser porten skal se, målt i denne
  //     iteration. Uden dem ville en bredere `garantie` igen give den betalte
  //     rapport et falsk juridisk link på dansk prosa.
  expectRed("R3 (dansk garanti i prosa)", contractR3, [
    ["motoren i repoet", { pass: true, warn: false, label: "1 legal page linked", detail: "Found on page: SLA / Warranty." }],
  ], fx("dansk sætning med garanti på produkter, intet juridisk link"));
  expectRed("R3 (svensk servicenivå i prosa)", contractR3, [
    ["motoren i repoet", { pass: true, warn: false, label: "1 legal page linked", detail: "Found on page: SLA / Warranty." }],
  ], fx("svensk sætning med servicenivå i prosa, intet juridisk link"));

  // 7. En (mønster, sprog)-række i tabellen uden fixture er rød. Den kalder
  //    portens egen kontrakt med den fixture fjernet, så den ikke kan være grøn
  //    ved at kræve noget andet end det porten kræver.
  const mistet = FIXTURES.filter((f) => f.name !== COVERAGE[0][2]);
  expectRed("R1 (tabellen kræver en fixture)", contractCoverage, COVERAGE, STEMS, mistet);

  // 8. Samme regel for en stængel, portens egen liste ikke har. Den peger på et
  //    mønster, opgave 55 **ikke** rettede — `General contact address` er
  //    email-adresser, der er **sprogneutrale** i alle fire sprog, så den har
  //    ingen grund til en stængel pr. sprog. Det er den ærlige række: en
  //    negativ case må ikke pege på en, der nu er dækket, for så bliver den grøn
  //    og porten kan ikke se den fejl den er skrevet til at se.
  //    Det skete **to** gange her: casen pegede først på `Shipping policy` DA,
  //    som opgave 54 netop rettede, og siden på `Whistleblower / Hinweisgeber`
  //    DA, som opgave 55 netop rettede. Selftesten blev rød med "gav en grøn
  //    port" begge gange — hvilket er præcis det, den er skrevet til at fange.
  expectRed("R1 (tabellen kræver en stængel)", contractCoverage,
    [...COVERAGE, ["General contact address", "DA", "dansk side med kun ét juridisk link"]],
    STEMS, FIXTURES);

  // 6 + 4 + 2 = de otte negative cases fra R1–R4 og de to dækningsregler, før
  // mutationerne. Mutationerne tæller hver fire (to motorer × to forventninger).
  const forventet = 12 + MUTATIONS.length * 4 + 2;
  if (caught.length !== forventet) {
    failures.push(`selftest: forventede ${forventet} negative cases fanget, fangede ${caught.length}`);
  } else {
    passed += forventet;
  }
}

if (failures.length) {
  for (const f of failures) console.error(`FAIL  ${f}`);
  console.error(`${failures.length} JURIDISK-SPROG FEJL`);
  process.exit(1);
}
console.log(
  `${passed} juridisk-sprogtest bestået — ${FIXTURES.length} fixtures, ${COVERAGE.length} (mønster, sprog) dækket`
);
