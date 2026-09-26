# Et juridisk dokument tæller kun, når siden **linker** det

Opgave 56, 26. september 2026. Plugin **1.3.19**.

## Fejlen, målt

`LEGAL_PATTERNS` er en liste af regexer, og de blev prøvet mod **hele sidens
HTML**. Mønsteret for privatliv er `PRIVACY_LINK_SIGNATURE` — ordene, ikke
linket. Det betyder at en sætning i løbende prosa var et juridisk link.

Fire sider, hver med **én indledning og nul links i foden**:

| Sprog | Falske fund | Mønstre |
|---|---|---|
| DA | **6** | Imprint, Cookie, Shipping, DPA, Acceptable use, Environmental |
| SV | **8** | Privacy, Imprint, Cookie, Returns, Shipping, DPA, Acceptable use, Environmental |
| NL | **7** | Imprint, Cookie, Returns, Shipping, DPA, Acceptable use, Environmental |
| EN | **1** | Privacy (fra `gdpr` i "Read our GDPR documentation") |
| | **22** | |

Den konkrete måling, som opgaven gav mig at starte fra:

> `<p>Wij zijn een subverwerker voor onze hostingpartners en verwerken daar
> persoonsgegevens.</p>` → `Found on page: Privacy / GDPR`

## Hvorfor det er værre end en tabt etiket

`legal` kræver **to** dokumenter for at bestå. Den svenske prosa-side med otte af
slags ord bestod derfor rækken med nul links — en **falsk beståelse** i en rapport,
et bureau betaler $79 om året for. En falsk advarsel kan en kunde se; en falsk
beståelse kan han ikke.

`forms` var værre, fordi den læser *den private note*:

```
<p>Vi behandler persondata i denne formular.</p>   + en <form>
  → "Form(s) found, privacy-policy link detected"   pass = true
```

En kontaktside hvis eneste omtale af privatliv var en sætning, blev **grøn** på
at den linkede sit privatlivslink. Det er det modsatte af opgave 50, som målte en
betalt række der var *svagere* end den gratis scanner: her var den *stærkere* end
sandheden.

## Rettelsen: beholderen, ikke ordene

Mønsterne er **uændrede**. Det er ikke en bredere eller smallere regex, det er et
andet **beholder**: mønsterne prøves mod sidens `<a>`-elementer, ikke mod siden.

```js
function linkAnchors(html) {
  return (html || "").match(/<a\b[^>]*>(?:(?!<\/a>)[\s\S])*/gi) || [];
}
```

Åbnings-tagget med `href` **og** den synlige tekst indeni er begge bevis. Det er
derfor et link der hedder *Privatlivspolitik* med URL'en `/juridisk/` stadig er
noticen, og det er derfor opgave 51s M4-mutation (en "forbedring" der kun læste
`href`) stadig er en fejl.

I pluginen er det `html_links_privacy()`, fordi pluginens `legal` slår
**WordPress-sider** op i stedet for at læse markup — to forskellige
mekanismer, to forskellige rettelser. `find_page_by_title`-vejen fra opgave 53 er
urørt.

### Prisen ved det negative lookahead

`(?:(?!<\/a>)[\s\S])*` stopper ved den næste `</a>`, så ét `<a` kan højst svare
for sit eget indhold. Det er lineært i praksis — mange `<a` giver mange korte
scans — og der er ingen indlejrede kvantisere tilbage at lade en konstrueret side
bruge. PHP-versionen bruger `preg_match_all` på samme mønster og det samme
argument.

## Målingen, begge veje

R1 og R2 er **par**: hver prosa-fixture har en tvilling med de præcis samme
dokumenter som links. Uden parret kan en for bred beskæring bestå R1 og tage
point fra kunden, og det er den vej fejlen kommer tilbage ad.

| | Krav |
|---|---|
| R1 | Prosa i DA, SV, NL, EN giver **nul** fund — ikke ét, nul |
| R2 | De samme dokumenter som **links** er stadig fundet, i alle fire sprog |
| R3 | De to motorer svarer identisk på hver fixture |
| R4 | Pluginen gør det samme, kørt gennem `tools/plugin_probe.php` |
| R5 | `forms` følger samme regel — prosa fejler, link består, i alle tre produkter |

Port: `tools/check_legal_links.mjs`, gate trin 23. **56 tests**, 16 fixtures i
fire sprog. Selftest: **11 negative cases**, heraf **tre mutationer mod
repoets egne filer** — begge motorer og pluginen, hver genskabt til at læse
hele HTML'en igen, som i 1.3.18.

## Fund i min egen port

1. **R1 var grøn af den forkerte grund.** Den læste `.detail` på helt
   `checks`-objektet i stedet for `checks.legal`, så `foundNames` fik `undefined`
   og returnerede nul fund — hvilket er præcis hvad R1 kræver. R2 fandt det,
   fordi R2 kræver fund. Samme fejlklasse som opgave 52 fund 4.
2. **En mutation ramte den forkerte funktion.** Den muterede `linksLegal()`
   (driver `forms`) og krævede R1 (handler om `legal`). To forskellige
   funktioner, så porten var grøn. Nu rører hver motor-mutation **begge**
   steder.
3. **PHP-mutationen sprang over præcis den side den skulle fange.** Den satte
   `$anchor = $html` inde i løkken over fundne anchors — men en prosa-side har
   **intet** `<a>`, så løkken kørte aldrig, og mutationen gav ingen fejl. Den
   indsætter nu hele siden som det ene "anchor", fordi det er 1.3.18's *kodevej*
   mutationen skal genskabe.

## En beslutning 1.3.17 skrev åbent, og som var forkert

1.3.17 sagde i sin changelog:

> It still matches the word wherever it appears, not only inside an href, because
> a link whose text says "Privatlivspolitik" and whose URL says /juridisk/ is
> still the notice.

Det var sandt, og det var grunden til at en sætning i et afsnit var nok. Kravet
er et **link**, og 1.3.17 målte linket og ikke kravet. 1.3.19 siger det samme
åbent, og begge dele tæller stadig: `href` **og** linktekst.

## Hvad porten ikke dækker

`find_page_by_title`-mekanismen fra opgave 53. Den slår WordPress-sider op efter
sti og titel og røres ikke her; dens egen sprogtest er
`tools/check_legal_pages_langs.php` (trin 22).

## Konsekvens for kunder der scannede mellem 1.3.18 og nu

En side der blev bestået på en sætning kan nu blive rapporteret som manglende
sit link. Det er en **falsk beståelse, der bliver fjernet**, ikke en
tilbageføring af en rigtig rettelse — men den er skrevet i changelog'en, fordi en
kunde der ser en ny fejl på en side han mente var i orden skal vide hvorfor.

Se også: `docs/eucomply-privatlivsprog.md` (sprog), `docs/eucomply-juridiske-sprog.md`
(de 18 mønstre), `docs/eucomply-forms-paritet.md` (forms mellem produkterne).
