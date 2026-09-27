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

/**
 * Hvor mange navne hvar signatur-tabel skal have, før porten går videre.
 *
 * `consent` var 21, blev 20 i 1.3.25 da `quantcast[_-]?choice` blev **fjernet**,
 * og er **16** siden 1.3.28, da fire rækker der kun hvilede på en antagelse blev
 * fjernet med dem — CookieScript, CEE/PL (shoper), Moove GDPR og WebToffee.
 * i stedet for rettet, fordi leverandørens egen installationsdokumentation ikke
 * kunne læses fra byggemiljøet, og et mønster skrevet mod en adresse ingen har
 * læst er præcis den fejl der fik den ind. Tallet står her, så den næste agent kan
 * se at 20 er et **valg** og ikke en tilfældighed — og den døde markør kan ikke
 * komme tilbage ved at sænke tallet igen, for den ville give 21.
 */
const MINDST = { trackers: 12, consent: 16, forms: 2, dora: 9 };

/** Navnet på tabellen i de to JS-motorer. `cookies` læser CONSENT_SIGNATURES. */
const MOTOR_TABEL = {
  trackers: "TRACKER_SIGNATURES",
  consent: "CONSENT_SIGNATURES",
  forms: "FORM_PLUGIN_SIGNATURES",
  dora: "DORA_SIGNATURES",
};

/**
 * R5s installationstest, én pr. række i `CONSENT_SIGNATURES`.
 *
 * **Hvorfor den findes:** opgave 63 fjernede en markør, fordi dens mønster
 * aldrig kunne matche det leverandøren faktisk indlæser — punktum og skråstreg
 * mellem to ord. Ingen port kunne se det, fordi porten testede mønstret mod
 * **sit eget navn**. R5 tester derfor mønstret mod en **installationstest**: en
 * rigtig URL eller et rigtigt markup-fragment, aldrig produktnavnet alene.
 * `quantcast_choice` ville tilfredsstille `quantcast[_-]?choice` og skjule
 * præcis den fejl R5 skal finde, så en streng skal indeholde `//`, `.`, `=`
 * eller `<`.
 *
 * **`kilde` er ikke en note — det er bevisstyrken**, og den skal kunne læses af
 * den næste agent uden at tro mig:
 *   `wp.org 200`  — slug'en er verificeret i WordPress' eget plugin-katalog
 *                   (`api.wordpress.org/plugins/info/1.0/<slug>.json` → 200)
 *   `vaert 200`   — leverandørens egen vært svarede 200 i dag
 *   `formodnet`   — **antagelse**. Intet læst, intet svaret. Rækker der kun
 *                   hviler på denne, står i ❓-afsnittet og skal have læst
 *                   leverandørens egen dokumentation, før de regnes som dækning.
 *
 * **Én streng pr. navngiven leverandør, siden opgave 69.** Formen er
 * `[etiket, installation, bevisstyrke]`, og etiketten står der, fordi en streng
 * pr. *række* ikke kan se forskel på fire leverandører: før denne regel lå
 * OneTrusts streng i rækken *Cookiebot / OneTrust / Usercentrics /
 * ConsentManager* under navnet *Cookiebot*, fordi rækken blev talt og ikke
 * læst. `leverandoerer()` læser antallet leverandører **af selve navnet**, så
 * en agent der skriver en ny leverandør ind i et navn får rød i regel (g) med
 * det samme. Leverandører uden installationstest står i `ULAEVNET` med dagens
 * måling — fem af dem — og tallet må kun synke.
 */
const DAEKNING = {
  // Fire leverandører, og **fire** strenge — opgave 69. Før denne regel havde
  // rækken én streng, og den lå på OneTrust, fordi det var det eneste af de fire
  // der var et hul. De fire er målt hver for sig 2026-09-27; ULAEVNET har de
  // fem leverandører der stadig mangler, i de tre andre navngivne rækker.
  "Cookiebot / OneTrust / Usercentrics / ConsentManager":
    [["OneTrust", '<script src="https://cdn.cookielaw.org/scripttemplates/otSDKStub.js" type="text/javascript" charset="UTF-8" data-domain-script="a1b2c3"></script>', "vaert 200 · læst i leverandørens egen stub 2026-09-27"],
     ["Cookiebot", '<script src="https://consent.cookiebot.com/uc.js" data-cbid="a1b2c3" data-consentmode="live"></script>', "vaert 200 2026-09-27"],
     ["Usercentrics", '<script src="https://app.usercentrics.eu/browser-ui/latest/loader.js" data-usercentrics-endpoint="a1b2"></script>', "vaert 200 2026-09-27"],
     ["ConsentManager", '<script src="https://www.consentmanager.de/gtm.js" id="CookieConsent" data-cmpid="a1b2"></script>', "vaert 200 2026-09-27"]],
  "CookieYes":
    [["CookieYes", '<script src="https://cdn-cookieyes.com/client_data/a1b2c3/script.js" data-yesmode="consent"></script>', "wp.org 200 cookie-law-info 2026-09-27 · vaert 403 på et opdigtet id"]],
  // Fire leverandører. Klaro og CookieConsent har strenge, TarteAuCitron og
  // Osano står i ULAEVNET med dagens måling. Klaro's gamle streng pegede på
  // `klaro@1.0.5` — en version der ikke findes (jsdelivr 404, og
  // `data.jsdelivr.com` lister 0.7.21 som nyeste), så påstanden om et 200 var
  // ikke sand. Rettet til den sti leverandørens egen pakke indeholder, læst i
  // jsdelivrs filliste: `/dist/klaro.js`.
  "TarteAuCitron / Klaro / Osano / CookieConsent":
    [["Klaro", '<script src="https://cdn.jsdelivr.net/npm/klaro/dist/klaro.js"></script>', "vaert 200 · filliste læst 2026-09-27"],
     ["CookieConsent", '<script src="https://cdn.jsdelivr.net/npm/cookieconsent@3.1.1/build/cookieconsent.min.js"></script>', "vaert 200 · filliste læst 2026-09-27"]],
  "Complianz GDPR":
    [["Complianz GDPR", "<link rel='stylesheet' id='cmplz-css' href='https://shop.example/wp-content/plugins/complianz-gdpr/assets/css/complianz.min.css'>", "wp.org 200"]],
  "Generic cookie consent banner":
    [["Generic cookie consent banner", "<link rel='stylesheet' id='gdpr-cookie-banner-public-css' href='https://shop.example/wp-content/plugins/gdpr-cookie-banner/public/css/gdpr-cookie-banner-public.css'>", "wp.org 200 gdpr-cookie-banner 2026-09-27 · læst i pluginens eget enqueue"]],
  "Axeptio":
    [["Axeptio", '<script src="https://static.axept.io/sdk.js"></script>', "vaert 200 · læst i leverandørens egen SDK 2026-09-27"]],
  "CookieHub":
    [["CookieHub", '<script src="https://shop.example/wp-content/plugins/cookiehub/includes/js/dcchub-test.js"></script>', "wp.org 200 cookiehub 2026-09-27"]],
  "iubenda":
    [["iubenda", '<script src="https://cdn.iubenda.com/iubenda.js"></script>', "wp.org 200 iubenda-cookie-law-solution 2026-09-27 · vaert 200"]],
  // Tre leverandører. OptinMonster har streng; JustUno og Privy står i
  // ULAEVNET. Før opgave 69 hed etiketten på OptinMonster-strengen "JustUno",
  // fordi porten slet ikke kunne se forskel: den tællede rækker, ikke navne.
  "JustUno / Privy / OptinMonster (popup detected)":
    [["OptinMonster", '<script src="https://shop.example/wp-content/plugins/optinmonster/assets/dist/js/global.min.js"></script>', "wp.org 200 optinmonster 2.17.1 2026-09-27"]],
  "WP Consent API":
    [["WP Consent API", '<script src="https://shop.example/wp-content/plugins/wp-consent-api/assets/js/wp-consent-api.js"></script>', "wp.org 200"]],
  "Borlabs":
    [["Borlabs", '<script>window.BorlabsCookie = window.BorlabsCookie || {}; var BorlabsCookie = window.BorlabsCookie;</script>', "dokumenteret leverandørens egen GTM-template 2026-09-27"]],
  "Real Cookie Banner":
    [["Real Cookie Banner", '<script src="https://shop.example/wp-content/plugins/real-cookie-banner/assets/js/rcb.js"></script>', "wp.org 200"]],
  "Cookie Notice Lite":
    [["Cookie Notice Lite", '<script src="https://shop.example/wp-content/plugins/cookie-notice-lite/cookie-notice-lite.js"></script>', "wp.org 200"]],
  "GDPR Cookie Compliance":
    [["GDPR Cookie Compliance", '<script src="https://shop.example/wp-content/plugins/gdpr-cookie-compliance/gdpr-cookie-compliance.js"></script>', "wp.org 200"]],
  "PixelYourSite (GDPR)":
    [["PixelYourSite", '<script src="https://shop.example/wp-content/plugins/pixelyoursite/pys.js"></script>', "wp.org 200 pixelyoursite 2026-09-27"]],
  "Analytify/CAOS":
    [["Analytify/CAOS", '<script src="https://shop.example/wp-content/plugins/wp-analytify/analytify.js"></script>', "wp.org 200 wp-analytify 2026-09-27"]],
};

/*
 * De tre huller tabellen erklærede, lukket 1.3.29 — hvert ved at læse
 * leverandørens egen kode, målt før rettelsen i alle fire kopier:
 *
 * 1. *Cookiebot / OneTrust / Usercentrics / ConsentManager* — OneTrust var det
 *    eneste af de fire, tabellen ikke kunne finde. **Målt før:** 0 fund på
 *    OneTrusts egen dokumenterede installation, mens Cookiebot,
 *    `app.usercentrics.eu/browser-ui/latest/loader.js` (200) og
 *    `www.consentmanager.de/gtm.js` (200) gav fund i alle fire kopier — altså
 *    3 af de 4 leverandører rækken navngiver. **Læst i leverandørens egen kode:**
 *    `cdn.cookielaw.org/scripttemplates/otSDKStub.js` svarer 200 og **er**
 *    OneTrusts egen SDK-stub — filen definerer `var OneTrustStub`, læser
 *    `window.OneTrust` og bruger OneTrusts `optanon`-felter. Stien rummer
 *    ikke `onetrust`, som den gamle note sagde, så alternativet
 *    `cookielaw\.org|otSDKStub|optanon` er skrevet efter **den markør der står i
 *    markup'en**, og den er læst, ikke gættet. Efter rettelsen: 4 af 4.
 * 2. `gdpr[_-]?banner` matchede ikke slug'en `gdpr-cookie-banner`. **Slug'en
 *    findes:** `api.wordpress.org` svarer 200 — *GDPR Cookie Banner*,
 *    version 1.0.0, 1615 downloads. **Læst i pluginens egen kode:** den
 *    enqueue'r på `wp_enqueue_scripts` (altså i front-end) både
 *    `public/css/gdpr-cookie-banner-public.css` og
 *    `public/js/gdpr-cookie-banner-public.js` via `plugin_dir_url()`, og
 *    bannerens egen markup har klassen `gdpr-cookie-banner`. Mønsteret er derfor
 *    `gdpr[_-]?cookie[_-]?banner|gdpr[_-]?banner` — **ikke** fordi nogen antager
 *    stien, men fordi den står i leverandørens egen kode. Rækkens anden sti,
 *    Cookie-Notices' `cookie-notice.css`, er ligeledes målt fund i alle fire
 *    kopier, så den blev ikke taget med.
 * 3. `cookieninja` er **væk fra mønstret og fra rækkens navn** (1.3.29), som
 *    Quantcast i 1.3.25: hverken `cookieninja` eller `cookie-ninja` findes i
 *    WordPress' eget katalog (404 mod `api.wordpress.org`), og der er intet i
 *    repoet der nogensinde har læst om et produkt ved det navn. En rapport der
 *    siger *Borlabs / CookieNinja* lover kunden en platform, der ikke kan
 *    findes, så rækken hedder nu **Borlabs** — det navn leverandørens egen
 *    GTM-template dokumenterer, og det er stadig 4/4 fund.
 *
 * De øvrige punkter under denne liste står uændrede: fire rækker er fjernet i
 * 1.3.28, fordi ingen af dem findes i WordPress' eget katalog under den slug
 * tabellen brugte (CookieScript, CEE/PL (shoper), Moove GDPR, WebToffee — alle
 * fire slug'e 301'er til en søgeside, mens fire kontrol-slug'e svarer 200 i
 * samme måling), og `analytify` var et dødt mønster indtil 1.3.26, se
 * `docs/eucomply-signatur-prosa.md` "Fejl 9".
 */

/**
 * R5s installationstest, én pr. række i `TRACKER_SIGNATURES` — opgave 65 del 1.
 *
 * Samme krav og samme bevisstyrke som `DAEKNING`, målt 2026-09-27. Rækken
 * *Google Analytics / GTM* har **to** strenge siden opgave 69: GA4s `gtag/js`
 * og GTM's egen `gtm.js`-snippet, som er den installation Googles egen
 * dokumentation beder alle GTM-sites installere. `ns.html` er dækket af
 * samme mønsteralternativer, men efterprøvet i opgave 59's R2-måling.
 *
 * Der er **to** rækker hvor værtens svar ikke er 200, og begge er målt, ikke
 * antaget: TikToks pixel og Matomos CDN svarer **404 på et opdigtet id** — de
 * to værter svarer altså, og netop det er bevist. Claritys `tag/<id>` svarer
 * **204** på et ukendt id, samme sag. En streng der kun kan få 200 med et rigtigt
 * kundenummer ville være ubrugelig i en port, så de tre er skrevet med det svar
 * de faktisk giver.
 *
 * Fire rækker er **ikke** nye fund men opgaver 60-62s arbejde, og deres strenge er
 * de samme stier: GA4 (`googletagmanager.com/gtag/js`), Google tag
 * (`googletagservices.com/tag/js/gpt.js`), TikTok (`analytics.tiktok.com/i18n/`)
 * og Pinterest (`s.pinimg.com/ct/`, `ct.pinterest.com/v3/`). R5 her dokumenterer
 * dem — den fik dem ikke.
 */
const DAEKNING_TRACKERE = {
  "Google Analytics / GTM":
    [["Google Analytics", '<script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC123"></script>', "vaert 200"],
     ["GTM", '<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({"gtm.start":new Date().getTime(),event:"gtm.js"});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!="dataLayer"?"&l="+l:"";j.async=true;j.src="https://www.googletagmanager.com/gtm.js?id="+i+dl;f.parentNode.insertBefore(j,f);})(window,document,"script","dataLayer","GTM-ABC123");</script>', "vaert 404 på et opdigtet id 2026-09-27"]],
  "Meta (Facebook) Pixel":
    [["Meta (Facebook) Pixel", '<script src="https://connect.facebook.net/en_US/fbevents.js"></script>', "vaert 200"]],
  "Hotjar":
    [["Hotjar", '<script src="https://static.hotjar.com/c/hotjar-1234567890.js?sv=6"></script>', "vaert 200"]],
  "Microsoft Clarity":
    [["Microsoft Clarity", '<script src="https://www.clarity.ms/tag/abc123"></script>', "vaert 204 på et ukendt id"]],
  "LinkedIn Insight Tag":
    [["LinkedIn Insight Tag", '<script src="https://snap.licdn.com/li.lms-analytics/insight.min.js"></script>', "vaert 200"]],
  "Snapchat Pixel":
    [["Snapchat Pixel", '<script src="https://sc-static.net/scevent.min.js"></script>', "vaert 200"]],
  "TikTok Pixel":
    [["TikTok Pixel", '<script src="https://analytics.tiktok.com/i18n/pixel/1234567890123.js"></script>', "dokumenteret ads.tiktok.com 2026-09-27 · vaert 404 på et opdigtet id"]],
  "Matomo / Piwik":
    [["Matomo", '<script src="https://cdn.matomo.cloud/abc123/matomo.js"></script>', "vaert 404 på et opdigtet id"],
     ["Piwik", '<script src="https://cdn.matomo.cloud/abc123/piwik.js"></script>', "vaert 404 på et opdigtet id 2026-09-27"]],
  "Plausible":
    [["Plausible", '<script defer data-domain="shop.example" src="https://plausible.io/js/script.js"></script>', "vaert 200"]],
  "Pinterest Tag":
    [["Pinterest Tag", '<script src="https://s.pinimg.com/ct/core.js" data-embed-type="dynamic"></script>', "dokumenteret help.pinterest.com 2026-09-27 · vaert 200"]],
  "Google Ads remarketing":
    [["Google Ads remarketing", '<script src="https://www.googletagservices.com/tag/js/gpt.js"></script>', "vaert 200"]],
  "DoubleClick / AdSense":
    [["AdSense", '<script src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>', "vaert 200"],
     ["DoubleClick", '<script src="https://securepubads.g.doubleclick.net/tag/js/gpt.js"></script>', "vaert 200 2026-09-27"]],
};

/**
 * Hvilket ord en bevisstyrke må starte med.
 *
 * Bevisstyrken er ikke en note — den er det, der gør tabellen læsbar af en agent
 * der ikke stoler på mig. Uden denne regel kan næste agent skrive `testet` og så
 * er R5 grøn på en antagelse, præcis som `quantcast_choice` ville være grøn på
 * en død markør. `formodnet` er bevidst med: en antagelse må kunne stå, men den
 * skal stå som det den er.
 */
const BEVISSTYRKE = ["vaert ", "dokumenteret ", "wp.org ", "formodnet"];

/**
 * Højst antal `formodnet`-strenge i alt — opgave 66, hævet af opgave 67.
 *
 * Opgave 66 satte loftet til **12**, fordi det var det antal `DAEKNING` havde,
 * før de tolv blev læst hos leverandørerne: et loft, ikke et mål, så en ny
 * leverandør ikke kunne tilføjes på en antagelse mens de tolv blev ryddet.
 *
 * Opgave 67 gjorde opgaven færdig, og derfor står der nu **nul**: de fem
 * antagelser blev enten læst i leverandørens egen kode (Borlabs) eller fjernet
 * fra tabellen og alle tre motorer (CookieScript, CEE/PL, Moove, WebToffee) —
 * fordi ingen af dem findes i WordPress' katalog under de slug'e tabellen brugte
 * (alle fire 301'er til en søgeside) og deres egne værter ikke svarer herfra.
 * Se `docs/eucomply-signatur-prosa.md` "Fejl 12".
 *
 * Loftet er derfor ikke længere et loft på et tal, men **kravet fra opgave 63**:
 * en installationstest skal være læst, ellers er den ingen. En agent der tilføjer
 * en række med en antaget adresse får rødt i regel (f) med det samme, i stedet
 * for at skulle huske at sænke et tal.
 */
const HOEJST_FORMODNET = 0;

/**
 * R5s installationstest, én pr. række i `FORM_PLUGIN_SIGNATURES` — opgave 65
 * del 2.
 *
 * Her er installationen **markup**, ikke en URL man kan kopiere, fordi rækkerne
 * navngiver form-plugins og to betalingsplatforme. Bevisstyrkerne er målt
 * 2026-09-27: `api.wordpress.org/plugins/info/1.0/<slug>.json` svarer 200 for
 * `contact-form-7`, `wpforms-lite`, `formidable`, `fluentform`, `ninja-forms`,
 * `elementor` og `woocommerce` — **ikke** for `gravityforms`, fordi Gravity
 * Forms er betalt og derfor ikke i det offentlige katalog. `embed.typeform.com`
 * og `js.stripe.com/v3` svarer begge 200; `checkout.stripe.com` svarer 301.
 *
 * **Fem af de syv strenge er hentet fra leverandørens egen kode, ikke skrevet
 * fra hukommelsen:** WooCommerce-skabelonen `templates/checkout/form-checkout.php`
 * (wordpress.org-svn, 200) skriver `woocommerce-checkout` i sit eget
 * container-element, og den samme kode er grunden til at mønsteret ikke er
 * `wc_checkout` alene. Shopify-markøren er målt på fire rigtige butikkers kurv-
 * og betalingssider (6 sider): `shopify-accelerated-checkout`.
 *
 * Fire ting tabellen **ikke** dækker:
 *
 * 1. Rækken *Contact Form 7 / WPForms / Formidable / Gravity / Fluent /
 *    Elementor* har seks leverandører og **én** streng, som beviser Contact
 *    Form 7 — `<div class="wpcf7">` er den markup CF7 leverer. De øvrige fem er
 *    uafhængigt ubeviste af denne test; deres slugs er verificeret i wp.org,
 *    men ingen af dem har en streng her.
 * 2. Rækken *Typeform / Formspree / Jotform* har tre leverandører og **én**
 *    streng, som beviser Typeforms egen embed. Formspree svarede 403 på
 *    `formspree.io/js/formspree.js` og Jotform 404 på `cdn.jotform.com/embed/`
 *    fra byggemiljøet, så de to står ubeviste.
 * 3. `js.stripe.com/v3` beviser at **Strikes JavaScript er indlæst**, ikke at
 *    en betalingsformular vises. Det er samme opgave som rækken overhovedet har
 *    — dommen kræver formular-markup i de samme bytes (se pluginens kommentar
 *    ved `forms`), så en side der kun indlæser Stripe-JS får et navn, ingen dom.
 * 4. `shopify-accelerated-checkout` er butikkens **accelerated-wallet-knap**,
 *    ikke selve betalingssiden. Den er målt på alle seks sider, men en butik
 *    der har slået den fra fanges ikke. Rækken dækker altså de Shopify-butikker
 *    der har den slået til — det er en delmængde, og det står her.
 */
const DAEKNING_FORMS = {
  // Seks leverandører, seks strenge — opgave 69. Slug'e verificeret i
  // `api.wordpress.org` 2026-09-27: contact-form-7, wpforms-lite, formidable,
  // fluentform, elementor → **200**. `gravityforms` → **404**, fordi Gravity
  // Forms er betalt og derfor ikke i det offentlige katalog; det stod allerede
  // i tabellens kommentar, og mønstret skriver på plugin-mappen, som en
  // betalt plugin også leverer sine assets fra.
  "Contact Form 7 / WPForms / Formidable / Gravity / Fluent / Elementor":
    [["Contact Form 7", '<div class="wpcf7" id="wpcf7-f1234-o1"><form class="wpcf7-form" method="post" action="https://shop.example/contact/"></form></div>', "wp.org 200 (contact-form-7) · markup fra CF7s egen div"],
     ["WPForms", '<script src="https://shop.example/wp-content/plugins/wpforms-lite/assets/js/wpforms.js"></script>', "wp.org 200 wpforms-lite 2026-09-27"],
     ["Formidable", '<script src="https://shop.example/wp-content/plugins/formidable/assets/js/frm_forms.min.js"></script>', "wp.org 200 formidable 2026-09-27"],
     ["Gravity", '<link rel="stylesheet" href="https://shop.example/wp-content/plugins/gravityforms/assets/css/gravityforms.css">', "wp.org 404 gravityforms — betalt plugin, ikke i det offentlige katalog"],
     ["Fluent", '<script src="https://shop.example/wp-content/plugins/fluentform/assets/js/form-submission.js"></script>', "wp.org 200 fluentform 2026-09-27"],
     ["Elementor", '<script src="https://shop.example/wp-content/plugins/elementor/assets/js/forms.js"></script>', "wp.org 200 elementor 2026-09-27"]],
  // Tre leverandører. Jotform står i ULAEVNET. Formspree fik en streng i denne
  // iteration: den svarer **403** på `formspree.io/js/formspree.js`, og en 403
  // er værtens eget svar på en fil der findes — præcis den bevisstyrke
  // consent-tabellen allerede bruger for CookieYes' `cdn-cookieyes.com`.
  "Typeform / Formspree / Jotform":
    [["Typeform", '<script src="https://embed.typeform.com/next/embed.js"></script>', "vaert 200"],
     ["Formspree", '<script src="https://formspree.io/js/formspree.js"></script>', "vaert 403 fra byggemiljøet 2026-09-27"]],
  "WooCommerce Checkout":
    [["WooCommerce Checkout", '<div class="woocommerce-checkout">', "dokumenteret plugins.svn.wordpress.org/woocommerce/trunk/templates/checkout/form-checkout.php 2026-09-27"]],
  "Shopify Checkout":
    [["Shopify Checkout", '<link rel="stylesheet" href="https://cdn.shopify.com/extensions/01a0e1ba/shopify-accelerated-checkout-styles.css">', "dokumenteret 4 butikker, 6 sider målt 2026-09-27"]],
  // To leverandører, to strenge. Den anden er **læst i leverandørens egen
  // fil**: `https://js.stripe.com/v3/` svarer 200, og filen rummer ordet
  // `payment-element` — så Payment Element er ikke en antagelse om hvad
  // Stripe leverer, men noget der står i den kode kunden faktisk indlæser.
  "Stripe Checkout / Payment":
    [["Stripe Checkout", '<script src="https://js.stripe.com/v3/"></script>', "vaert 200"],
     ["Payment", '<div id="payment-element" data-stripe-key="pk_live_a1b2c3"></div>', "vaert 200 · payment-element læst i leverandørens egen v3-fil 2026-09-27"]],
};

/**
 * R5s installationstest, én pr. række i `DORA_SIGNATURES` — opgave 65 del 2.
 *
 * **`dora` er den ene tabel hvor installationstesten *er* prosa**, og det er
 * ikke en lavenage: de ni rækker er **påstande om virksomheden** (SPF, DKIM,
 * DMARC, MX, failover, incident response, BCP, status page), og den eneste
 * sted en sådan påstand står er en virksomheds egen side. R4 (opgave 58)
 * kræver endda at `dora` *kun* læser prosa — en URL ville være modsætningen.
 *
 * Derfor har denne tabel sin **egen** regel (e) i `contractR5` i stedet for
 * kravet om `//`, `.`, `=` eller `<`: en sætning skal have mindst seks ord og
 * mindst to ord der ikke står i rækkens eget navn. Uden den ville
 * `"Status page / uptime monitoring."` være grøn — den har et punktum, så den
 * almindelige regel ville tage den for en installation, mens den er en
 * genindskrivning af navnet. Det er præcis den fejl R5 blev skrevet for.
 *
 * Bevisstyrkerne: ingen af de ni markører er leverandør-URL'er, så der er intet
 * at svare på. De er læst fra **målingen** af de mønstre, de skal finde, og det
 * er derfor alle ni er `dokumenteret` med dagens måling — ikke `vaert 200`, som
 * ville være en løgn om noget der aldrig blev hentet.
 */
const DAEKNING_DORA = {
  "SPF (Email sender auth)":
    [["SPF", "Our sending IPs are published in the SPF record: v=spf1 include:_spf.example.com ~all", "dokumenteret mønstret matcher denne sætning 2026-09-27"]],
  "DKIM (Email signing)":
    [["DKIM", "Add the DKIM public key in DNS as a TXT record named selector1._domainkey.example.com", "dokumenteret mønstret matcher denne sætning 2026-09-27"]],
  "DMARC (Email policy)":
    [["DMARC", "Our DMARC policy is published at _dmarc.example.org with p=reject", "dokumenteret mønstret matcher denne sætning 2026-09-27"]],
  "MX (Mail exchange)":
    [["MX", "Mail is delivered by our MX 1 and MX 2 records in Frankfurt and Amsterdam", "dokumenteret mønstret matcher denne sætning 2026-09-27"]],
  "Multi-server / failover signals":
    [["Multi-server", "Our platform runs on multiple servers with automatic failover between two regions", "dokumenteret mønstret matcher denne sætning 2026-09-27"]],
  "CDN failover / multi-CDN":
    [["CDN failover", "Traffic is served from a multi-CDN setup with a backup origin in a second region", "dokumenteret mønstret matcher denne sætning 2026-09-27"]],
  "Incident response / SOC reporting":
    [["Incident response", "Our incident response plan is tested twice a year and shared with customers under NDA", "dokumenteret mønstret matcher denne sætning 2026-09-27"]],
  "BC/DR planning reference":
    [["BC/DR planning reference", "The business continuity plan is reviewed annually and covers our disaster recovery procedure", "dokumenteret mønstret matcher denne sætning 2026-09-27"]],
  "Status page / uptime monitoring":
    [["Status page", "System status is published on our status page, with uptime monitoring alerts", "dokumenteret mønstret matcher denne sætning 2026-09-27"]],
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

// Den modsatte fejlretning for TikToks værtrettelse. Rettelsen af opgave 62
// skriver `analytics\.tiktok\.com\/`, fordi det er den sti TikToks egen
// hjælpe-side sender folk til i dag — men den naturlige næste bevægelse er at
// skrive hele `tiktok\.com`, og en butik der har indlejret **én** TikTok-video
// i sin"Lookbook" har ikke installeret en pixel. Samme fejlretning som
// Pinterests billed-CDN en linje ovenfor, så den er samme slags fixture: R1
// kræver nul fund, og mutationen nedenfor binder mønsteret til hele værten.
PROSA_FIXTURES.push({
  navn: "TikTok-video indlejret (værten, ikke pixel)",
  lang: "EN",
  slags: "prosa",
  html: side(
    "<h1>Lookbook</h1><p>Se vores efterårskollektion.</p>"
    + '<blockquote class="tiktok-embed" cite="https://www.tiktok.com/@lookbook/video/7418529630"></blockquote>'
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
    // TikToks *nuværende* pixel-sti, fra TikToks egen hjælpe-side
    // ("Install the base code onto your website",
    // ads.tiktok.com/help/article/get-started-pixel, hentet 2026-09-27).
    // Mønsteret kendte kun den ældre `static.tiktok.com/js/` og det indlejrede
    // `ttq.`-kald, så den almindeligste pixel-opsætning gav
    // `Third-party trackers: 0 found` — en grøn række på en side med en
    // tracker. Målt før rettelsen: 0 fund i alle tre produkter.
    navn: "TikToks nuværende pixel-sti", gruppe: "trackers", phpGruppe: "trackers", liste: "trackers",
    forventet: "TikTok Pixel",
    html: side('<script src="https://analytics.tiktok.com/i18n/pixel/C1A2B3C4D5E6F7890.js"></script><p>Hej</p>'),
  },
  {
    // Googles egen Google tag, som er den officielle afløser for
    // `googleadservices.com/pagead/conversion.js` — på **en anden vært**, så
    // hverken AdSensens `googlesyndication` eller det gamle `googleadservices`
    // matcher den. Bevis: `https://www.googletagservices.com/tag/js/gpt.js`
    // svarer 200 fra Googles egen vært 2026-09-27. Målt før rettelsen: 0 fund
    // i alle tre produkter. Den nye alternativstien gør det til *Google Ads
    // remarketing* og ikke til DoubleClick/AdSense, fordi det er Googles egen
    // annoncebibliotek og ikke AdSenses annoncebibliotek.
    navn: "Google tag (gpt.js)", gruppe: "trackers", phpGruppe: "trackers", liste: "trackers",
    forventet: "Google Ads remarketing",
    html: side('<script async src="https://www.googletagservices.com/tag/js/gpt.js"></script><p>Hej</p>'),
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

/**
 * R5: hver række skal have en installationstest, og sit mønster skal kunne finde
 * den — i **alle tre** kopier.
 *
 * Fire røde tilfælde:
 *   (a) rækken mangler en streng i `DAEKNING` — porten ville være grøn uden at
 *       have noget at se på, samme fejl som `MINDST` dækker på den anden side;
 *   (b) strengen findes ikke, fordi mønstret ikke matcher den i en af de tre
 *       kopier — det er præcis opgave 63s Quantcast, målt i stedet for antaget;
 *   (c) en streng peger på et navn der ikke står i tabellen — en installationstest
 *       af ingen tabellenummer er dækning på papiret;
 *   (d) en kopi læser nule rækker, så (b) springer den over. Det er ikke en
 *       hypotetisk fejl: det var denne ports egen PHP-læsning indtil 2026-09-27.
 *       Målt før rettelsen: `consent` 20/20/**0** og `trackers` 12/12/**0**.
 *   (e) kun for tabeller hvor installationstesten er **prosa** (`dora`): sætningen
 *       skal have mindst seks ord og mindst to ord uden for rækkens eget navn.
 *       Uden den ville `"Status page / uptime monitoring."` være grøn, fordi den
 *       har et punktum og dermed klarer kravet om `//`, `.`, `=` eller `<` — den
 *       ville være en genindskrivning af navnet, ikke en installation.
 *
 * Mønstrene læses **fra filerne**, ikke ud fra et navne-array, fordi en regel der
 * kun sammenligner to lister af navne aldrig kan se en mangel i mønsteret — det
 * er opgave 63 fund 2, hvor netop sådan en regel meldte 23 rækker døde og var
 * forkert på den første (`static\.hotjar\.com` kan ikke matche navnet `Hotjar`).
 *
 * @param {Array<Array<{navn: string, re: RegExp}>>} grupper én pr. kopi
 * @param {Object<string, [string, string]>} daekning installationstest pr. række
 * @param {number} mindstRækker hvor mange rækker hver kopi skal læse (regel d)
 * @param {{prosa?: boolean}} [krav] regel (e), kun for prosa-tabeller
 */
/**
 * Blokken efter `'trackers' => array(` i pluginen, med **klammebalance** der
 * respekterer strenge.
 *
 * Den gamle læsning holdt op ved det første `\n]` i filen. PHP-arrayet ender på
 * `\n            ),` — der står **aldrig** et `\n]` i pluginens signaturtabeller —
 * så `indexOf` læste *resten af filen* og den efterfølgende regex, der krævede et
 * `[` foran `'name'`, fandt **0 rækker**. R5 erklærede i sin egen docblock at den
 * læser mønstrene i "alle tre" kopier; den læste to. Målt 2026-09-27:
 * `consent` 20/20/0 og `trackers` 12/12/0. Samme fejlklasse som opgave 30 fund 1,
 * opgave 32 fund 1 og opgave 63 fund 2 — en regel der læser mindre end den påstår.
 */
function phpBlok(kilde, gruppe) {
  const fra = new RegExp(`'${gruppe}'\\s*=>\\s*array\\(`).exec(kilde);
  assert.ok(fra, `kilden har ingen signatur-tabel for «${gruppe}»`);
  const start = fra.index + fra[0].length;
  let dybde = 0;
  for (let i = fra.index + fra[0].length - 1; i < kilde.length; i++) {
    const c = kilde[i];
    if (c === "'") {
      // Spring en PHP-streng over — og dens `\'`-escapes med.
      i++;
      while (i < kilde.length && kilde[i] !== "'") i += kilde[i] === "\\" ? 2 : 1;
      continue;
    }
    if (c === "(") dybde++;
    else if (c === ")" && --dybde === 0) return kilde.slice(start, i);
  }
  throw new Error(`signatur-tabellen for «${gruppe}» har ubalancerede klammer`);
}

function signaturMonstre(kilde, gruppe, php) {
  const blok = php
    ? phpBlok(kilde, gruppe)
    : (() => {
        const fra = new RegExp(`const ${MOTOR_TABEL[gruppe]}\\s*=\\s*\\[`).exec(kilde);
        assert.ok(fra, `kilden har ingen signatur-tabel for «${gruppe}»`);
        const resten = kilde.slice(fra.index);
        const til = resten.indexOf("\n]");
        return til === -1 ? resten : resten.slice(0, til);
      })();
  const par = php
    ? /'name'\s*=>\s*'([^']+)'\s*,\s*'re'\s*=>\s*'~([^~]*)~([a-z]*)/g
    : /re:\s*\/((?:[^/\\]|\\.)*)\/([a-z]*)\s*,\s*name:\s*"([^"]+)"/g;
  return [...blok.matchAll(par)].map((m) => (php
    ? { navn: m[1], re: new RegExp(m[2], m[3]) }
    : { navn: m[3], re: new RegExp(m[1], m[2]) }));
}

/**
 * Leverandørerne i en rækkes navn, læst **af navnet selv**.
 *
 * Et navn med ` / ` imellem opregner flere produkter: *Cookiebot / OneTrust /
 * Usercentrics / ConsentManager* er fire leverandører, og en installationstest
 * for den første siger intet om de tre andre. Det er hele opgave 69: før denne
 * regel havde `DAEKNING` én streng pr. række, så den mest navnerige række i
 * tabellen kunne bevise **én** af sine fire — opgave 68 målte alle fire i samme
 * kørsel, men kun OneTrust kom i tabellen, fordi der var plads til én.
 *
 * Separatoren er ` / ` **med mellemrum på begge sider**, fordi to navne i
 * tabellen bruger en skråstreg uden mellemrum som en del af ét produktnavn:
 * `Analytify/CAOS` er ét plugin (CAOS er dets betalte modul), og `BC/DR` i
 * `dora`-tabellen er to initialer for ét ord. En regel der splittede på enhver
 * `/` ville kræve to installationstester for to navne på ét produkt, og så
 * ville næste agent "løse" det ved at slette den anden test.
 *
 * En afsluttende parentes er ikke en del af leverandørnavnet, så *OptinMonster
 * (popup detected)* er segmentet `OptinMonster`. Samme normalisering på begge
 * sider af regel (g), så etiketten og segmentet kan ikke glide fra hinanden.
 */
function leverandoerer(navn) {
  return navn
    .split(/\s+\/\s+/)
    .map((s) => s.replace(/\s*\([^()]*\)\s*$/, "").trim())
    .filter(Boolean);
}

/**
 * Leverandører i et navn, der står **uden** installationstest — opgave 69.
 *
 * Registeret er begrundet pr. segment, fordi en navngiven leverandør uden bevis
 * ellers er usynlig: porten så én streng og troede den dækkede navnet. En agent
 * der tilføjer en ny leverandør i et navn får derfor rødt i regel (g) med det
 * samme, med mindst to veje ud: læs leverandørens egen kode og skriv strengen,
 * eller skriv her hvorfor den ikke kan læses.
 *
 * Alle fem er **målt** 2026-09-27, ikke antaget:
 *   TarteAuCitron — `api.wordpress.org` svarer **404** på slug'en
 *     `tarteaucitron` (såvel som på `tarteaucitron-cookies`), og pakken findes
 *     ikke på npm. Der er altså ingen kode at læse herfra; kun et produktnavn.
 *   Osano — `cdn.osano.com` svarer **200 på roden**, men **404** på
 *     `cdn.osano.com/js/osano.js`, `cdn.osano.com/v1/cmp/osano.js` og
 *     `static.osano.com/js/osano.min.js`. Værten findes, ingen sti gør.
 *   JustUno — `js.justuno.com` svarer **520** og `widget.justuno.com/script.js`
 *     **520**: værtens egen fejlside, ikke et 404 på en bestemt fil.
 *   Privy — `widget.privy.com` svarer **403** og `static.privy.com/pidget.js` /
 *     `static.privy.com/privy.js` **404**; kun `static.privy.com` roden er 200.
 *   Jotform — `cdn.jotform.com` svarer **200 på roden**, men **404** på
 *     `cdn.jotform.com/embed/`, `…/embed/iframe/frame.html` og
 *     `…/js/embed/v2/embed.js`. Samme billede som Osano.
 *
 * Bemærk hvad der **ikke** står her, fordi det blev målt i samme kørsel:
 * Formspree svarer **403** på `formspree.io/js/formspree.js` — en 403 er
 * værtens eget svar på en fil der findes, præcis som CookieYes' `vaert 403` i
 * den consent-tabel, så Formspree har en streng. Klaro lå med en streng på
 * `klaro@1.0.5`, en version der **ikke findes** (jsdelivr svarer 404, og
 * `data.jsdelivr.com` lister `0.7.21` som nyeste) — altså en påstand om et 200
 * der ikke var sand; rettet til den sti leverandørens egen pakke virkelig
 * indeholder, læst i jsdelivrs filliste.
 */
const ULAEVNET = {
  "TarteAuCitron / Klaro / Osano / CookieConsent": {
    TarteAuCitron: "wp.org 404 (tarteaucitron, tarteaucitron-cookies) · ikke på npm · ingen læsbar kode 2026-09-27",
    Osano: "cdn.osano.com 200 på roden, 404 på alle tre dokumenterede stier 2026-09-27",
  },
  "JustUno / Privy / OptinMonster (popup detected)": {
    JustUno: "js.justuno.com 520, widget.justuno.com/script.js 520 2026-09-27",
    Privy: "widget.privy.com 403, static.privy.com roden 200 men pidget.js/privy.js 404 2026-09-27",
  },
  "Typeform / Formspree / Jotform": {
    Jotform: "cdn.jotform.com 200 på roden, 404 på embed/, embed/iframe/frame.html og js/embed/v2/embed.js 2026-09-27",
  },
};

/**
 * Højst antal leverandører i navne uden installationstest — opgave 69.
 *
 * Loftet er ikke et mål, så **færre** er grønt. Det er en ratchet fordi opgaven
 * netop startede med nul: `DAEKNING` havde én streng pr. række, så tallet af
 * navngivne leverandører uden bevis var ikke bare ukendt — porten kunne ikke
 * se det. Hver ny udfyldning skal skaffe bevis og **sænke** tallet.
 */
const HOEJST_ULAEVNET = 5;

function contractR5(grupper, daekning, mindstRækker, krav = {}) {
  // (d) En kopi porten ikke læser, er en kopi porten ikke dømmer på. Den gamle
  //     PHP-læsning gjorde præcis det, og R5 erklærede i sin egen docblock at
  //     den læser "alle tre" kopier — målt 2026-09-27: consent 20/20/**0**,
  //     trackers 12/12/**0**, altså aldrig ét mønster i den betalte plugin.
  grupper.forEach((rækker, i) => {
    assert.ok(
      rækker.length >= mindstRækker,
      `kopi ${i + 1} af ${grupper.length} læste ${rækker.length} rækker, forventede mindst ${mindstRækker} — ` +
        "en kopi porten ikke læser, kan den heller ikke se en mangel i, så R5 ville være grøn på den"
    );
  });
  // (c) En streng på intet tabellenummer er dækning på papiret.
  for (const navn of Object.keys(daekning)) {
    assert.ok(
      grupper.some((g) => g.some((r) => r.navn === navn)),
      `DAEKNING har en installationstest for «${navn}», som ikke står i nogen signatur-tabel — ` +
        "en streng der peger på ingen række dækker ingen"
    );
  }
  // (f) Ratchetten fra opgave 66. Uden den kunne næste agent tilføje en ny
  //     leverandør med `formodnet` og være grøn, fordi R5 slet ikke kan se
  //     forskellen på en antagelse og et bevis — det er hele pointen med
  //     bevisstyrken. Loftet er et loft, ikke et mål, så **færre** er grønt.
  //     NB: den gamle form var `s[1] === "formodnet"`. Med `[etiket, streng,
  //     bevis]` pr. streng er `s[1]` den **anden streng** i rækken, så
  //     ratchetten talte nul og var grøn på enhver antagelse. Selftesten
  //     "en installationstest der kun er formodet" fandt den.
  const formodnede = Object.entries(daekning)
    .flatMap(([række, strenge]) => strenge
      .map(([, , bevis], i) => (bevis === "formodnet" ? `«${række}»#${i + 1}` : null))
      .filter(Boolean));
  assert.ok(
    formodnede.length <= HOEJST_FORMODNET,
    `DAEKNING har ${formodnede.length} installationstester der kun er ` +
      `«formodnet» — højst ${HOEJST_FORMODNET} er tilladt. Rækker der kun hviler ` +
      `på en antagelse: ${formodnede.map(([n]) => `«${n}»`).join(", ")}`
  );
  for (const rækker of grupper) {
    for (const { navn } of rækker) {
      // (a) Uden streng er porten grøn uden at have noget at se på. En række
      //     med N leverandører i navnet skal have N strenge — regel (g).
      const strenge = daekning[navn];
      assert.ok(
        strenge && strenge.length,
        `signatur-rækken «${navn}» har ingen installationstest i DAEKNING — en række ingen har læst `
          + "et krav på kan hverken bekræfte eller afkræfte sit eget mønster"
      );
      // (g) Én streng pr. navngiven leverandør. En streng der beviser Cookiebot
      //     siger intet om OneTrust, så en række der navngiver fire skal have
      //     fire — ellers kan næste agent skrive en femtende leverandør ind i
      //     navnet uden at læse den, og det er præcis det hullet var.
      if (!krav.prosa) {
        const segmenter = leverandoerer(navn);
        const begrundet = ULAEVNET[navn] || {};
        const ubeviste = segmenter.filter(
          (seg) => !strenge.some(([l]) => l === seg) && !begrundet[seg]
        );
        assert.ok(
          ubeviste.length === 0,
          `signatur-rækken «${navn}» navngiver ${segmenter.length} leverandører `
            + `(${segmenter.join(", ")}) men har ${strenge.length} installationstest`
            + `${strenge.length > 1 ? ` (${strenge.map(([l]) => l).join(", ")})` : ""} — `
            + `ingen installationstest for: ${ubeviste.join(", ")}. Skriv en streng pr. leverandør, `
            + "mærket med leverandørens navn, eller en begrundelse i ULAEVNET hvis den ikke kan læses. "
            + "En streng for den første leverandør siger intet om de andre."
        );
        // En streng skal være for en leverandør der står i navnet — ellers
        // beviser den en leverandør, rapporten ikke nævner.
        for (const [etiket] of strenge) {
          assert.ok(
            segmenter.includes(etiket),
            `installationstesten «${etiket}» i rækken «${navn}» er for en leverandør der ikke står i `
              + `navnet (${segmenter.join(", ")}) — den beviser en leverandør rapporten ikke nævner`
          );
        }
        // To ens strenge er én måling, ikke to: ellers kan fire leverandører
        // "dækkes" af den samme adresse skrevet to gange.
        const unikke = new Set(strenge.map(([, s]) => s));
        assert.ok(
          unikke.size === strenge.length,
          `rækken «${navn}» har ${strenge.length - unikke.size} installationstest(s) der er ens — `
            + "en måling tæller én gang, så den kan ikke bevise to leverandører"
        );
      }
      for (const [etiket, streng, bevis] of strenge) {
        const hvilken = `«${navn}»${strenge.length > 1 ? ` → «${etiket}»` : ""}`;
        // (e) I en prosa-tabel er installationen en sætning fra en virksomheds
        //     side, så kravet er at den læses som en sætning — ikke at den rummer
        //     et tegn, som kun en URL gør. Se `DAEKNING_DORA`.
        if (krav.prosa) {
          const ord = (streng.toLowerCase().match(/[a-z0-9æøåäöéèüç_-]+/g) || []);
          const navneord = new Set(navn.toLowerCase().match(/[a-z0-9æøåäöéèüç_-]+/g) || []);
          const udenfor = ord.filter((o) => !navneord.has(o));
          assert.ok(
            ord.length >= 6 && udenfor.length >= 2,
            `installationstesten for ${hvilken} er «${streng}» — den har ${ord.length} ord og `
              + `${udenfor.length} ord uden for rækkens navn, og en prosa-tabel kræver mindst 6 og 2, `
              + "fordi en genindskrivning af navnet ellers ville være grøn"
          );
        } else {
          assert.ok(
            /(\/\/|[.=<])/.test(streng),
            `installationstesten for ${hvilken} er «${streng}» — den rummer hverken //, ., = eller <, så den `
              + "er skrevet efter mønsterets eget navn og beviser intet"
          );
        }
        assert.ok(
          bevis && BEVISSTYRKE.some((p) => bevis.startsWith(p)),
          `bevisstyrken for ${hvilken} er «${bevis}» — den skal begynne med ${BEVISSTYRKE.join(", ")}, `
            + "for uden den er strengen en antagelse der læser som et bevis"
        );
        // (b) Mønstret skal kunne finde sin egen installationstest, i hver kopi.
        for (const række of grupper) {
          const rækkeMedNavn = række.find((r) => r.navn === navn);
          if (!rækkeMedNavn) continue;
          assert.ok(
            rækkeMedNavn.re.test(streng),
            `mønstret i ${hvilken} kan ikke finde sin egen installationstest «${streng}» — `
              + "denne leverandør er død for den installation rækken er skrevet til (opgave 63)"
          );
        }
      }
    }
  }
  // (h) Registeret tælles her, men valideres i `contractULAEVNET` — det er et
  //     register over **alle fire** tabeller, så en assert her ville løbe for
  //     hver enkelt tabel og bebrejde tracker-tabellen en consent-række.
  const huller = Object.entries(ULAEVNET).flatMap(([n, h]) => Object.keys(h).map((e) => `${n} → ${e}`));
  assert.ok(
    huller.length <= HOEJST_ULAEVNET,
    `ULAEVNET har ${huller.length} navngivne leverandører uden installationstest — højst `
      + `${HOEJST_ULAEVNET} er tilladt, og tallet må kun synke: ${huller.join("; ")}`
  );
}

/**
 * (h) `ULAEVNET` skal være sandt i begge retninger, målt mod **alle fire** tabeller.
 *
 * Registeret er kun værd at have, hvis det ikke kan lyve: en leverandør med en
 * installationstest må ikke stå som ubevist (så fortæller registret en løgn om
 * egen dækning), en begrundelse må ikke pege på en leverandør der ikke står i
 * navnet, og en begrundelse skal være en måling — derfor mindst 20 tegn, så
 * "kan ikke findes" ikke kan bruges som afslutning.
 */
function contractULAEVNET(daekninger, register = ULAEVNET) {
  for (const [navn, huller] of Object.entries(register)) {
    const tabel = Object.entries(daekninger).find(([, d]) => d[navn]);
    assert.ok(
      tabel,
      `ULAEVNET har huller for «${navn}», som ikke står i nogen af de fire tabeller — en begrundet `
        + "undtagelse på intet er en undtagelse, der læser som dækning"
    );
    for (const [etiket, grund] of Object.entries(huller)) {
      assert.ok(
        grund && grund.length > 20,
        `ULAEVNET-begrundelsen for «${navn} → ${etiket}» er «${grund}» — den skal være en måling, `
          + "ikke en vilje. Skriv hvad der blev spurgt om, og hvad værten svarede."
      );
      assert.ok(
        leverandoerer(navn).includes(etiket),
        `ULAEVNET nævner «${etiket}» i «${navn}», men navnet siger `
          + `${leverandoerer(navn).join(", ")} — registret skal pege på en leverandør i navnet`
      );
      assert.ok(
        !(tabel[1][navn] || []).some(([l]) => l === etiket),
        `ULAEVNET siger at «${etiket}» i «${navn}» mangler en installationstest, men den har en — `
          + "fjern hullet, ellers fortæller registret en leverandør er ubevist, mens porten beviser den"
      );
    }
  }
  return Object.values(register).reduce((n, h) => n + Object.keys(h).length, 0);
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

/** R5 læser mønstrene fra de tre filer — se `signaturMonstre`. */
const R5_GRUPPER = [MOTOR_NAVNE, PHP_NAVNE].map((navne) => navne.consent.map((n) => n));
const MOTOR_FILER = [
  [join(REPO, "shared", "scan-engine.js"), false],
  [join(REPO, "eucomply-scanner", "engine", "index.js"), false],
  [PLUGIN, true],
];
const læsMønstre = (gruppe) => MOTOR_FILER.map(([fil, php]) => signaturMonstre(readFileSync(fil, "utf8"), gruppe, php));
const R5_MOENSTRE = læsMønstre("consent");
const R5_TRACKERE = læsMønstre("trackers");
const R5_FORMS = læsMønstre("forms");
const R5_DORA = læsMønstre("dora");

const FIXTURES = [...PROSA_FIXTURES, ...MEKANISME, ...DORA_FIXTURES];

// R5 måler tabellen, ikke fixtures, så den kører **én** gang pr. tabel og ikke
// pr. fixture. De negative cases i selftesten kalder den samme funktion med en
// brudt tabel, så en case der forventer grønt ikke kan blive grøn af en anden
// grund. `mindstRækker` er regel (d): hver kopi skal læse hele tabellen.
await test("R5 hver consent-række har en installationstest", () => contractR5(R5_MOENSTRE, DAEKNING, MINDST.consent));
await test("R5 hver tracker-række har en installationstest", () => contractR5(R5_TRACKERE, DAEKNING_TRACKERE, MINDST.trackers));
await test("R5 hver form-række har en installationstest", () => contractR5(R5_FORMS, DAEKNING_FORMS, MINDST.forms));
await test("R5 hver dora-række har en installationstest", () => contractR5(R5_DORA, DAEKNING_DORA, MINDST.dora, { prosa: true }));
// (h) Registeret dømmes her, så en ny ubevist leverandør uden begrundelse er
//     rød i den kørsel CI ser — ikke først når nogen kører --selftest.
const LEVERANDOERER_I_TABELLERNE = [DAEKNING, DAEKNING_TRACKERE, DAEKNING_FORMS, DAEKNING_DORA]
  .flatMap((d) => Object.values(d)).reduce((n, strenge) => n + strenge.length, 0);
const LEVERANDOERER_NAVNGIVNE = [DAEKNING, DAEKNING_TRACKERE, DAEKNING_FORMS]
  .flatMap((d) => Object.keys(d)).reduce((n, navn) => n + leverandoerer(navn).length, 0);
const ULÆVNET_TAL = Object.values(ULAEVNET).reduce((n, h) => n + Object.keys(h).length, 0);
await test("(h) ULAEVNET er sandt i begge retninger", () =>
  contractULAEVNET({ consent: DAEKNING, trackers: DAEKNING_TRACKERE, forms: DAEKNING_FORMS, dora: DAEKNING_DORA }));

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
    + `${PROSA_FIXTURES.length} prosa-sprog målt, ${MEKANISME.length} mekanismer, 6 kontrakter, 3 produkter, `
    + `${Object.keys(DAEKNING).length + Object.keys(DAEKNING_TRACKERE).length
      + Object.keys(DAEKNING_FORMS).length + Object.keys(DAEKNING_DORA).length} af 46 rækker med installationstest, `
    + `${LEVERANDOERER_I_TABELLERNE} installationstester for ${LEVERANDOERER_NAVNGIVNE} navngivne leverandører, `
    + `${ULÆVNET_TAL} ubeviste i ULAEVNET af højst ${HOEJST_ULAEVNET}`
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

  /**
   * Spejlet af `expectRed`. En regel der kun kan være rød er ikke en regel, den
   * er en fejl — så regel (f) skal kunne bevises **begge** veje: rød ved
   * tretten antagelser, grøn ved præcis tolv.
   */
  const expectGreen = (name, contract, ...args) => {
    try {
      contract(...args);
      caught.push(name);
    } catch (e) {
      failures.push(`selftest: ${name} gav en rød port på en gyldig tabel — ${e.message}`);
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

  // 26. R5 regel (g) — **denne iterations egen fejl**, genskabt præcis som den
  //     var: en række der navngiver fire leverandører med én streng. Før
  //     regel (g) var dette tilstanden i «Cookiebot / OneTrust / Usercentrics /
  //     ConsentManager», og porten var grøn, fordi den tællede *rækker*, ikke
  //     *navne*. Uden denne case ved næste agent ikke om reglen virker.
  const fireSomEn = {
    ...DAEKNING,
    "Cookiebot / OneTrust / Usercentrics / ConsentManager":
      [["OneTrust", '<script src="https://cdn.cookielaw.org/scripttemplates/otSDKStub.js"></script>', "vaert 200"]],
  };
  expectRed("R5 (fire leverandører, én streng)", contractR5, R5_MOENSTRE, fireSomEn, MINDST.consent);

  // 27. R5 regel (g): en streng mærket med en leverandør der ikke står i navnet.
  //     Ellers kan en agent "bevise" en leverandør, rapporten ikke nævner — og
  //     regel (g) ville være tilfreds, fordi der så er lige så mange strenge som
  //     navne, bare uden at de passer sammen.
  const forkertEtiket = {
    ...DAEKNING,
    "Cookiebot / OneTrust / Usercentrics / ConsentManager":
      DAEKNING["Cookiebot / OneTrust / Usercentrics / ConsentManager"].map(
        ([l, s, b]) => [l === "Cookiebot" ? "Cookiebot OG GDPR" : l, s, b]
      ),
  };
  expectRed("R5 (streng for en leverandør uden for navnet)", contractR5, R5_MOENSTRE, forkertEtiket, MINDST.consent);

  // 28. R5 regel (g): fire strenge hvor to er ens. Antallet er rigtigt, så
  //     porten må ikke kunne tælle — en måling er én måling, og ellers kan fire
  //     leverandører "dækkes" af den samme adresse skrevet to gange.
  const toEns = {
    ...DAEKNING,
    "Cookiebot / OneTrust / Usercentrics / ConsentManager":
      DAEKNING["Cookiebot / OneTrust / Usercentrics / ConsentManager"].map(
        ([l, s, b], i) => (i === 1 ? [l, DAEKNING["Cookiebot / OneTrust / Usercentrics / ConsentManager"][0][1], b] : [l, s, b])
      ),
  };
  expectRed("R5 (to leverandører deler én installation)", contractR5, R5_MOENSTRE, toEns, MINDST.consent);

  // 29. R5 regel (g) for **forms**: den række der har flest leverandører i
  //     hele tabellen (seks). Den mutation der sletter **én** af de seks
  //     strenge skal give rød, så en agent der tilføjer en ny form-plugin til
  //     navnet ikke kan gøre det ved at fjerne en anden leverandørs bevis.
  const formsUdenEn = {
    ...DAEKNING_FORMS,
    "Contact Form 7 / WPForms / Formidable / Gravity / Fluent / Elementor":
      DAEKNING_FORMS["Contact Form 7 / WPForms / Formidable / Gravity / Fluent / Elementor"]
        .filter(([l]) => l !== "Fluent"),
  };
  expectRed("R5 (form-række: én af seks leverandører taber sin streng)", contractR5, R5_FORMS, formsUdenEn, MINDST.forms);

  // 30. R5 regel (h): ULAEVNET må ikke sige at en leverandør er ubevist, når
  //     porten beviser den. Registret er ellers et sted, hvor dækning kan
  //     **aftage** i papiret uden at nogen melder det.
  const hulletForEnBevist = {
    "Cookiebot / OneTrust / Usercentrics / ConsentManager": {
      OneTrust: "cdn.cookielaw.org svarer 200, men det er ikke nok — jeg gad ikke se den",
    },
  };
  expectRed("(h) (ULAEVNET kalder en beviset leverandør ubevist)", contractULAEVNET,
    { consent: DAEKNING, trackers: DAEKNING_TRACKERE, forms: DAEKNING_FORMS, dora: DAEKNING_DORA },
    { ...ULAEVNET, "Cookiebot / OneTrust / Usercentrics / ConsentManager": hulletForEnBevist });

  // 31. R5 regel (h): en begrundelse skal være en måling. "Kan ikke findes" er
  //     en vilje, og den er præcis den, der gjorde de tolv antagelser i
  //     opgave 66 mulige at leve med i ni runder.
  const vilje = {
    "TarteAuCitron / Klaro / Osano / CookieConsent": {
      TarteAuCitron: "kan ikke findes",
    },
  };
  expectRed("(h) (ULAEVNET-begrundelsen er ikke en måling)", contractULAEVNET,
    { consent: DAEKNING, trackers: DAEKNING_TRACKERE, forms: DAEKNING_FORMS, dora: DAEKNING_DORA },
    { ...ULAEVNET, "TarteAuCitron / Klaro / Osano / CookieConsent": vilje });

  // 32. Spejlet: de **rigtige** tabeller skal være grønne i (h), ellers er case
  //     30 og 31 grønne fordi porten altid er rød.
  expectGreen("(h) (de fire rigtige tabeller passerer ULAEVNET)", contractULAEVNET,
    { consent: DAEKNING, trackers: DAEKNING_TRACKERE, forms: DAEKNING_FORMS, dora: DAEKNING_DORA }, ULAEVNET);

  // 33. Spejlet af case 26: en agent der skriver en **ny** leverandør ind i et
  //     navn, uden at læse den, får rød. Det er det opgaven forbyder, og før
  //     denne regel var det den eneste vej til en død række i tabellen.
  const nyLeverandørINavnet = {
    ...DAEKNING,
    "Cookiebot / OneTrust / Usercentrics / ConsentManager / En Upfundet Femte":
      DAEKNING["Cookiebot / OneTrust / Usercentrics / ConsentManager"],
  };
  expectRed("R5 (en ny leverandør skrevet ind i navnet uden streng)", contractR5, R5_MOENSTRE, nyLeverandørINavnet, MINDST.consent);

  // 14. R5: en række uden installationstest. Den er grøn i dag kun fordi
  //     `DAEKNING` er skrevet — en ny leverandør kan tilføjes i tabellen uden
  //     streng, og så må porten sige det.
  const udenStreng = { ...DAEKNING };
  delete udenStreng["Axeptio"];
  expectRed("R5 (række uden installationstest)", contractR5, R5_MOENSTRE, udenStreng, MINDST.consent);

  // 15. R5: en streng mønstret ikke matcher — Quantcast-fejlen, som et navne-
  //     array aldrig kunne se. Den er skrevet mod **R5_MOENSTRE's** egen
  //     mønsterkopi, så den er en mutation af de data porten dømmer på, ikke
  //     en syntaktisk død streng i tabellen.
  const boetMønster = R5_MOENSTRE.map((rækker) => rækker.map((r) => (
    r.navn === "Axeptio" ? { navn: r.navn, re: /axepti(?:o)?s\.example/i } : r
  )));
  expectRed("R5 (mønstret finder ikke sin egen installationstest)", contractR5, boetMønster, DAEKNING, MINDST.consent);

  // 16. R5: en streng der peger på et navn der ikke står i nogen tabel. Den er
  //     den fejl der ligner mest en dækning: tabellen siger "testet", og
  //     ingen læser må tro at den testede noget.
  const forvisset = { ...DAEKNING, "En platform der ikke findes": [["En platform der ikke findes", '<script src="https://gone.example/cmp.js"></script>', "formodnet"]] };
  expectRed("R5 (streng på en række der ikke findes)", contractR5, R5_MOENSTRE, forvisset, MINDST.consent);

  // 17. R5: en streng skrevet efter mønstret **navn** i stedet for en
  //     installation. Den består kravet om `//`, `.`, `=` eller `<`, som er
  //     hele pointen: `quantcast_choice` ville tilfredsstille et navne-krav og
  //     skjule præcis den fejl R5 blev skrevet for.
  // Bevisstyrken er `vaert 200` og **ikke** `formodnet`: siden opgave 67 er
  // loftet 0, så en `formodnet`-streng også giver rød i regel (f), og casen
  // ville være rød af to grunde. Den skal rød af præcis sin egen.
  const navnebaseret = { ...DAEKNING, Axeptio: [["Axeptio", "axeptio", "vaert 200"]] };
  expectRed("R5 (strengen er skrevet efter navnet, ikke en installation)", contractR5, R5_MOENSTRE, navnebaseret, MINDST.consent);

  // 18. R5 regel (d): en kopi der læser **nule rækker**. Det er ikke en
  //     hypotetisk fejl — det var portens egen PHP-læsning indtil denne diff,
  //     fordi blokken blev afsluttet på `\n]` som PHP-arrayet aldrig gør. Case
  //     18 genskaber præcis den tilstand med tredje gruppe tømt, så reglen (d)
  //     skal være rød netop sådan som den var grøn i virkeligheden.
  const blindKopi = [R5_MOENSTRE[0], R5_MOENSTRE[1], []];
  expectRed("R5 (en kopi læses ikke)", contractR5, blindKopi, DAEKNING, MINDST.consent);

  // 19. R5 regel om bevisstyrke: en streng hvis anden felt er «testet». Uden
  //     reglen kan næste agent skrive hvad som helst i feltet, og R5 er grøn på
  //     en antagelse der læser som et bevis — den fejl `quantcast_choice` ville
  //     have vædt, hvis den ikke var en død markør.
  const ubevidst = { ...DAEKNING, Axeptio: [["Axeptio", '<script src="https://axeptio.cdn.app/axeptio.js"></script>', "testet"]] };
  expectRed("R5 (bevisstyrken er ikke en af de fire slags)", contractR5, R5_MOENSTRE, ubevidst, MINDST.consent);

  // 25. R5: de to markører opgave 68 tilføjede efter at have læst leverandørens
  //     egen kode. Begge mutationer er skrevet mod **R5_MOENSTRE's** egen
  //     mønsterkopi, så de beviser at strengen i `DAEKNING` ikke kan være
  //     grøn uden den markør den udtrykkeligt blev skrevet for:
  //     (a) OneTrusts `cookielaw\.org|otSDKStub|optanon` — OneTrusts egen
  //         stub-sti rummer ikke `onetrust`, så uden den er den største CMP i
  //         rækkens navn usynlig, og det er præcis det hullet var;
  //     (b) `gdpr[_-]?cookie[_-]?banner` — slug'en står i leverandørens eget
  //         front-end-enqueue, og `gdpr[_-]?banner` kan ikke matche den.
  const udenOneTrust = R5_MOENSTRE.map((rækker) => rækker.map((r) => (
    r.navn === "Cookiebot / OneTrust / Usercentrics / ConsentManager"
      ? { navn: r.navn, re: /cookiebot|consentmanager|onetrust|usercentrics/i } : r
  )));
  expectRed("R5 (OneTrusts leverandør-sti matcher ikke)", contractR5, udenOneTrust, DAEKNING, MINDST.consent);
  const udenSlug = R5_MOENSTRE.map((rækker) => rækker.map((r) => (
    r.navn === "Generic cookie consent banner"
      ? { navn: r.navn, re: /cookie[_-]?notice|gdpr[_-]?banner|eu[_-]?cookie/i } : r
  )));
  expectRed("R5 (slug'en gdpr-cookie-banner matcher ikke)", contractR5, udenSlug, DAEKNING, MINDST.consent);

  // 20. R5 for `forms`: en række uden installationstest. Samme fejl som case 14,
  //     men i den tabel hvor en ny betalingsplatform oftest bliver tilføjet — og
  //     det er den tabel hvor opgave 65 del 2 fandt **to** døde rækker, fordi
  //     ingen havde spørgsmålet "hvad skriver leverandøren faktisk?".
  const formsUden = { ...DAEKNING_FORMS };
  delete formsUden["WooCommerce Checkout"];
  expectRed("R5 (form-række uden installationstest)", contractR5, R5_FORMS, formsUden, MINDST.forms);

  // 21. R5 for `forms`: det mønster, den ene af de to døde rækker havde. Den er
  //     skrevet mod portens **egen** mønsterkopi, så selftesten beviser at
  //     rettelsen ikke var kosmetisk: samme streng, grønt før og rødt nu.
  const shopifySomDenVar = R5_FORMS.map((rækker) => rækker.map((r) => (
    r.navn === "Shopify Checkout" ? { navn: r.navn, re: /shopify[_-]?checkout|checkout[_-]?shopify/i } : r
  )));
  expectRed("R5 (form-række mønstret døde på leverandørens egen markup)", contractR5, shopifySomDenVar, DAEKNING_FORMS, MINDST.forms);

  // 22. R5 for `dora`: en række uden installationstest. Uden den ville porten
  //     være grøn på ni rækker den aldrig har set sætningen fra en virksomheds
  //     side — altså præcis det R5 blev skrevet for.
  const doraUden = { ...DAEKNING_DORA };
  delete doraUden["Status page / uptime monitoring"];
  expectRed("R5 (dora-række uden installationstest)", contractR5, R5_DORA, doraUden, MINDST.dora, { prosa: true });

  // 23. R5 regel (e): en prosa-streng der bare er rækkens navn med et punktum.
  //     Den er valgt fordi den **består** det gamle krav om `//`, `.`, `=` eller
  //     `<` **og** mønsteret — så uden regel (e) ville den være grøn. Det er
  //     dora-tabellen hele problem: en påstand om virksomheden skal læses som
  //     en sætning, ellers er den en genindskrivning af det vi led efter.
  const doraNavnebaseret = { ...DAEKNING_DORA, "Status page / uptime monitoring": [["Status page / uptime monitoring", "Status page / uptime monitoring.", "dokumenteret målt 2026-09-27"]] };
  expectRed("R5 (dora-strengen er navnet igen, ikke en sætning)", contractR5, R5_DORA, doraNavnebaseret, MINDST.dora, { prosa: true });

  // 24. R5 regel (e): en sætning der er for kort til at være en påstand om en
  //     virksomhed. Den matcher mønsteret, så kun ordtællingen kan fange den.
  const doraKort = { ...DAEKNING_DORA, "SPF (Email sender auth)": [["SPF", "SPF record.", "dokumenteret målt 2026-09-27"]] };
  expectRed("R5 (dora-strengen er for kort til at være en installationstest)", contractR5, R5_DORA, doraKort, MINDST.dora, { prosa: true });

  // 25. R5 for `dora`: mønsteret skal kunne finde sætningen, i hver kopi. Det er
  //     den samme fejl som case 15, men i en prosa-tabel — og den er værd at have
  //     fordi `dora` er den tabel hvor en fejlretning giver en **falsk**
  //     række: en DORA-påstand læst i prosa skal give fund, ellers er rapporten
  //     stille om noget kunden har skrevet offentligt.
  const doraBoet = R5_DORA.map((rækker) => rækker.map((r) => (
    r.navn === "DMARC (Email policy)" ? { navn: r.navn, re: /dmarc[ _-]?enforcement/i } : r
  )));
  expectRed("R5 (dora-mønsteret finder ikke sin egen installationstest)", contractR5, doraBoet, DAEKNING_DORA, MINDST.dora, { prosa: true });

  // 25. Ratchetten fra opgave 66, regel (f), hævet af opgave 67 fra 12 til **0**.
  //     Loftet var 12, fordi det var det antal antagelser tabellen havde, før de
  //     tolv blev læst. Opgave 67 ryddede de fem sidste: en blev læst i
  //     leverandørens egen kode, fire blev fjernet, fordi ingen af dem findes i
  //     WordPress' katalog under den slug tabellen brugte. Derfor er der nu ingen
  //     `formodnet`-strenge, og reglen siger det samme som opgave 63s krav: en
  //     installationstest skal være læst, ellers er den ingen.
  //
  //     Den nye række **tilføjes i signatur-tabellen**, så regel (c) ikke kan fyre
  //     først: den findes i tabellen, og dens mønster matcher dens egen streng.
  //     Uden det ville casen være rød af den forkerte grund — præcis den bevægelse
  //     opgaven forbyder, som var tolv strenge i træk.
  const nyLeverandør = { navn: "En ny leverandør", re: /ny-cmp/ };
  const medLeverandør = R5_MOENSTRE.map((g) => [...g, nyLeverandør]);
  const formodnetI = (d) => Object.values(d).filter((s) => s[1] === "formodnet").length;
  assert.strictEqual(
    formodnetI(DAEKNING),
    0,
    "selftestens egen forudsætning: opgave 67 efterlod ingen antagelser, så porten " +
      "kan kræve nul — en frisk antagelse er derfor den første og bliver rød"
  );
  expectGreen("R5 (nul antagelser, som opgave 67 efterlod)", contractR5, R5_MOENSTRE, DAEKNING, MINDST.consent);

  // Den **første** antagelse skal give rød, og den nye række skal findes i
  // signatur-tabellen — ellers fyrer regel (c) først, og casen er så rød af den
  // forkerte grund. Det er præcis den bevægelse opgaven forbyder: at føje en
  // leverandør til på en antagelse.
  const antagelse = { ...DAEKNING, "En ny leverandør": [["En ny leverandør", '<script src="https://ny.example/ny-cmp.js"></script>', "formodnet"]] };
  expectRed("R5 (en installationstest der kun er formodet)", contractR5, medLeverandør, antagelse, MINDST.consent);


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
    // Opgave 62. Alle fire mutationer herunder er skrevet mod den **nye**
    // lange linje, så de fejler med "fandt ikke den linje den erstatter" den
    // dag nye stier kommer til, i stedet for at stå grønne på en mutation de
    // ikke længere rammer.
    navn: "motoren i repoet taber Googles Google tag",
    fil: join(REPO, "shared", "scan-engine.js"),
    forventer: "R2",
    fixture: "Google tag (gpt.js)",
    foer: [
      {
        for: "|googletagservices\\.com\\/tag\\/js\\/gpt\\.js",
        efter: "",
      },
    ],
  },
  {
    navn: "den publicerede motor taber Googles Google tag",
    fil: join(REPO, "eucomply-scanner", "engine", "index.js"),
    forventer: "R2",
    fixture: "Google tag (gpt.js)",
    foer: [
      {
        for: "|googletagservices\\.com\\/tag\\/js\\/gpt\\.js",
        efter: "",
      },
    ],
  },
  {
    navn: "pluginen taber Googles Google tag",
    fil: PLUGIN,
    forventer: "R2",
    fixture: "Google tag (gpt.js)",
    foer: [
      {
        for: "|googletagservices\\.com/tag/js/gpt\\.js",
        efter: "",
      },
    ],
  },
  {
    navn: "motoren i repoet taber TikToks nuværende pixel-sti",
    fil: join(REPO, "shared", "scan-engine.js"),
    forventer: "R2",
    fixture: "TikToks nuværende pixel-sti",
    foer: [
      {
        for: "analytics\\.tiktok\\.com\\/|",
        efter: "",
      },
    ],
  },
  {
    navn: "pluginen taber TikToks nuværende pixel-sti",
    fil: PLUGIN,
    forventer: "R2",
    fixture: "TikToks nuværende pixel-sti",
    foer: [
      {
        for: "analytics\\.tiktok\\.com/|",
        efter: "",
      },
    ],
  },
  {
    // Den brede regel: hele værten i stedet for vært **og** sti. Den fanges af
    // R1 på `www.tiktok.com`-værten, altså af den negative fixture en linje
    // længere oppe. Uden den fixture ville mutationen stå grøn, fordi porten
    // aldrig ville spørge om en indlejret video.
    navn: "motoren i repoet matcher hele TikTok-værten som et pixel",
    fil: join(REPO, "shared", "scan-engine.js"),
    forventer: "R1",
    fixture: "TikTok-video indlejret (værten, ikke pixel)",
    foer: [
      {
        for: "analytics\\.tiktok\\.com\\/|",
        efter: "tiktok\\.com|",
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
