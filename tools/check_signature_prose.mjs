/**
 * Tæller et værktøjsnavn i prosa som et værktøj?
 *
 *   node tools/check_signature_prose.mjs
 *   node tools/check_signature_prose.mjs --selftest   (beviser at den kan fejle)
 *
 * Opgave 58. Opgave 57 rettede `trackers`, `consent` og `forms` i **alle tre
 * produkter**: `TRACKER_SIGNATURES`, `CONSENT_SIGNATURES` og
 * `FORM_PLUGIN_SIGNATURES` læste hele HTML'en, så en side der *skriver* "vi
 * bruger Matomo" fik en rød tracker-række og en fix, der beder kunden
 * installere en samtykkeplatform de ikke har brug for. Målt: 48 falske fund,
 * 12 pr. sprog i fire sprog, i begge motorer og i pluginen.
 *
 * Ingen af de 23 eksisterende steps måler den nye egenskab. De måler at en
 * rigtig side stadig findes (trin 20, 21, 23) og at etiketten følger dommet
 * (trin 19) — ikke at **prosa ikke tæller**. Uden denne port kan hele
 * rettelsen forsvinde i en diff der kun rører de tre `teknisk`-kald, og alle
 * 23 steps er grønne. Samme situation som opgave 33 fandt i inline-JS-
 * kontrollen, hvor porten endte på `exit 0`.
 *
 * Fire kontrakter, alle egenskaber ved adfærden:
 *
 *   R1  **Prosa giver nul fund.** Fire sprog, hvert med en prosa-fixture der
 *       bruger navne på trackere, samtykkeplatforme og formular-plugins i
 *       løbende tekst ved siden af en rigtig formular. Begge motorer **og**
 *       pluginen skal finde nul — ikke "færre", nul. Det er opgave 57s 48 fund
 *       kodet som fixtures i stedet for som en engangskørsel.
 *   R2  **Ingen tabt dækning.** En rigtig WordPress-side pr. mekanisme:
 *       `<script src="…gtm.js">`, inline `gtag(`, GA's og Hotjars
 *       `<noscript>`-pixel, `<div class="wpcf7">` og `<link …klaro.css>`.
 *       Uden R2 kan en for **bred** beskæring bestå R1 og tage point fra
 *       kunden — det er præcis den fare, der gjorde at opgave 57 afviste en ren
 *       scriptregel. R1 alene kan ikke se den forskel; kun R2 kan. Selftestens
 *       fjerde mutation beviser det: den efterlader R1 grøn og gør R2 rød.
 *   R3  **De tre produkter er ens.** Samme fund i alle tre, og de to motorer
 *       skal være byte-identiske i `label` og `detail` for alle tre grupper.
 *       Læst på **holdene**, ikke på hele `checks`-objektet: `.detail` på
 *       `checks` er `undefined`, og en påstand om nul fund bliver grøn af den
 *       grund (opgave 56 fund 4). Siden opgave 59 gælder ligheden også for
 *       **pluginens** tracker-detalje: motoren skrev "…was also detected."
 *       mens pluginen skrev "…was also detected (Klaro / …)" om det samme
 *       website, og undtagelsen der gjorde R3 grøn for lige netop den forskel
 *       er nu væk.
 *   R4  **`dora` er stadig urørt.** "vi har en business continuity plan" i prosa
 *       skal stadig finde `BC/DR planning reference` i alle tre produkter. Det
 *       er undtagelsen `matched_signatures()` skriver i sin docblock: DORA-
 *       markørerne er påstande om *virksomheden*, ikke om at kode kører. Uden
 *       R4 bliver undtagelsen usynlig, og en senere agent "forenkler" den væk
 *       fordi den ser unødigt speciel ud. R4 måler **også** den lange engelske
 *       form med mellemrum, som var den anden lækage i opgave 59.
 *
 * Fund-listen læses **af porten selv**: navnene parses ud af produkternes egne
 * signatur-tabeller, så en ny signatur dækkes automatisk, og en tabel der ikke
 * kan parses gør porten rød frem for grøn. Samme "dækkede-ikke-antaget"-regel
 * som trin 21.
 *
 * Hvad porten **ikke** dækker, og hvorfor: den måler at portens egne fixtures
 * er fundet, ikke at signatur-tabellerne er *fuldstændige*. En markør der
 * mangler helt i en tabel kan porten ikke se — den læser navnene, den læser
 * ikke formernes rækkevidde. Det er opgave 59s tredje lækage forklaret:
 * `googletagmanager.com/ns.html` var i ingen tabel, så intet fixture kunne
 * finde den. De to mutationer der fjerner `ns.html` igen er derfor netop så
 * vigtige som fixtures — de binder tabellen til et krav om dækning.
 *
 * Spec: `docs/eucomply-signatur-prosa.md`.
 */

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
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
const PLUGIN = join(REPO, "plugin", "eucomply.php");
const PROBE = join(REPO, "tools", "plugin_probe.php");

/** Ét IP-literal: assertPublicTarget slår værter op i DNS, og porten skal ikke kræve netværk. */
const TARGET = "https://93.184.216.34/";

const SPROG = { DA: "dansk", SV: "svensk", NL: "nederlandsk", EN: "engelsk" };

/** De grupper R1 og R3 måler. `dora` er R4s gruppe og er bevidst ikke her. */
const GRUPPER = ["trackers", "cookies", "forms"];

/** Hvor mange navne hver signatur-tabel skal have, før porten går videre. */
const MINDST = { trackers: 12, consent: 21, forms: 2, dora: 9 };

/** Navnet på tabellen i de to JS-motorer. `cookies` læser CONSENT_SIGNATURES. */
const MOTOR_TABEL = {
  trackers: "TRACKER_SIGNATURES",
  consent: "CONSENT_SIGNATURES",
  forms: "FORM_PLUGIN_SIGNATURES",
  dora: "DORA_SIGNATURES",
};

/**
 * R1s fixtures: navne på trackere, samtykkeplatforme og formular-plugins i
 * **løbende tekst**, ved siden af en rigtig formular. Formularen er der, fordi
 * ellers er `forms` grøn af den trivielle grund at der ingen er, og porten så
 * ikke måler det den påstår at måle.
 *
 * Det er opgave 57s fund, kodet som fixtures: de navne der gav en rød række,
 * i de sprog målingen blev taget på.
 */
const PROSA = {
  DA: "Vi bruger Matomo til statistik, og vores samtykkeplatform er Klaro. "
    + "Kontaktformularen er bygget med Contact Form 7, og nyhedsbrevet sender vi "
    + "gennem Mailchimp. Tidligere brugte vi Google Analytics og Facebook Pixel.",
  SV: "Vi använder Matomo för statistik och vår samtyckesplattform är Klaro. "
    + "Kontaktformuläret är byggt med Contact Form 7, och nyhetsbrevet skickas via "
    + "Mailchimp. Tidigare använde vi Google Analytics och Facebook Pixel.",
  NL: "We gebruiken Matomo voor statistieken en ons toestemmingsplatform is Klaro. "
    + "Het contactformulier is gebouwd met Contact Form 7, en de nieuwsbrief "
    + "versturen we met Mailchimp. Eerder gebruikten we Google Analytics en "
    + "Facebook Pixel.",
  // Beviset på at fejlen ikke var et sprogproblem: de fleste af navnene er de
  // samme i alle fire sprog, kun få forskellige. En bredere port ville være
  // nemligere, og det er derfor den er skrevet fire sprog.
  EN: "We write about Matomo, Klaro, Cookiebot, Hotjar and Typeform on this page, "
    + "because a blog post about analytics tools mentions them. The form below was "
    + "built with Contact Form 7. We used to run Google Analytics and Facebook Pixel.",
};

function side(indhold) {
  return `<html><body><main>${indhold}</main></body></html>`;
}

/** Prosa **og** formularmarkup, i alle fire sprog. */
const PROSA_FIXTURES = Object.keys(PROSA).map((lang) => ({
  navn: `prosa (${lang})`,
  lang,
  slags: "prosa",
  html: side(
    `<h1>Om os</h1><p>${PROSA[lang]}</p>`
    + `<form action="/kontakt" method="post"><input name="email" type="email" required></form>`
  ),
}));

// Den modsatte fejlretning, målt på Pinterests **billed**-CDN. En rettelse af
// opgave 61 skriver `s\.pinimg\.com\/ct\/`, fordi det er den dokumenterede
// sti — men den naturlige næste bevægelse er at skrive hele værten, og Pinters
// billeder ligger på `i.pinimg.com`. En butik der har lagt tre opslagsbilleder
// op og **intet** tag har intet at slette på, og det er den fejlklasse hele
// rækken af opgaverne 51–60 handler om: en mangel rettet med en for bred
// regel. Derfor er den en R1-fixture — prosa-kontrakten kræver nul fund — og
// derfor fanger mutationen nedenfor den.
PROSA_FIXTURES.push({
  navn: "Pinterest-billede (CDN, ikke tag)",
  lang: "EN",
  slags: "prosa",
  html: side(
    "<h1>Lookbook</h1><p>Photos from our autumn collection.</p>"
    + '<img src="https://i.pinimg.com/originals/4a/2b/4a2b1c3d4e5f60718293a4b5c6d7e8f9.jpg" alt="Autumn collection" width="320" height="480">'
    + '<form action="/kontakt" method="post"><input name="email" type="email" required></form>'
  ),
});

/**
 * R2: en rigtig WordPress-side pr. mekanisme. `gruppe` er den række der skal
 * navne fundet i motorerne, `phpGruppe` er den række pluginen gør det i, når
 * den gør det i en anden, og `liste` er den signatur-tabel det forventede navn
 * **kommer fra** — ikke den række det står i.
 *
 * `phpGruppe` er ikke en bortfald: pluginens `cookies` er et
 * **WordPress-tilstandstjek** — den læser hvilke consent-plugins der er
 * *installeret*, ikke markup'en. Dens consent-*signaturer* læses derimod af
 * `check_trackers()`, som nævner platformen i `detail`. Derfor måles Klaro i
 * pluginen på `trackers` med en tracker ved siden af, ellers står dens navn
 * ingen steder i den betalte rapport.
 */
const MEKANISME = [
  {
    navn: "GTM som eksternt script", gruppe: "trackers", phpGruppe: "trackers", liste: "trackers",
    forventet: "Google Analytics / GTM",
    html: side('<script src="https://www.googletagmanager.com/gtm.js?id=GTM-ABC"></script><p>Hej</p>'),
  },
  {
    navn: "gtag() inline i et script", gruppe: "trackers", phpGruppe: "trackers", liste: "trackers",
    forventet: "Google Analytics / GTM",
    html: side("<script>gtag('config', 'G-1234');</script><p>Hej</p>"),
  },
  {
    // Googles egen no-JavaScript-pixel. Den ligger i `<noscript>`, altså i den
    // kode-del af siden — opgave 57s kodebeholder beholder den.
    navn: "GA's noscript-pixel", gruppe: "trackers", phpGruppe: "trackers", liste: "trackers",
    forventet: "Google Analytics / GTM",
    html: side('<noscript><img height="1" width="1" style="display:none" src="https://www.google-analytics.com/collect?v=2&amp;tid=UA-1&amp;cid=1"></noscript><p>Hej</p>'),
  },
  {
    // Hotjars no-JavaScript-sporing. Samme mekanisme som ovenfor, anden
    // udbyder: `<noscript>` er bevis, prosa er ikke.
    navn: "Hotjars noscript-sporing", gruppe: "trackers", phpGruppe: "trackers", liste: "trackers",
    forventet: "Hotjar",
    html: side('<noscript><a href="https://www.hotjar.com" target="_blank"><img src="https://static.hotjar.com/hjblockedpixels/banner.gif" border="0" alt=""></a></noscript><p>Hej</p>'),
  },
  {
    // Googles egen no-JavaScript-fallback for GTM. Det er det snippet Googles
    // dokumentation beder **alle** GTM-sites installere, og på en side der kun
    // har fallbacken er det den eneste analytics-reference. Mønsteret matchede
    // kun `gtm.js`, så "Third-party trackers: 0 found" stod på en side der
    // sender et pixel. Målt før rettelsen: 0 fund i alle tre produkter.
    navn: "GTM's ns.html-fallback", gruppe: "trackers", phpGruppe: "trackers", liste: "trackers",
    forventet: "Google Analytics / GTM",
    html: side('<noscript><iframe height="0" width="0" style="display:none;visibility:hidden" src="https://www.googletagmanager.com/ns.html?id=GTM-ABC"></iframe></noscript><p>Hej</p>'),
  },
  {
    // Den dyreste lækage målt til dato, og den der gav den grønne række. GA4
    // indlæses med ét eksternt script, og når konfigurationen ligger i en
    // **aparte fil** står der intet `gtag(` i markup'en. Det gamle mønster
    // ramte kun det indlejrede kald, så denne almindeligste GA4-opsætning gav
    // `Third-party trackers: 0 found` — altså *modsatte* fejlretning af
    // opgave 57: kunden fik en grøn række og ingen grund til samtykke.
    // Målt før rettelsen: 0 fund i alle tre produkter.
    navn: "GA4's gtag/js-script", gruppe: "trackers", phpGruppe: "trackers", liste: "trackers",
    forventet: "Google Analytics / GTM",
    html: side('<script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC123"></script><p>Hej</p>'),
  },
  {
    // Samme URL, andet id-præfiks: Googles **Ads**-tags indlæses også fra
    // `gtag/js`, med `AW-` i stedet for `G-`. Fixturet findes, fordi en
    // "rettelse" der skriver `gtag\/js\?id=G-` ville få den grønne fixture
    // ovenfor til at bestå og denne til at fejle — den skal kunne skelne de to.
    navn: "Google Ads-tag på gtag/js", gruppe: "trackers", phpGruppe: "trackers", liste: "trackers",
    forventet: "Google Analytics / GTM",
    html: side('<script async src="https://www.googletagmanager.com/gtag/js?id=AW-9876543"></script><p>Hej</p>'),
  },
  {
    // Pinterests egen dokumentation ("Install the base code",
    // help.pinterest.com/business/article/install-the-base-code, hentet
    // 2026-09-27) indlæser tagget fra `s.pinimg.com/ct/core.js` og kalder
    // `pintrk('load', …)`. Det gamle mønster ramte **kun** indlejrede
    // `pintrk(`-kald, så en side hvor et samtykketool har flyttet de
    // indlejrede scripts ud i en bundle — eller en CSP der dem blokerer — gav
    // "Third-party trackers: 0 found" på en side der kører tagget. Målt før
    // rettelsen: 0 fund i alle tre produkter.
    navn: "Pinterest-tagens loader", gruppe: "trackers", phpGruppe: "trackers", liste: "trackers",
    forventet: "Pinterest Tag",
    html: side('<script async src="https://s.pinimg.com/ct/core.js"></script><p>Hej</p>'),
  },
  {
    // Samme dokumentations side, anden sti: `<noscript>`-pixelet på
    // `ct.pinterest.com/v3/?tid=…&event=init&noscript=1`. Det er Pinterests
    // egen no-JavaScript-fallback, præcis som Googles og Hotjars, og porten
    // har allerede begge de andre to. Målt før rettelsen: 0 fund i alle tre.
    navn: "Pinterest-tagens noscript-pixel", gruppe: "trackers", phpGruppe: "trackers", liste: "trackers",
    forventet: "Pinterest Tag",
    html: side('<noscript><img height="1" width="1" style="display:none" alt="" src="https://ct.pinterest.com/v3/?tid=2612345678901&amp;event=init&amp;noscript=1"></noscript><p>Hej</p>'),
  },
  {
    // Contact Form 7 lever som `<div class="wpcf7">` i **markup'en**, ikke som
    // et script. Det er grunden til at opgave 57 beholdte attributterne, og det
    // er derfor denne fixture findes: en ren scriptregel ville have slettet den
    // mest almindelige WordPress-formulardetektion.
    navn: "Contact Form 7 som attribut", gruppe: "forms", phpGruppe: "forms", liste: "forms",
    forventet: "Contact Form 7 / WPForms / Formidable / Gravity / Fluent / Elementor",
    html: side('<div class="wpcf7"><p>Send en besked</p></div>'),
  },
  {
    // Klaro kommer som et stylesheet-link, altså igen en attribut og ikke kode.
    navn: "Klaro som stylesheet-link", gruppe: "cookies", phpGruppe: "trackers", liste: "consent",
    forventet: "TarteAuCitron / Klaro / Osano / CookieConsent",
    html: side('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/klaro@1.0.5/dist/klaro.css">'
      + '<script src="https://www.googletagmanager.com/gtm.js?id=GTM-ABC"></script><p>Hej</p>'),
  },
];

/**
 * R4. DORA-markørerne er påstande om virksomheden, så de læser prosa med
 * vilje. Samme undtagelse i alle tre produkter, og den skal blive ligesådan.
 */
const DORA_FIXTURES = [
  {
    navn: "dora i prosa (dansk)", lang: "DA", slags: "dora",
    // `BCP-plan` og `DR-plan` er de formuleringer et dansk eller norsk
    // bureau skriver, og de er fundet i dag. Den lange engelske form er målt i
    // fixturet nedenfor — den var **ikke** fundet i noget produkt, fordi
    // `business[_-]?continuity` kun tillod bindestreg. Samme separatorfejl som
    // opgave 52 fandt i `terms` og opgave 55 i `sla`.
    html: side("<h1>Driftssikkerhed</h1><p>Vi har en BCP-plan og en DR-plan, og vi "
      + "publicerer vores MX- og DMARC-opsætning.</p>"),
  },
  {
    navn: "dora i prosa (engelsk, lange former)", lang: "EN", slags: "dora",
    // Den sætning en **engelsk** sikkerhedsside faktisk skriver, med mellemrum
    // mellem ordene. Målt før rettelsen: `business continuity plan`,
    // `incident response` og `status page` gav **0 af 3** i alle tre produkter,
    // fordi separatoren var `[_-]?`. Kun de enkeltstående tokens (DKIM, SPF,
    // `failover`) kunne finde noget, og de er tilfældigvis ikke dem siden
    // handler om. Det er den betalte DORA-række, der taber point på en side der
    // gør præcis det tjekket spørger efter.
    html: side("<h1>Business continuity</h1><p>We have a business continuity plan and an "
      + "incident response process, and we publish a public status page for uptime. "
      + "We publish our SPF record and our DMARC policy too.</p>"),
  },
];

/** Navnene i en gruppes signatur-tabel, læst ud af produktetens egen fil. */
function signaturNavne(kilde, gruppe, php) {
  const start = php
    ? new RegExp(`'${gruppe}'\\s*=>\\s*array\\(`)
    : new RegExp(`const ${MOTOR_TABEL[gruppe]}\\s*=\\s*\\[`);
  const fra = start.exec(kilde);
  assert.ok(
    fra,
    `kilden har ingen signatur-tabel for «${gruppe}» — porten ville være grøn uden at vide hvad den måler`
  );
  const resten = kilde.slice(fra.index);
  const til = resten.indexOf("\n]");
  const blok = til === -1 ? resten : resten.slice(0, til);
  const navne = [...blok.matchAll(php ? /'name'\s*=>\s*'([^']+)'/g : /name:\s*"([^"]+)"/g)]
    .map((m) => m[1]);
  assert.ok(
    navne.length >= MINDST[gruppe],
    `signatur-tabellen for «${gruppe}» gav ${navne.length} navne, forventede mindst ${MINDST[gruppe]} — ` +
      "en tabel der ikke kan parses gør porten grøn uden at den har noget at se på"
  );
  return navne;
}

/** Alle fundne signatur-navne i en doms tekst. */
function fundneNavne(verdict, navne) {
  const tekst = `${(verdict && verdict.label) || ""} ${(verdict && verdict.detail) || ""}`;
  return navne.filter((n) => tekst.includes(n));
}

/** Samme fund som en liste, så to lister kan sammenlignes i en assert. */
function fundneListe(verdict, navne) {
  return fundneNavne(verdict, navne).sort().join(" | ");
}

// ── Kør en motor mod én fixture ──────────────────────────────────────────────

async function engineChecks(runScan, html) {
  const saved = globalThis.fetch;
  globalThis.fetch = async () => new Response(html, { status: 200, headers: { "Content-Type": "text/html" } });
  try {
    const scan = await runScan(TARGET);
    for (const gruppe of [...GRUPPER, "dora"]) {
      assert.ok(scan.checks[gruppe], `motoren kender ikke tjekket ${gruppe}`);
    }
    return scan.checks;
  } finally {
    globalThis.fetch = saved;
  }
}

/** Kør pluginen på én fixture gennem proben, dens ene sandhed om hvad WordPress gør. */
function pluginChecks(html) {
  const dir = mkdtempSync(join(tmpdir(), "eucomply-prosa-"));
  const file = join(dir, "fixture.json");
  try {
    writeFileSync(file, JSON.stringify({ html }));
    const out = execFileSync("php", [PROBE, file], { encoding: "utf8", stdio: ["ignore", "pipe", "inherit"] });
    const parsed = JSON.parse(out);
    for (const gruppe of [...GRUPPER, "dora"]) {
      assert.ok(parsed[gruppe], `pluginen kender ikke tjekket ${gruppe}`);
    }
    return parsed;
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

// ── Kontrakterne. Porten OG selftesten kalder disse, så en negativ case ikke
// kan blive grøn ved at forvente noget andet end det porten kræver.

/**
 * R1: prosa giver nul fund. Læst på **holdene** — `checks` er ikke `checks.trackers`.
 */
function contractR1(domme, fixture, navne) {
  for (const [hvem, dom] of domme) {
    for (const gruppe of GRUPPER) {
      // Pluginens `cookies` læser **installerede** plugins, ikke markup: dens
      // detalje nævner "WP Consent API" på hver eneste side, uanset prosa, for
      // det er den sætning den bruger når den intet fandt. At kræve nul
      // signatur-navne dér ville være rød af design, og en regel der er rød af
      // design læses ikke. Dens markup-bevis er consent-signaturerne i
      // `trackers`, og dem måler porten i stedet.
      if (hvem === "pluginen" && gruppe === "cookies") continue;
      const fundne = fundneNavne(dom[gruppe], gruppe === "cookies" ? navne.consent : navne[gruppe]);
      assert.equal(
        fundne.length,
        0,
        `${hvem} tæller ${fundne.join(", ")} på «${fixture.navn}» — navnet står i løbende tekst, ` +
          "og en sætning er ikke et værktøj der kører"
      );
    }
  }
  // Og pluginens eget consent-bevis: nul fund på en prosa-side. **Helt uden for
  // løkken ovenfor**, fordi pluginens `cookies`-række er sprunget over — så
  // dens consent-bevis skal måles et andet sted end der, hvor de to motorer
  // måles. `domme[2][1]`, ikke `domme[2]`: elementet er et [hvem, dom]-par, og
  // `.trackers` på paret er `undefined` — som gjorde regelen grøn uden at se
  // noget. Det er samme fælde som R3's to niveauer.
  const php = domme[2] ? domme[2][1] : null;
  if (php) {
    const fundne = fundneNavne(php.trackers, navne.consent);
    assert.equal(
      fundne.length,
      0,
      `pluginen tæller ${fundne.join(", ")} på «${fixture.navn}» — navnet står i løbende tekst, ` +
        "og en sætning er ikke en samtykkeplatform der kører"
    );
  }
  // Og dommen skal sige det samme, ikke bare tie stilhedsmæssigt. Uden dette kan
  // en motor finde nul fordi den **kørte sig ihjel** på dommen.
  const motor = domme[0][1];
  assert.equal(Boolean(motor.trackers.pass), true, `motoren består ikke en prosa-side: ${motor.trackers.label}`);
  assert.equal(Boolean(motor.cookies.pass), false, `motoren består cookies på prosa: ${motor.cookies.label}`);
}

/** R2: ingen tabt dækning. En for bred beskæring skal være rød her. */
function contractR2(domme, fixture, navne) {
  for (const [hvem, dom] of domme) {
    // Rækken afhænger af **produktet** (pluginens `cookies` er et
    // tilstandstjek), listen af **navnet** — de er ikke det samme, og at
    // blande dem gav en grøn R2 på en plugin der ikke så Klaro overhovedet.
    const gruppe = hvem === "pluginen" ? fixture.phpGruppe : fixture.gruppe;
    const fundne = fundneNavne(dom[gruppe], navne[fixture.liste]);
    assert.ok(
      fundne.includes(fixture.forventet),
      `${hvem} finder ikke «${fixture.forventet}» på «${fixture.navn}» `
        + `(rapporten siger: "${dom[gruppe].detail}") — rettelsen har taget dækning fra kunden`
    );
  }
}

/**
 * R3: de tre produkter er ens.
 *
 * Fund-listen skal være **identisk** i alle tre, og de to motorer skal være
 * byte-identiske i `label` og `detail` for alle tre grupper. Pluginens
 * `trackers` er skrevet med motorens sætninger, så den skal også være
 * identisk der — hele detaljen, ikke kun etiketten.
 *
 * Pluginens `cookies` kan **ikke** være med i ligheden, og det er ikke en
 * undtagelse for lettede: det er et WordPress-tilstandstjek, der læser hvilke
 * consent-plugins der er *installeret*. Det sammenlignelige er derfor dens
 * consent-*bevis* — de signaturer `check_trackers()` læser i markup'en — og
 * det holdes op mod motorens `cookies`. Skrives det forkert, får en kunde to
 * svar på det samme spørgsmål: "har sitten en samtykkeplatform?"
 */
function contractR3(domme, navne) {
  // **To** niveauer. `domme` er [hvem, dom]-par, så `const [a, b, c]` giver
  // parene og ikke dommene — og så læser R3 `.label` på `undefined` og er
  // grøn af den forkerte grund. Det er præcis fælden opgave 52 fund 4
  // dokumenterede, og den er her fordi det er den nemmeste fejl at lave i en
  // regel der sammenligner to lister.
  const [[, a], [, b], [, c]] = domme;
  for (const gruppe of GRUPPER) {
    const i = gruppe === "cookies" ? navne.consent : navne[gruppe];
    assert.equal(
      fundneListe(b[gruppe], i),
      fundneListe(a[gruppe], i),
      `de to motorer er uenige om fund i ${gruppe}: «${fundneListe(a[gruppe], i)}» mod «${fundneListe(b[gruppe], i)}»`
    );
    assert.equal(b[gruppe].label, a[gruppe].label, `de to motorer har ulik etiket i ${gruppe}`);
    assert.equal(b[gruppe].detail, a[gruppe].detail, `samme dom, to rapporter i ${gruppe}`);
  }
  // De to grupper pluginen læser markup for, skal finde det samme som motorerne.
  for (const gruppe of ["trackers", "forms"]) {
    assert.equal(
      fundneListe(c[gruppe], navne[gruppe]),
      fundneListe(a[gruppe], navne[gruppe]),
      `pluginen er uenig med motorerne om fund i ${gruppe}: «${fundneListe(a[gruppe], navne[gruppe])}» mod «${fundneListe(c[gruppe], navne[gruppe])}»`
    );
  }
  // Etiketten skal vælge ens, og **detaljen skal være ens for `trackers`**. Den
  // gjorde det ikke før opgave 59: pluginen skrev "…was also detected
  // (TarteAuCitron / Klaro / …)" mens motoren skrev "…was also detected." — samme
  // dom, to forskellige rapporter om det *samme* website, og den betalte var den
  // mere informative. Da motoren blev rettet til at navngive platformen, kunne
  // undtagelsen fjernes: de to produkter skal nu svare præcis det samme, så
  // holdet sammenligner hele detaljen og ikke bare om sætningen er med.
  assert.equal(
    c.trackers.label,
    a.trackers.label,
    `pluginens tracker-etiket afviger fra motorens: «${a.trackers.label}» mod «${c.trackers.label}»`
  );
  assert.equal(
    c.trackers.detail,
    a.trackers.detail,
    `samme dom, to rapporter i tracker-detaljen: «${a.trackers.detail}» mod «${c.trackers.detail}»`
  );
  // Og platformens **navn** skal stå i motorens egen rapport, når den fandt en.
  // Ellers kunne en motor finde platformen, skrive "was also detected" og være
  // grøn på detail-ligheden fordi pluginen heller ikke skrev noget navn — det er
  // præcis den fejlretning R3 holdt fast ved at sammenligne sætningen alene.
  const fundetPlatform = fundneNavne(a.trackers, navne.consent);
  if (fundetPlatform.length) {
    assert.equal(
      c.trackers.detail,
      a.trackers.detail,
      "platformens navn skal stå i begge produkter"
    );
    assert.ok(
      fundetPlatform.every((n) => a.trackers.detail.includes(n)),
      `motoren fandt ${fundetPlatform.join(", ")} men skrev det ikke i rapporten: "${a.trackers.detail}"`
    );
  }
  // Og pluginens consent-bevis skal være motorens `cookies`-fund.
  assert.equal(
    fundneListe(c.trackers, navne.consent),
    fundneListe(a.cookies, navne.consent),
    `pluginen og motoren er uenige om samtykkeplatformen: «${fundneListe(a.cookies, navne.consent)}» mod «${fundneListe(c.trackers, navne.consent)}»`
  );
  // Pluginens `cookies` læser ikke markup, så den må ikke navngive en platform
  // den ikke kan se. Undtagelsen er "WP Consent API": det er pluginens **eget**
  // faste sprog ("No known GDPR cookie consent plugin or WP Consent API
  // detected."), og det navn tilfældigvis også findes i CONSENT_SIGNATURES. Et
  // navne-kollisions-fund, ikke et fund — og det er målt, ikke antaget.
  const uvedkommende = fundneNavne(c.cookies, navne.consent).filter((n) => n !== "WP Consent API");
  assert.equal(
    uvedkommende.length,
    0,
    `pluginens cookie-tjek navngiver «${uvedkommende.join(", ")}» — det læser installerede plugins, ikke markup`
  );
}

/** R4: `dora` læser prosa. Undtagelsen skal blive ligesådan. */
function contractR4(domme, fixture, navne) {
  for (const [hvem, dom] of domme) {
    const fundne = fundneNavne(dom.dora, navne.dora);
    assert.ok(
      fundne.includes("BC/DR planning reference"),
      `${hvem} finder ikke «BC/DR planning reference» på «${fixture.navn}» (rapporten siger: "${dom.dora.detail}") — `
        + "DORA-markørerne er påstande om virksomheden, så prosa er bevis for dem"
    );
  }
  const detaljer = domme.map(([, dom]) => dom.dora.detail);
  assert.equal(detaljer[1], detaljer[0], "de to motorer er uenige om DORA-markørerne");
  assert.equal(detaljer[2], detaljer[0], "pluginen er uenig med motorerne om DORA-markørerne");
}

// ── Kør porten ───────────────────────────────────────────────────────────────

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

/** Navnene i hver gruppe, for hvert produkt. Porten **og** selftesten læser dem herfra. */
function laesSignaturer(fil, php) {
  const kilde = readFileSync(fil, "utf8");
  return {
    trackers: signaturNavne(kilde, "trackers", php),
    consent: signaturNavne(kilde, "consent", php),
    forms: signaturNavne(kilde, "forms", php),
    dora: signaturNavne(kilde, "dora", php),
  };
}

const MOTOR_NAVNE = laesSignaturer(join(REPO, "shared", "scan-engine.js"), false);
const PHP_NAVNE = laesSignaturer(PLUGIN, true);

const FIXTURES = [...PROSA_FIXTURES, ...MEKANISME, ...DORA_FIXTURES];

for (const fixture of FIXTURES) {
  const domme = [];
  for (const [hvem, , runScan] of ENGINES) domme.push([hvem, await engineChecks(runScan, fixture.html)]);
  domme.push(["pluginen", pluginChecks(fixture.html)]);

  if (fixture.slags === "prosa") {
    await test(`R1 prosa er ikke et fund: ${fixture.navn}`, () => contractR1(domme, fixture, MOTOR_NAVNE));
  } else if (fixture.slags === "dora") {
    await test(`R4 dora læser prosa: ${fixture.navn}`, () => contractR4(domme, fixture, MOTOR_NAVNE));
  } else {
    await test(`R2 ingen tabt dækning: ${fixture.navn}`, () => contractR2(domme, fixture, MOTOR_NAVNE));
  }
  await test(`R3 de tre produkter er ens: ${fixture.navn}`, () => contractR3(domme, MOTOR_NAVNE));
}

console.log(
  `${passed} signatur-prosatest bestået — ${FIXTURES.length} fixtures i ${Object.keys(PROSA).length} sprog, `
    + `${PROSA_FIXTURES.length} prosa-sprog målt, ${MEKANISME.length} mekanismer, 4 kontrakter, 3 produkter`
);

if (failures.length) {
  for (const f of failures) console.error(`FEJL  ${f}`);
  process.exit(1);
}

// ── Selftest: bevis at porten kan fejle ──────────────────────────────────────

if (process.argv.includes("--selftest")) {
  const caught = [];
  const expectRed = (name, contract, ...args) => {
    try {
      contract(...args);
      failures.push(`selftest: ${name} gav en grøn port — den kan ikke se den fejl`);
    } catch {
      caught.push(name);
    }
  };

  const prosa = PROSA_FIXTURES[0];
  const wpcf7 = MEKANISME.find((m) => m.gruppe === "forms");
  const klaro = MEKANISME.find((m) => m.gruppe === "cookies");

  // 1. R1: en motor tæller prosa igen — præcis fejlen opgave 57 rettede.
  expectRed("R1 (fund på prosa)", contractR1, [
    ["motoren i repoet", { trackers: { label: "1 tracker(s) with NO consent platform", detail: "Trackers found in page markup: Matomo / Piwik." } }],
  ], prosa, MOTOR_NAVNE);

  // 2. R1: etiketten siger "0 fundet", mens detaljen **nævner** et fund. Det er
  //    den falske beståelse fra en værre motor — en kunde læser etiketten og
  //    tror der ikke er noget. R1 læser begge dele af dommen, så den skal se
  //    det; en regel der kun læser etiketten ville være grøn her.
  expectRed("R1 (etiketten modsiger fundet)", contractR1, [
    ["motoren i repoet", {
      trackers: { label: "Third-party trackers: 0 found", detail: "No third-party marketing/analytics trackers found in the served HTML, but Matomo / Piwik was named.", pass: true },
      cookies: { label: "No consent banner detected", detail: "", pass: false },
    }],
  ], prosa, MOTOR_NAVNE);

  // 3. R1: motoren **består** cookies på en prosa-side.
  expectRed("R1 (cookies består på prosa)", contractR1, [
    ["motoren i repoet", {
      trackers: { label: "Third-party trackers: 0 found", detail: "No third-party marketing/analytics trackers found in the served HTML.", pass: true },
      cookies: { label: "Consent platform: Klaro", detail: "Detected: TarteAuCitron / Klaro / Osano / CookieConsent", pass: true },
    }],
  ], prosa, MOTOR_NAVNE);

  // 4. R1: dommen er ikke en dom, fordi motoren kørte sig ihjel. R1 kræver de to
  //    pass-udsagn, så en motor uden dem er rød — også uden et eneste fund.
  expectRed("R1 (dommen mangler helt)", contractR1, [
    ["motoren i repoet", { trackers: { label: "", detail: "" } }],
  ], prosa, MOTOR_NAVNE);

  // 5. R2: dækning tabt. Parret til R1: den samme motor må gerne være grøn på
  //    R1 og rød på R2 — ellers beviser parret intet.
  expectRed("R2 (dækning tabt)", contractR2, [
    ["motoren i repoet", { forms: { label: "Page has neither form markup nor a form plugin", detail: "No HTML forms detected on this page." } }],
  ], wpcf7, MOTOR_NAVNE);

  // 6. R3: de to motorer er uenige om fundet.
  expectRed("R3 (motorer uenige om fund)", contractR3, [
    ["motoren i repoet", { trackers: { label: "a", detail: "a" }, cookies: { label: "x", detail: "x" }, forms: { label: "x", detail: "x" } }],
    ["den publicerede motor", { trackers: { label: "b", detail: "b" }, cookies: { label: "x", detail: "x" }, forms: { label: "x", detail: "x" } }],
    ["pluginen", { trackers: { label: "a", detail: "a" }, cookies: { label: "x", detail: "x" }, forms: { label: "x", detail: "x" } }],
  ], MOTOR_NAVNE);

  // 7. R3: ulik etiket mellem motorerne, samme fund.
  expectRed("R3 (ulik etiket, samme fund)", contractR3, [
    ["motoren i repoet", { trackers: { label: "1 tracker(s) with NO consent platform", detail: "a" }, cookies: { label: "x", detail: "x" }, forms: { label: "x", detail: "x" } }],
    ["den publicerede motor", { trackers: { label: "Third-party trackers: 1 found", detail: "a" }, cookies: { label: "x", detail: "x" }, forms: { label: "x", detail: "x" } }],
    ["pluginen", { trackers: { label: "1 tracker(s) with NO consent platform", detail: "a" }, cookies: { label: "x", detail: "x" }, forms: { label: "x", detail: "x" } }],
  ], MOTOR_NAVNE);

  // 8. R3: pluginen er uenig med motorerne om et fund i `forms`.
  expectRed("R3 (pluginen uenig om fund)", contractR3, [
    ["motoren i repoet", { trackers: { label: "a", detail: "a" }, cookies: { label: "x", detail: "x" }, forms: { label: "Contact Form 7 / WPForms / Formidable / Gravity / Fluent / Elementor detected", detail: "Form plugins detected: Contact Form 7 / WPForms / Formidable / Gravity / Fluent / Elementor." } }],
    ["den publicerede motor", { trackers: { label: "a", detail: "a" }, cookies: { label: "x", detail: "x" }, forms: { label: "Contact Form 7 / WPForms / Formidable / Gravity / Fluent / Elementor detected", detail: "Form plugins detected: Contact Form 7 / WPForms / Formidable / Gravity / Fluent / Elementor." } }],
    ["pluginen", { trackers: { label: "a", detail: "a" }, cookies: { label: "x", detail: "x" }, forms: { label: "x", detail: "x" } }],
  ], MOTOR_NAVNE);

  // 9. R3: pluginen **og** motoren er uenige om samtykkeplatformen.
  expectRed("R3 (uenige om samtykkeplatformen)", contractR3, [
    ["motoren i repoet", { trackers: { label: "a", detail: "a" }, cookies: { label: "Consent platform: Klaro", detail: "Detected: TarteAuCitron / Klaro / Osano / CookieConsent" }, forms: { label: "x", detail: "x" } }],
    ["den publicerede motor", { trackers: { label: "a", detail: "a" }, cookies: { label: "Consent platform: Klaro", detail: "Detected: TarteAuCitron / Klaro / Osano / CookieConsent" }, forms: { label: "x", detail: "x" } }],
    ["pluginen", { trackers: { label: "a", detail: "a" }, cookies: { label: "x", detail: "x" }, forms: { label: "x", detail: "x" } }],
  ], MOTOR_NAVNE);

  // 10. R3: pluginens cookie-tjek kan ikke se markup, så den må ikke navngive en
  //     platform den ikke har set.
  expectRed("R3 (pluginen navngiver en uset platform)", contractR3, [
    ["motoren i repoet", { trackers: { label: "a", detail: "a" }, cookies: { label: "x", detail: "x" }, forms: { label: "x", detail: "x" } }],
    ["den publicerede motor", { trackers: { label: "a", detail: "a" }, cookies: { label: "x", detail: "x" }, forms: { label: "x", detail: "x" } }],
    ["pluginen", { trackers: { label: "a", detail: "a" }, cookies: { label: "Cookie consent active", detail: "Detected: Cookiebot / OneTrust / Usercentrics / ConsentManager" }, forms: { label: "x", detail: "x" } }],
  ], MOTOR_NAVNE);

  // 11. R4: dora læser ikke prosa mere.
  expectRed("R4 (dora taber fundet)", contractR4, [
    ["motoren i repoet", { dora: { label: "No DORA-related page signals detected", detail: "No page-text references to failover, incident response or continuity were found." } }],
  ], DORA_FIXTURES[0], MOTOR_NAVNE);

  // 12. R3: motoren **finder** platformen men skriver ikke navnet i rapporten.
  //     Det var den gamle fejl: "A consent platform was also detected." Den
  //     gamle R3-regel var grøn for den, fordi den spurgte om sætningen var der
  //     — og den kan ikke se en motor der udelader navnet. Den nye regel
  //     sammenligner hele detaljen med pluginens og kræver navnet i rapporten.
  expectRed("R3 (motoren skriver ikke platformens navn)", contractR3, [
    ["motoren i repoet", {
      trackers: { label: "1 tracker(s) detected, consent platform present", detail: "Trackers found in page markup: Google Analytics / GTM. A consent platform was also detected." },
      cookies: { label: "Consent platform: TarteAuCitron / Klaro / Osano / CookieConsent", detail: "Detected: TarteAuCitron / Klaro / Osano / CookieConsent" },
      forms: { label: "x", detail: "x" },
    }],
    ["den publicerede motor", {
      trackers: { label: "1 tracker(s) detected, consent platform present", detail: "Trackers found in page markup: Google Analytics / GTM. A consent platform was also detected (TarteAuCitron / Klaro / Osano / CookieConsent)." },
      cookies: { label: "Consent platform: TarteAuCitron / Klaro / Osano / CookieConsent", detail: "Detected: TarteAuCitron / Klaro / Osano / CookieConsent" },
      forms: { label: "x", detail: "x" },
    }],
    ["pluginen", {
      trackers: { label: "1 tracker(s) detected, consent platform present", detail: "Trackers found in page markup: Google Analytics / GTM. A consent platform was also detected (TarteAuCitron / Klaro / Osano / CookieConsent)." },
      cookies: { label: "x", detail: "x" },
      forms: { label: "x", detail: "x" },
    }],
  ], MOTOR_NAVNE);

  // 13. R2: GTM's ns.html-fallback forsvinder igen. Den er den eneste
  //     analytics-reference på den fixture, så uden den er svaret "0 fundet".
  expectRed("R2 (GTM ns.html taber dækning)", contractR2, [
    ["motoren i repoet", { trackers: { label: "Third-party trackers: 0 found", detail: "No third-party marketing/analytics trackers found in the served HTML." } }],
  ], MEKANISME.find((m) => m.navn === "GTM's ns.html-fallback"), MOTOR_NAVNE);

  /*
   * Fire mutationer mod repoets egne filer.
   *
   * De tre første gør hver produkts kodebeholder til at læse hele HTML'en igen —
   * den uændrede fejl fra før opgave 57 — og porten skal blive rød på en
   * prosa-fixture. Alle tre er skrevet mod den **lange** linje, så de fejler
   * med "fandt ikke den linje den erstatter" den dag et nyt `teknisk`-kald
   * indsættes frem for at stå grønne på en mutation de ikke længere rammer
   * (samme selvbeskyttelse som opgave 29 og 51).
   *
   * Den fjerde er den modsatte fejlretning, og den er pointen med R2: en
   * beholder der kun læser kode og **ikke attributter** består R1 (prosa er jo
   * heller ikke kode) og mister Contact Form 7 og Klaro. Selftesten kræver
   * derfor præcis det: R1 grøn, R2 rød. Uden den mutation er parret R1/R2 en
   * påstand om at de kan modsige hinanden — R2 *skal* kunne være rød mens R1
   * er grøn, ellers beviser parret intet.
   */
  const MUTATIONER = [
    {
      navn: "motoren i repoet læser hele HTML'en igen",
      fil: join(REPO, "shared", "scan-engine.js"),
      forventer: "R1",
      foer: [
        { for: "  const teknisk = codeAndAttributes(html);", efter: "  const teknisk = html; // mutation: læs hele siden" },
      ],
    },
    {
      navn: "den publicerede motor læser hele HTML'en igen",
      fil: join(REPO, "eucomply-scanner", "engine", "index.js"),
      forventer: "R1",
      foer: [
        { for: "  const teknisk = codeAndAttributes(html);", efter: "  const teknisk = html; // mutation: læs hele siden" },
      ],
    },
    {
      navn: "pluginen læser hele HTML'en igen",
      fil: PLUGIN,
      forventer: "R1",
      foer: [
        {
          for: "        $haystack = ( 'dora' === $group ) ? $html : self::code_and_attributes( $html );",
          efter: "        $haystack = $html; // mutation: læs hele siden",
        },
      ],
    },
    {
      navn: "motoren i repoet læser kun kode og taber attributterne",
      fil: join(REPO, "shared", "scan-engine.js"),
      forventer: "R2",
      foer: [
        { for: "  if (!kode) return visibleText(html);", efter: "  if (!kode) return \"\"; // mutation: kun kode" },
        {
          for: "  return visibleText(html.replace(CODE_BLOCK, \"\\u0000\")) + \"\\n\" + kode.join(\"\\n\");",
          efter: "  return kode.join(\"\\n\"); // mutation: kun kode",
        },
      ],
    },
    /*
     * De fire nye er opgave 59s tre lækager, skrevet som mutationer mod
     * repoets egne filer. En lækage er en mangel, der ikke kan ses i en diff —
     * mønstret er der, det matcher bare ikke det, kunden skriver. Den eneste
     * måde at binde den er at tage rettelsen væk igen og kræve rødt.
     */
    {
      navn: "motoren i repoet taber GTM's ns.html-fallback",
      fil: join(REPO, "shared", "scan-engine.js"),
      forventer: "R2",
      fixture: "GTM's ns.html-fallback",
      foer: [
        {
          // Opdateret i opgave 60, fordi den lange linje fik et alternativ til.
          // Mutationen skriver den **nye** lange linje, så den fejler højt den
          // dag endnu et alternativ kommer til i stedet for at ramme en linje der
          // ikke længere findes — eller værre: ramme den del der stadig er der
          // og stå grøn, mens den tabte dækning er usynlig.
          for: "googletagmanager\\.com\\/(?:gtm\\.js|ns\\.html|gtag\\/js)",
          efter: "googletagmanager\\.com\\/(?:gtm\\.js|gtag\\/js)",
        },
      ],
    },
    /*
     * Opgave 60. `gtag/js` lå i ingen alternativ, så en GA4-side hvis config
     * ligger i en aparte fil fik "Third-party trackers: 0 found" — den modsatte
     * fejlretning af opgave 57. Alle tre mutationer er skrevet mod den **lange**
     * linje, så de fejler med "fandt ikke den linje den erstatter" den dag et
     * nyt alternativ kommer til, frem for at stå grønne på en mutation de ikke
     * længere rammer.
     *
     * `gtag\/js\?id=G-` er en mutation der fjerner *mindre*: den rammer stadig
     * den almindeligste GA4-fixture og taber kun Googles Ads-tag. Den er der
     * fordi den er den fejl en "rettelse" faktisk begår — man binder mønsteret
     * til id-præfikset fordi det er det man kan huske — og den fanges kun fordi
     * den anden fixture findes.
     */
    {
      navn: "motoren i repoet taber GA4's gtag/js",
      fil: join(REPO, "shared", "scan-engine.js"),
      forventer: "R2",
      fixture: "GA4's gtag/js-script",
      foer: [
        {
          for: "googletagmanager\\.com\\/(?:gtm\\.js|ns\\.html|gtag\\/js)",
          efter: "googletagmanager\\.com\\/(?:gtm\\.js|ns\\.html)",
        },
      ],
    },
    {
      navn: "den publicerede motor taber GA4's gtag/js",
      fil: join(REPO, "eucomply-scanner", "engine", "index.js"),
      forventer: "R2",
      fixture: "GA4's gtag/js-script",
      foer: [
        {
          for: "googletagmanager\\.com\\/(?:gtm\\.js|ns\\.html|gtag\\/js)",
          efter: "googletagmanager\\.com\\/(?:gtm\\.js|ns\\.html)",
        },
      ],
    },
    {
      navn: "pluginen taber GA4's gtag/js",
      fil: PLUGIN,
      forventer: "R2",
      fixture: "GA4's gtag/js-script",
      foer: [
        {
          for: "googletagmanager\\.com/(?:gtm\\.js|ns\\.html|gtag\\/js)",
          efter: "googletagmanager\\.com/(?:gtm\\.js|ns\\.html)",
        },
      ],
    },
    {
      navn: "motoren i repoet binder gtag/js til id-præfikset G-",
      fil: join(REPO, "shared", "scan-engine.js"),
      forventer: "R2",
      fixture: "Google Ads-tag på gtag/js",
      foer: [
        {
          for: "gtag\\/js)",
          efter: "gtag\\/js\\?id=G-)",
        },
      ],
    },
    {
      navn: "pluginen binder gtag/js til id-præfikset G-",
      fil: PLUGIN,
      forventer: "R2",
      fixture: "Google Ads-tag på gtag/js",
      foer: [
        {
          for: "gtag\\/js)",
          efter: "gtag\\/js\\?id=G-)",
        },
      ],
    },
    {
      navn: "motoren i repoet taber mellerummet i DORA-separatoren",
      fil: join(REPO, "shared", "scan-engine.js"),
      forventer: "R4",
      fixture: "dora i prosa (engelsk, lange former)",
      foer: [
        {
          for: "  { re: /bcdr|bcp[ _-]?plan|dr[ _-]?plan|business[ _-]?continuity/i, name: \"BC/DR planning reference\" },",
          efter: "  { re: /bcdr|bcp[_-]?plan|dr[_-]?plan|business[_-]?continuity/i, name: \"BC/DR planning reference\" }, // mutation: ingen mellemrum",
        },
        {
          for: "  { re: /status[ _-]?page|uptime[ _-]?monitor/i, name: \"Status page / uptime monitoring\" },",
          efter: "  { re: /status[_-]?page|uptime[_-]?monitor/i, name: \"Status page / uptime monitoring\" }, // mutation: ingen mellemrum",
        },
      ],
    },
    {
      navn: "pluginen taber mellerummet i DORA-separatoren",
      fil: PLUGIN,
      forventer: "R4",
      fixture: "dora i prosa (engelsk, lange former)",
      foer: [
        {
          for: "array( 'name' => 'BC/DR planning reference', 're' => '~bcdr|bcp[ _-]?plan|dr[ _-]?plan|business[ _-]?continuity~i' ),",
          efter: "array( 'name' => 'BC/DR planning reference', 're' => '~bcdr|bcp[_-]?plan|dr[_-]?plan|business[_-]?continuity~i' ), // mutation: ingen mellemrum",
        },
      ],
    },
    {
      navn: "den publicerede motor taber mellerummet i DORA-separatoren",
      fil: join(REPO, "eucomply-scanner", "engine", "index.js"),
      forventer: "R4",
      fixture: "dora i prosa (engelsk, lange former)",
      foer: [
        {
          for: "  { re: /bcdr|bcp[ _-]?plan|dr[ _-]?plan|business[ _-]?continuity/i, name: \"BC/DR planning reference\" },",
          efter: "  { re: /bcdr|bcp[_-]?plan|dr[_-]?plan|business[_-]?continuity/i, name: \"BC/DR planning reference\" },",
        },
        {
          for: "  { re: /status[ _-]?page|uptime[ _-]?monitor/i, name: \"Status page / uptime monitoring\" },",
          efter: "  { re: /status[_-]?page|uptime[_-]?monitor/i, name: \"Status page / uptime monitoring\" },",
        },
      ],
    },
    {
      navn: "motoren i repoet holder op med at navngive samtykkeplatformen",
      fil: join(REPO, "shared", "scan-engine.js"),
      forventer: "R3",
      fixture: "Klaro som stylesheet-link",
      foer: [
        {
          for: "${hasConsentPlatform ? `A consent platform was also detected (${consentMatches[0]}).` :",
          efter: "${hasConsentPlatform ? \"A consent platform was also detected.\" :",
        },
      ],
    },
    /*
     * Opgave 61. Pinterests egen dokumentation indlæser tagget fra
     * `s.pinimg.com/ct/core.js` og lægger et `<noscript>`-pixel på
     * `ct.pinterest.com/v3/`. Det gamle mønster kendte ingen af de to — den
     * dokumenterede installation var kun synlig gennem det indlejrede
     * `pintrk(`, altså kun så længe de indlejrede scripts ikke er blevet
     * flyttet ud i en bundle af et samtykketool. Målt før rettelsen: 0 fund i
     * alle tre produkter.
     *
     * De tre første fjerner **begge** nye stier fra én kopi ad gangen. De er
     * skrevet mod den lange linje, så de fejler højt den dag et nyt alternativ
     * kommer til, i stedet for at stå grønne på en mutation de ikke længere
     * rammer. Den fjerde er den realistiske halve rettelse — kun loaderen,
     * ikke pixelet — og den skal være rød på noscript-fixturen. Den femte er
     * den modsatte fejlretning: en bred regel på **værten** rammer Pinterests
     * billed-CDN, så en butik med tre opslagsbilleder får et tracker-fund den
     * aldrig installerede.
     */
    {
      navn: "motoren i repoet taber Pinterests dokumenterede stier",
      fil: join(REPO, "shared", "scan-engine.js"),
      forventer: "R2",
      fixture: "Pinterest-tagens loader",
      foer: [
        {
          for: "s\\.pinimg\\.com\\/ct\\/|ct\\.pinterest\\.com\\/v3\\/|",
          efter: "",
        },
      ],
    },
    {
      navn: "den publicerede motor taber Pinterests dokumenterede stier",
      fil: join(REPO, "eucomply-scanner", "engine", "index.js"),
      forventer: "R2",
      fixture: "Pinterest-tagens loader",
      foer: [
        {
          for: "s\\.pinimg\\.com\\/ct\\/|ct\\.pinterest\\.com\\/v3\\/|",
          efter: "",
        },
      ],
    },
    {
      navn: "pluginen taber Pinterests dokumenterede stier",
      fil: PLUGIN,
      forventer: "R2",
      fixture: "Pinterest-tagens loader",
      foer: [
        {
          for: "s\\.pinimg\\.com/ct/|ct\\.pinterest\\.com/v3/|",
          efter: "",
        },
      ],
    },
    {
      navn: "motoren i repoet retter kun loaderen og taber noscript-pixelet",
      fil: join(REPO, "shared", "scan-engine.js"),
      forventer: "R2",
      fixture: "Pinterest-tagens noscript-pixel",
      foer: [
        {
          for: "s\\.pinimg\\.com\\/ct\\/|ct\\.pinterest\\.com\\/v3\\/|",
          efter: "s\\.pinimg\\.com\\/ct\\/|",
        },
      ],
    },
    {
      navn: "motoren i repoet matcher Pinterests billed-CDN som et tag",
      fil: join(REPO, "shared", "scan-engine.js"),
      forventer: "R1",
      fixture: "Pinterest-billede (CDN, ikke tag)",
      foer: [
        {
          for: "s\\.pinimg\\.com\\/ct\\/|",
          efter: "pinimg\\.com|",
        },
      ],
    },
  ];

  for (const m of MUTATIONER) {
    const original = readFileSync(m.fil, "utf8");
    let mutant = original;
    for (const { for: fra, efter } of m.foer) {
      if (!mutant.includes(fra)) {
        failures.push(`selftest: mutationen «${m.navn}» fandt ikke den linje den erstatter i ${m.fil}: ${fra}`);
        mutant = null;
        break;
      }
      mutant = mutant.replace(fra, efter);
    }
    if (mutant === null) continue;
    writeFileSync(m.fil, mutant);
    let rød = false;
    let grund = "";
    const red = (e) => {
      rød = true;
      if (!grund) grund = e.message;
    };
    const valgtFixture = m.fixture
      ? FIXTURES.find((f) => f.navn === m.fixture)
      : prosa;
    if (!valgtFixture) {
      failures.push(`selftest: mutationen «${m.navn}» har ingen fixture ved navnet «${m.fixture}»`);
      writeFileSync(m.fil, original);
      continue;
    }
    try {
      if (m.fil.endsWith(".php")) {
        const dom = pluginChecks(valgtFixture.html);
        if (m.forventer === "R1") {
          try {
            contractR1([["mutationen", dom]], valgtFixture, PHP_NAVNE);
          } catch (e) {
            red(e);
          }
        } else if (m.forventer === "R2") {
          // R2 på pluginen. Denne gren manglede, og den er præcis derfor
          // pluginen ikke kunne have en egen signatur-mutation: `else` greb
          // alt andet end R1 og kørte **R4** på den, som intet af en
          // tracker-signaturmutation kan gøre rød. Den ville altså have stået
          // grøn og porten ville have løjet om at pluginen er dækket — samme
          // fejlklasse som opgave 58 fund 1, hvor R2 sammenlignede `undefined`
          // med `undefined`. Pluginen er **tredje kopi** af hver signatur, så
          // en rettelse der kun rammer de to JS-motorer er en lækage der ikke
          // kan ses i en diff.
          try {
            contractR2([["mutationen", dom]], valgtFixture, PHP_NAVNE);
          } catch (e) {
            red(e);
          }
        } else {
          try {
            contractR4([["mutationen", dom]], valgtFixture, PHP_NAVNE);
          } catch (e) {
            red(e);
          }
        }
      } else {
        // Query-strengen på importen, fordi ESM cache'r modulerne pr. URL.
        const importPath = `${pathToFileURL(m.fil).href}?mut=${encodeURIComponent(m.navn)}`;
        const mutantScan = (await import(importPath)).runScan;
        if (m.forventer === "R1") {
          try {
            // `m.fixture` skal ændre **hvilken** prosa-prøve der køres. Uden det
            // læste R1-grenen altid `prosa` — altså den danske tekst — så en
            // mutation der gør en *anden* R1-fixture rød blev målt på en
            // fixture den ikke rammer, stod grøn, og porten skrev "mutationen
            // fanges" fordi den aldrig var blevet kørt. Samme fejlklasse som
            // opgave 59 fund 1: et krav der kun ses i den ene retning.
            contractR1([["mutationen", await engineChecks(mutantScan, valgtFixture.html)]], valgtFixture, MOTOR_NAVNE);
          } catch (e) {
            red(e);
          }
        } else if (m.forventer === "R4") {
          // DORA er den eneste gruppe der **skal** læse prosa, så R4 er dens
          // kontrakt. En separator der igen kun matcher bindestreg tager alle
          // de lange engelske markører, og porten skal se det.
          try {
            contractR4([["mutationen", await engineChecks(mutantScan, valgtFixture.html)]], valgtFixture, MOTOR_NAVNE);
          } catch (e) {
            red(e);
          }
        } else if (m.forventer === "R3") {
          // R3 er den eneste kontrakt der sammenligner **alle tre** produkter,
          // så mutationen skal måles i alle tre: den muterede motor, den
          // **urørte** søskermotor og pluginen. Søskeren er den der *ikke* er
          // muteret — at tage `m.fil` selv ville gøre de to motorer ens af
          // mutationen, og R3 ville så teste to kopier af den samfe fejl.
          const soster = ENGINES.find(([, fil]) => fil !== m.fil);
          assert.ok(soster, `mutationen «${m.navn}» rammer begge motorer — der er ingen urørt søsker at sammenligne med`);
          const urort = (await import(pathToFileURL(soster[1]).href)).runScan;
          const domme = [
            ["mutationen", await engineChecks(mutantScan, valgtFixture.html)],
            ["den urørte motor", await engineChecks(urort, valgtFixture.html)],
            ["pluginen", pluginChecks(valgtFixture.html)],
          ];
          try {
            contractR3(domme, MOTOR_NAVNE);
          } catch (e) {
            red(e);
          }
        } else {
          // R1 skal være **grøn** for denne mutation. Det er hele pointen med
          // parret: en for smal beholder rammer ikke prosa, så den kan aldrig
          // findes ved at se på prosa.
          try {
            contractR1([["mutationen", await engineChecks(mutantScan, prosa.html)]], prosa, MOTOR_NAVNE);
          } catch (e) {
            grund = `R1 var rød på en mutation der kun taber attributter — parret kan ikke se forskellen: ${e.message}`;
          }
          for (const fx of (m.fixture ? [valgtFixture] : [wpcf7, klaro])) {
            try {
              contractR2([["mutationen", await engineChecks(mutantScan, fx.html)]], fx, MOTOR_NAVNE);
            } catch (e) {
              red(e);
            }
          }
          // Og pluginen skal se det samme tab, ellers er R2 kun halvt målt.
          try {
            contractR2([["pluginen", pluginChecks(wpcf7.html)]], wpcf7, PHP_NAVNE);
          } catch {
            rød = true;
          }
        }
      }
    } finally {
      writeFileSync(m.fil, original);
    }
    if (rød) {
      caught.push(`mutation: ${m.navn} → ${m.fil.replace(`${REPO}/`, "")} (${m.forventer} rød)`);
    } else {
      failures.push(`selftest: mutationen «${m.navn}» gav en grøn port — ${grund || "mutationen gav ingen fejl"}`);
    }
  }

  if (failures.length) {
    for (const f of failures) console.error(`FEJL  ${f}`);
    process.exit(1);
  }
  console.log(`SELFTEST GRØN — alle negative cases fanges (${caught.length} af ${caught.length})`);
  for (const c of caught) console.log(`  fanget: ${c}`);
}
