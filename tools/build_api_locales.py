#!/usr/bin/env python3
"""Generér DA/DE/FR-spejlingerne af /api/ ud fra den engelske original.

    python3 tools/build_api_locales.py            # skriv de tre spejlinger
    python3 tools/build_api_locales.py --check    # mål på afdrift mod filerne
    python3 tools/build_api_locales.py --list     # de strenge der mangler en sætning
    python3 tools/build_api_locales.py --selftest # negative cases

Hvorfor et script og ikke tre håndskrevne sider
------------------------------------------------
Iteration 107 gjorde /api/ indekserbar, og målingen i denne iteration viste at
sproget var det næste reelle problem: **191 indekserbare stier, kun 7 af dem på
mere end ét sprog**, og 45 af dem — alle med en købsknap — kun på engelsk. De otte
`vs/*`-sider i iteration 106 var skrevet i hånden og var derfor alle sammen
skrevet forkerte. Tre håndskrevne spejlinger af den bedste udviklerflade er tre
billeder af den samme løgn.

Derfor er `site/api/index.html` den **ene kilde**, og spejlingerne er genereret
fra den: samme `<main>`, samme kodeeksempler, samme felter, kun sproget
skifter. En ny sætning på originalsiden kan ikke glemmes på tre sprog, fordi
den ikke kan skrives ét sted — den kan kun opstå her, og så er spejlingen rød
indtil den er oversat.

To ting røres aldrig i en spejling: `<pre>`-blokke (curl, Python, JSON) og
inline `<code>` (feltnavne, endepunkter, HTTP-metoder). De er kode, ikke prosa,
og en tysk curl-kommando må ikke blive tysk.

`--check` er den egentlige port: den regenererer i hukommelsen og sammenligner
byte for byte med de committede filer. En håndskrevet rettelse i en spejling —
eller en original der er ændret uden at spejlingerne er regenereret — er rød,
ikke en bemærkning i en diff.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SOURCE = SITE / "api" / "index.html"
LOCALES = ("da", "de", "fr")

# Strenge der er ens i alle sprog. HTTP-metoder, endepunktstier, feltnavne og
# enheder er ikke prosa — de skal stå ens i alle fire sprog, ellers er
# kodeeksemplerne på spejlingen ikke længere de samme kald.
KEEP = {
    "GET", "POST", "PASS", "FAIL",
    "/scan", "/stats", "/subscribe", "/config",
    "score", "passed", "total", "pct", "checks", "pass", "warn", "label", "detail", "fix",
    "disclaimer", "url", "platform", "scannedAt", "durationMs", "string", "number", "object",
    "email", "source", "Body", "Status", "Field", "Type", "Ctrl K",
    "10 requests per minute per IP",
    # Produktnavne og skelnemærker, der er ens i alle sprog. `CLI` er navnet på
    # værktøjet, og `Home` er den breadcrumb-label, apply_shell skriver på sit
    # eget sprog. De skal derfor stå ens, ellers dømmer porten sit eget output.
    # `API` er det tredje: produktnavnet **og** breadcrumb-etiketten, som
    # `SEG_LABELS["api"]` skriver som "API" i alle fire sprog. Uden den her ville
    # hver spejling kræve en sætning til et ord der ikke er prosa.
    "CLI", "Home", "API",
}

TITLE_EN = "EU compliance scan API — free, no API key"
DESC_EN = ("Scan any website for GDPR, NIS2, DORA and EAA technical gaps over HTTP. "
           "One GET request, no API key, no sign-up, JSON response. Free and open source.")

# Oversættelsen. Nøglerne er de **nøjagtige** engelske tekstnoder i `<main>`,
# `<title>` og meta-description. Hver sætning skal dække hele sætningen: der
# er ingen delstrengs-oversættelse, fordi den ville ramme kodeeksemplerne.
TRANSLATIONS: dict[str, dict[str, str]] = {
    "da": {
        "takes the same": "tager det samme",
        "field as JSON.": "felt som JSON.",
        "The JSON": "JSON'en",
        "The": "Den",
        "Returns": "Returnerer",
        "EU compliance scan API — free, no API key": "EU-compliance-scan-API — gratis, ingen API-nøgle",
        "Scan any website for GDPR, NIS2, DORA and EAA technical gaps over HTTP. One GET request, no API key, no sign-up, JSON response. Free and open source.":
            "Scan ethvert website for tekniske huller i GDPR, NIS2, DORA og EAA over HTTP. Én GET-anmodning, ingen API-nøgle, ingen tilmelding, JSON-svar. Gratis og open source.",
        "Free scan API": "Gratis scan-API",
        "Free · no API key · no sign-up": "Gratis · ingen API-nøgle · ingen tilmelding",
        "The EU compliance scan": "EU-compliance-scanneren",
        "Send one GET request with a URL, get back nine technical checks for GDPR, NIS2, DORA and EAA as JSON. Any CMS, any stack. No key, no quota to buy, no account.":
            "Send én GET-anmodning med en URL, og få ni tekniske tjek for GDPR, NIS2, DORA og EAA tilbage som JSON. Ethvert CMS, enhver stack. Ingen nøgle, ingen kvota at købe, ingen konto.",
        "Make a request": "Send en anmodning",
        "Try it in the browser": "Prøv det i browseren",
        "One call scans one site": "Ét kald scanner ét site",
        "This is the whole interface. The URL is the only parameter, and it works with or without a scheme.":
            "Det er hele grænsefladen. URL'en er den eneste parameter, og den virker med eller uden skema.",
        "Prefer to send a body, or you need a longer URL than a query string takes?":
            "Foretrækker du at sende en body, eller skal din URL være længere end en query-streng?",
        "In Python, with nothing but the standard library:":
            "I Python, med intet ud over standardbiblioteket:",
        "CORS is open, so this also works straight from a browser — no proxy needed. Verified: a preflight for":
            "CORS er åben, så det også virker direkte fra en browser — ingen proxy nødvendig. Verificeret: en preflight for",
        "returns": "returnerer",
        "What comes back": "Hvad der kommer tilbage",
        "A 200 with one JSON object. Every field, measured against the running service on 28 September 2026:":
            "Et 200-svar med ét JSON-objekt. Alle felter målt mod den kørende tjeneste den 28. september 2026:",
        "What it holds": "Hvad det rummer",
        "The URL as resolved, after redirects.": "URL'en som den blev fundet, efter redirects.",
        "Detected platform, e.g.": "Fundet platform, fx",
        "ISO 8601 timestamp of the scan.": "ISO 8601-tidsstempel for scanningen.",
        "How long the scan took.": "Hvor længe scanningen tog.",
        "over all nine checks.": "over alle ni tjek.",
        "Nine entries, keyed by check id. Each has": "Ni poster, med tjek-id som nøgle. Hver har",
        "Sent with every response. Keep it visible — it is the line that keeps this from being read as legal advice.":
            "Sendes med hvert svar. Lad den stå synlig — det er den linje, der hindrer dette i at blive læst som juridisk rådgivning.",
        "A check that fails is the useful part, so here is one returned verbatim, trimmed to its first three fields:":
            "Et tjek, der fejler, er den nyttige del, så her er ét ordret gengivet og trimmet til de første tre felter:",
        "One honest difference from the CLI": "En ærlig forskel fra CLI'en",
        "divides passed checks by": "deler beståede tjek med",
        "all nine": "alle ni",
        ", including the four that only apply to some sites — cookies, programmatic advertising, Google Ads, DORA. A site that did everything right for its type can still show a middling number.":
            ", inklusive de fire, der kun gælder nogle sites — cookies, programmatisk annoncering, Google Ads, DORA. Et site, der har gjort alt rigtigt for sin type, kan stadig vise et middelmådigt tal.",
        "is the build that splits this, and it tells you which checks it did not count and why. If the number matters more than the JSON shape, run the CLI. This API is currently served by an older build of the same engine than the one in the repository, so it does not return that split yet.":
            "er den udgave, der deler den op, og den fortæller hvilke tjek den ikke talte med og hvorfor. Hvis tallet betyder mere end JSON-formen, så kør CLI'en. Dette API serveres i øjeblikket af en ældre udgave af den samme motor end den i repositoriet, så den returnerer endnu den deling.",
        "The other three endpoints": "De tre andre endepunkter",
        "All of them are unauthenticated and CORS-open, same as": "De er alle uden godkendelse og CORS-åbne, samme som",
        "and the twenty most-scanned hosts. We exclude our own smoke-test domains from the list.":
            "og de tyve mest scannede værter. Vores egne smoke-test-domæner er ikke på listen.",
        "Do not read this as a user count.": "Læs ikke dette som et brugertal.",
        "The counter is incremented by our own automated test runs as well as by visitors — measured 28 September 2026, roughly three quarters of the total came from automated runs against reserved IP addresses. It is a liveness check, not a popularity claim.":
            "Tælleren tælles både af vores egne automatiske testkørsler og af besøgende — målt 28. september 2026 kom cirka tre fjerdedele af det samlede fra automatiske kørsler mod reserverede IP-adresser. Det er en liveness-prøve, ikke et popularitetsbevis.",
        "Stores an email for compliance updates. Body:": "Gemmer en mailadresse til compliance-opdateringer. Body:",
        ", optionally": ", valgfrit",
        "Returns 400 for a malformed address and 422 for a test or disposable domain, so test runs never land in the list.":
            "Returnerer 400 for en ugyldig adresse og 422 for en test- eller engangsadresse, så testkørsler aldrig havner på listen.",
        "Public runtime configuration. The checkout URLs it carries are empty in production, which is deliberate: the site hardcodes the contract links and the payment pages are not driven from a worker variable.":
            "Offentlig runtime-konfiguration. De checkout-URL'er, den indeholder, er tomme i produktion, og det er med vilje: sitet hardkoder kontraktlinks, og betalingssiderne styres ikke fra en worker-variabel.",
        "Limits and errors": "Grænser og fejl",
        "No key, no account, and one limit that matters:": "Ingen nøgle, ingen konto og én grænse der betyder noget:",
        ", counted server-side.": ", talt serverside.",
        "When you get it": "Når du får den",
        "No usable": "Ingen brugbar",
        "parameter": "parameter",
        "Any path other than the four above": "Enhver anden sti end de fire ovenfor",
        "with a test address": "med en testadresse",
        "More than 10 requests in a minute from one IP": "Mere end 10 anmodninger i minuttet fra én IP",
        "The target site could not be read": "Det valgte site kunne ikke læses",
        "A 502 means the site you asked about failed, not that the API did. It carries the underlying message, so read it before retrying — a host behind a bot wall will keep failing, and hammering it will not help.":
            "Et 502 betyder, at det site, du spurgte til, fejlede — ikke at API'et gjorde. Svaret bærer den underliggende besked, så læs den, før du prøver igen — en vært bag en bot-mur fejler hele tiden, og flere forsøg hjælper ikke.",
        "What this API does not do": "Hvad dette API ikke gør",
        "It is a single request for a single site at a single moment. It keeps no history, runs nothing on a schedule, sends no webhooks, and takes no payment. If you need any of those, the current paid product is the WordPress plugin: it re-scans your own site once a day, keeps the last 12 scans, emails you when a check breaks, and generates an HTML report you can send to a client. Hosted monitoring is not part of it.":
            "Det er én anmodning om ét site på ét tidspunkt. Det gemmer ingen historik, kører intet på en tidsplan, sender ingen webhooks og tager ingen betaling. Har du brug for noget af det, er det betalte produkt i dag WordPress-pluginet: det scanner dit eget site én gang om dagen, gemmer de seneste 12 scanninger, sender dig en mail når et tjek brydes, og genererer en HTML-rapport, du kan sende til en kunde. Hosted overvågning er ikke en del af det.",
        "The nine checks are technical signals read from the served HTML. The DORA check looks for public page-text markers and is not an assessment of anything.":
            "De ni tjek er tekniske signaler læst i det serverede HTML. DORA-tjekket læser efter offentlige markører i sidens tekst og er ikke en vurdering af noget som helst.",
        "Need history, scheduling and a report?": "Brug for historik, tidsplan og en rapport?",
        "The API above stays free. Pro is a WordPress plugin licence: daily re-scans in your own WordPress, the last 12 scans on record, an email when a check breaks, and an HTML report from the latest scan. It gets the editable HTML document starters too.":
            "API'et ovenfor forbliver gratis. Pro er en licens til WordPress-pluginet: daglige re-scans i din egen WordPress, de seneste 12 scanninger gemt, en mail når et tjek brydes, og en HTML-rapport fra den seneste scanning. Det giver også adgang til de redigerbare HTML-dokumentstartere.",
        "Buy Pro — $79/year per website →": "Køb Pro — $79/år pr. website →",
    },
    "de": {
        "takes the same": "nimmt dasselbe",
        "field as JSON.": "Feld als JSON.",
        "The JSON": "Das JSON",
        "The": "Die",
        "Returns": "Gibt zurück",
        "EU compliance scan API — free, no API key": "EU-Compliance-Scan-API — kostenlos, ohne API-Schlüssel",
        "Scan any website for GDPR, NIS2, DORA and EAA technical gaps over HTTP. One GET request, no API key, no sign-up, JSON response. Free and open source.":
            "Prüfe jede Website auf technische Lücken bei GDPR, NIS2, DORA und EAA — über HTTP. Ein GET-Request, kein API-Schlüssel, keine Anmeldung, JSON-Antwort. Kostenlos und quelloffen.",
        "Free scan API": "Kostenlose Scan-API",
        "Free · no API key · no sign-up": "Kostenlos · kein API-Schlüssel · keine Anmeldung",
        "The EU compliance scan": "Der EU-Compliance-Scan",
        "Send one GET request with a URL, get back nine technical checks for GDPR, NIS2, DORA and EAA as JSON. Any CMS, any stack. No key, no quota to buy, no account.":
            "Senden Sie einen GET-Request mit einer URL und erhalten Sie neun technische Prüfungen für GDPR, NIS2, DORA und EAA als JSON zurück. Jedes CMS, jeder Stack. Kein Schlüssel, keine zu kaufende Quote, kein Konto.",
        "Make a request": "Request senden",
        "Try it in the browser": "Im Browser ausprobieren",
        "One call scans one site": "Ein Aufruf prüft eine Website",
        "This is the whole interface. The URL is the only parameter, and it works with or without a scheme.":
            "Das ist die gesamte Schnittstelle. Die URL ist der einzige Parameter, und sie funktioniert mit oder ohne Schema.",
        "Prefer to send a body, or you need a longer URL than a query string takes?":
            "Möchten Sie einen Body senden, oder ist Ihre URL länger, als ein Query-String hergibt?",
        "In Python, with nothing but the standard library:": "In Python, mit nichts als der Standardbibliothek:",
        "CORS is open, so this also works straight from a browser — no proxy needed. Verified: a preflight for":
            "CORS ist offen, das funktioniert also direkt aus dem Browser — kein Proxy nötig. Geprüft: ein Preflight für",
        "returns": "liefert",
        "What comes back": "Was zurückkommt",
        "A 200 with one JSON object. Every field, measured against the running service on 28 September 2026:":
            "Eine 200 mit einem JSON-Objekt. Jedes Feld am laufenden Dienst gemessen, am 28. September 2026:",
        "What it holds": "Was es enthält",
        "The URL as resolved, after redirects.": "Die URL, wie sie nach den Weiterleitungen aufgelöst wurde.",
        "Detected platform, e.g.": "Erkannte Plattform, z. B.",
        "ISO 8601 timestamp of the scan.": "ISO-8601-Zeitstempel des Scans.",
        "How long the scan took.": "Wie lange der Scan gedauert hat.",
        "over all nine checks.": "über alle neun Prüfungen.",
        "Nine entries, keyed by check id. Each has": "Neun Einträge, geschlüsselt nach Prüf-ID. Jeder hat",
        "Sent with every response. Keep it visible — it is the line that keeps this from being read as legal advice.":
            "Wird mit jeder Antwort mitgesendet. Lassen Sie sie sichtbar — sie ist die Zeile, die verhindert, dass dies als Rechtsberatung gelesen wird.",
        "A check that fails is the useful part, so here is one returned verbatim, trimmed to its first three fields:":
            "Eine fehlgeschlagene Prüfung ist der nützliche Teil, deshalb hier eine wortgetreu zurückgegebene, auf die ersten drei Felder gekürzt:",
        "One honest difference from the CLI": "Ein ehrlicher Unterschied zur CLI",
        "divides passed checks by": "teilt die bestandenen Prüfungen durch",
        "all nine": "alle neun",
        ", including the four that only apply to some sites — cookies, programmatic advertising, Google Ads, DORA. A site that did everything right for its type can still show a middling number.":
            ", einschließlich der vier, die nur für manche Websites gelten — Cookies, programmatische Werbung, Google Ads, DORA. Eine Website, die für ihren Typ alles richtig gemacht hat, kann trotzdem eine mittelmäßige Zahl zeigen.",
        "is the build that splits this, and it tells you which checks it did not count and why. If the number matters more than the JSON shape, run the CLI. This API is currently served by an older build of the same engine than the one in the repository, so it does not return that split yet.":
            "ist die Version, die das aufteilt, und sie nennt, welche Prüfungen sie nicht mitgezählt hat und warum. Ist Ihnen die Zahl wichtiger als die JSON-Form, nehmen Sie die CLI. Diese API wird derzeit von einer älteren Version derselben Engine ausgeliefert als die im Repository, sie liefert diese Aufteilung also noch nicht.",
        "The other three endpoints": "Die anderen drei Endpunkte",
        "All of them are unauthenticated and CORS-open, same as": "Alle sind ohne Authentifizierung und CORS-offen, genau wie",
        "and the twenty most-scanned hosts. We exclude our own smoke-test domains from the list.":
            "und die zwanzig am häufigsten geprüften Hosts. Unsere eigenen Smoke-Test-Domains stehen nicht auf der Liste.",
        "Do not read this as a user count.": "Lesen Sie das nicht als Nutzerzahl.",
        "The counter is incremented by our own automated test runs as well as by visitors — measured 28 September 2026, roughly three quarters of the total came from automated runs against reserved IP addresses. It is a liveness check, not a popularity claim.":
            "Der Zähler wird sowohl von unseren automatisierten Testläufen als auch von Besuchern hochgezählt — gemessen am 28. September 2026 kamen rund drei Viertel der Summe aus automatisierten Läufen gegen reservierte IP-Adressen. Das ist eine Lebendprüfung, keine Popularitätsaussage.",
        "Stores an email for compliance updates. Body:": "Speichert eine E-Mail-Adresse für Compliance-Updates. Body:",
        ", optionally": ", optional",
        "Returns 400 for a malformed address and 422 for a test or disposable domain, so test runs never land in the list.":
            "Gibt 400 bei einer fehlerhaften Adresse und 422 bei einer Test- oder Wegwerfdomain zurück, sodass Testläufe nie auf der Liste landen.",
        "Public runtime configuration. The checkout URLs it carries are empty in production, which is deliberate: the site hardcodes the contract links and the payment pages are not driven from a worker variable.":
            "Öffentliche Laufzeitkonfiguration. Die enthaltenen Checkout-URLs sind in der Produktion leer, und das ist Absicht: die Website hat die Vertragslinks fest im Code, und die Zahlungsseiten werden nicht aus einer Worker-Variable gesteuert.",
        "Limits and errors": "Grenzen und Fehler",
        "No key, no account, and one limit that matters:": "Kein Schlüssel, kein Konto und ein Grenzwert, der zählt:",
        ", counted server-side.": ", serverseitig gezählt.",
        "When you get it": "Wann Sie ihn bekommen",
        "No usable": "Kein brauchbarer",
        "parameter": "Parameter",
        "Any path other than the four above": "Jeder andere Pfad als die vier oben",
        "with a test address": "mit einer Testadresse",
        "More than 10 requests in a minute from one IP": "Mehr als 10 Requests pro Minute von einer IP",
        "The target site could not be read": "Die geprüfte Website konnte nicht gelesen werden",
        "A 502 means the site you asked about failed, not that the API did. It carries the underlying message, so read it before retrying — a host behind a bot wall will keep failing, and hammering it will not help.":
            "Ein 502 heißt, dass die abgefragte Website fehlgeschlagen ist, nicht die API. Die Antwort enthält die eigentliche Meldung — lesen Sie sie, bevor Sie es erneut versuchen: Ein Host hinter einer Bot-Sperre scheitert dauerhaft, und mehr Versuche helfen nicht.",
        "What this API does not do": "Was diese API nicht tut",
        "It is a single request for a single site at a single moment. It keeps no history, runs nothing on a schedule, sends no webhooks, and takes no payment. If you need any of those, the current paid product is the WordPress plugin: it re-scans your own site once a day, keeps the last 12 scans, emails you when a check breaks, and generates an HTML report you can send to a client. Hosted monitoring is not part of it.":
            "Sie ist ein einzelner Request für eine einzelne Website in einem einzelnen Moment. Sie speichert keine Historie, läuft nicht nach Zeitplan, sendet keine Webhooks und nimmt keine Zahlung an. Brauchen Sie eines davon, ist das kostenpflichtige Produkt derzeit das WordPress-Plugin: Es prüft Ihre eigene Website einmal täglich, behält die letzten 12 Scans, meldet per E-Mail, wenn eine Prüfung bricht, und erzeugt einen HTML-Bericht, den Sie an einen Kunden schicken können. Überwachtes Hosting ist nicht Teil davon.",
        "The nine checks are technical signals read from the served HTML. The DORA check looks for public page-text markers and is not an assessment of anything.":
            "Die neun Prüfungen sind technische Signale aus dem ausgelieferten HTML. Die DORA-Prüfung sucht öffentliche Textmarken und ist keine Bewertung von irgendetwas.",
        "Need history, scheduling and a report?": "Brauchen Sie Historie, Zeitplan und einen Bericht?",
        "The API above stays free. Pro is a WordPress plugin licence: daily re-scans in your own WordPress, the last 12 scans on record, an email when a check breaks, and an HTML report from the latest scan. It gets the editable HTML document starters too.":
            "Die API oben bleibt kostenlos. Pro ist eine Lizenz für das WordPress-Plugin: tägliche Re-Scans in Ihrem eigenen WordPress, die letzten 12 Scans gespeichert, eine E-Mail, wenn eine Prüfung bricht, und ein HTML-Bericht aus dem letzten Scan. Es gibt außerdem Zugriff auf die editierbaren HTML-Dokumentvorlagen.",
        "Buy Pro — $79/year per website →": "Pro kaufen — $79/Jahr pro Website →",
    },
    "fr": {
        "takes the same": "prend le même",
        "field as JSON.": "champ au format JSON.",
        "The JSON": "Le JSON",
        "The": "La",
        "Returns": "Renvoie",
        "EU compliance scan API — free, no API key": "API de scan de conformité UE — gratuite, sans clé API",
        "Scan any website for GDPR, NIS2, DORA and EAA technical gaps over HTTP. One GET request, no API key, no sign-up, JSON response. Free and open source.":
            "Analysez n'importe quel site pour ses failles techniques GDPR, NIS2, DORA et EAA, en HTTP. Une seule requête GET, aucune clé API, aucune inscription, réponse JSON. Gratuite et open source.",
        "Free scan API": "API de scan gratuite",
        "Free · no API key · no sign-up": "Gratuite · sans clé API · sans inscription",
        "The EU compliance scan": "Le scan de conformité UE",
        "Send one GET request with a URL, get back nine technical checks for GDPR, NIS2, DORA and EAA as JSON. Any CMS, any stack. No key, no quota to buy, no account.":
            "Envoyez une seule requête GET avec une URL et recevez neuf contrôles techniques GDPR, NIS2, DORA et EAA au format JSON. N'importe quel CMS, n'importe quelle pile. Aucune clé, aucun quota à acheter, aucun compte.",
        "Make a request": "Envoyer une requête",
        "Try it in the browser": "Essayez dans le navigateur",
        "One call scans one site": "Un appel analyse un site",
        "This is the whole interface. The URL is the only parameter, and it works with or without a scheme.":
            "C'est toute l'interface. L'URL est le seul paramètre, et elle fonctionne avec ou sans schéma.",
        "Prefer to send a body, or you need a longer URL than a query string takes?":
            "Vous préférez envoyer un corps, ou votre URL est plus longue qu'une chaîne de requête ?",
        "In Python, with nothing but the standard library:": "En Python, avec rien d'autre que la bibliothèque standard :",
        "CORS is open, so this also works straight from a browser — no proxy needed. Verified: a preflight for":
            "CORS est ouvert, donc cela fonctionne aussi directement depuis un navigateur — aucun proxy requis. Vérifié : une requête preflight pour",
        "returns": "renvoie",
        "What comes back": "Ce qui revient",
        "A 200 with one JSON object. Every field, measured against the running service on 28 September 2026:":
            "Un 200 avec un seul objet JSON. Chaque champ mesuré sur le service en production le 28 septembre 2026 :",
        "What it holds": "Ce qu'il contient",
        "The URL as resolved, after redirects.": "L'URL telle qu'elle a été résolue, après les redirections.",
        "Detected platform, e.g.": "Plateforme détectée, par ex.",
        "ISO 8601 timestamp of the scan.": "Horodatage ISO 8601 du scan.",
        "How long the scan took.": "Durée du scan.",
        "over all nine checks.": "sur les neuf contrôles.",
        "Nine entries, keyed by check id. Each has": "Neuf entrées, indexées par identifiant de contrôle. Chacune a",
        "Sent with every response. Keep it visible — it is the line that keeps this from being read as legal advice.":
            "Envoyé avec chaque réponse. Laissez-le visible — c'est la ligne qui empêche qu'on y lise un avis juridique.",
        "A check that fails is the useful part, so here is one returned verbatim, trimmed to its first three fields:":
            "Un contrôle qui échoue est la partie utile : en voici un renvoyé mot pour mot, réduit à ses trois premiers champs :",
        "One honest difference from the CLI": "Une différence honnête avec la CLI",
        "divides passed checks by": "divise les contrôles réussis par",
        "all nine": "les neuf",
        ", including the four that only apply to some sites — cookies, programmatic advertising, Google Ads, DORA. A site that did everything right for its type can still show a middling number.":
            ", y compris les quatre qui ne concernent que certains sites — cookies, publicité programmatique, Google Ads, DORA. Un site qui a tout fait correctement pour son type peut afficher un nombre moyen.",
        "is the build that splits this, and it tells you which checks it did not count and why. If the number matters more than the JSON shape, run the CLI. This API is currently served by an older build of the same engine than the one in the repository, so it does not return that split yet.":
            "est la version qui fait cette répartition, et elle indique quels contrôles elle n'a pas comptés et pourquoi. Si le nombre compte plus que la forme du JSON, utilisez la CLI. Cette API est actuellement servie par une version plus ancienne du même moteur que celle du dépôt : elle ne renvoie donc pas encore cette répartition.",
        "The other three endpoints": "Les trois autres points de terminaison",
        "All of them are unauthenticated and CORS-open, same as": "Tous sont sans authentification et CORS ouvert, comme",
        "and the twenty most-scanned hosts. We exclude our own smoke-test domains from the list.":
            "et les vingt hôtes les plus analysés. Nos propres domaines de test ne sont pas dans la liste.",
        "Do not read this as a user count.": "Ne lisez pas cela comme un nombre d'utilisateurs.",
        "The counter is incremented by our own automated test runs as well as by visitors — measured 28 September 2026, roughly three quarters of the total came from automated runs against reserved IP addresses. It is a liveness check, not a popularity claim.":
            "Le compteur est incrémenté par nos propres exécutions de test automatisées autant que par les visiteurs — mesuré le 28 septembre 2026, environ les trois quarts du total venaient d'exécutions automatisées contre des adresses IP réservées. C'est un test de disponibilité, pas une preuve de popularité.",
        "Stores an email for compliance updates. Body:": "Enregistre une adresse e-mail pour les mises à jour de conformité. Corps :",
        ", optionally": ", facultativement",
        "Returns 400 for a malformed address and 422 for a test or disposable domain, so test runs never land in the list.":
            "Renvoie 400 pour une adresse mal formée et 422 pour un domaine de test ou jetable : les exécutions de test n'arrivent donc jamais dans la liste.",
        "Public runtime configuration. The checkout URLs it carries are empty in production, which is deliberate: the site hardcodes the contract links and the payment pages are not driven from a worker variable.":
            "Configuration publique du runtime. Les URL de paiement qu'elle contient sont vides en production, c'est délibéré : le site code les liens du contrat en dur et les pages de paiement ne dépendent pas d'une variable du worker.",
        "Limits and errors": "Limites et erreurs",
        "No key, no account, and one limit that matters:": "Pas de clé, pas de compte, et une limite qui compte :",
        ", counted server-side.": ", comptée côté serveur.",
        "When you get it": "Quand vous l'obtenez",
        "No usable": "Aucun",
        "parameter": "paramètre",
        "Any path other than the four above": "Toute autre route que les quatre ci-dessus",
        "with a test address": "avec une adresse de test",
        "More than 10 requests in a minute from one IP": "Plus de 10 requêtes en une minute depuis une IP",
        "The target site could not be read": "Le site visé n'a pas pu être lu",
        "A 502 means the site you asked about failed, not that the API did. It carries the underlying message, so read it before retrying — a host behind a bot wall will keep failing, and hammering it will not help.":
            "Un 502 signifie que le site interrogé a échoué, pas l'API. La réponse contient le message d'origine : lisez-le avant de réessayer — un hôte derrière un mur anti-bot échouera toujours, et insister n'aide pas.",
        "What this API does not do": "Ce que cette API ne fait pas",
        "It is a single request for a single site at a single moment. It keeps no history, runs nothing on a schedule, sends no webhooks, and takes no payment. If you need any of those, the current paid product is the WordPress plugin: it re-scans your own site once a day, keeps the last 12 scans, emails you when a check breaks, and generates an HTML report you can send to a client. Hosted monitoring is not part of it.":
            "C'est une seule requête pour un seul site à un seul instant. Elle ne garde aucun historique, ne s'exécute pas selon un calendrier, n'envoie aucun webhook et n'accepte aucun paiement. Si vous avez besoin de l'un de ces éléments, le produit payant actuel est l'extension WordPress : elle réanalyse votre propre site une fois par jour, conserve les 12 derniers scans, vous envoie un e-mail quand un contrôle casse, et génère un rapport HTML que vous pouvez envoyer à un client. La supervision hébergée n'en fait pas partie.",
        "The nine checks are technical signals read from the served HTML. The DORA check looks for public page-text markers and is not an assessment of anything.":
            "Les neuf contrôles sont des signaux techniques lus dans le HTML servi. Le contrôle DORA cherche des marqueurs publics dans le texte de la page et n'est aucune évaluation.",
        "Need history, scheduling and a report?": "Besoin d'historique, de planification et d'un rapport ?",
        "The API above stays free. Pro is a WordPress plugin licence: daily re-scans in your own WordPress, the last 12 scans on record, an email when a check breaks, and an HTML report from the latest scan. It gets the editable HTML document starters too.":
            "L'API ci-dessus reste gratuite. Pro est une licence de l'extension WordPress : réanalyses quotidiennes dans votre propre WordPress, les 12 derniers scans conservés, un e-mail quand un contrôle casse, et un rapport HTML du dernier scan. Elle donne aussi accès aux modèles de documents HTML modifiables.",
        "Buy Pro — $79/year per website →": "Acheter Pro — 79 $/an par site →",
    },
}

# Maskér de områder, der ikke er prosa: kodeblokke, scripts, styles og
# JSON-LD. En oversættelse må aldrig røre dem.
MASK = re.compile(
    r"<(pre|code|script|style)\b[^>]*>.*?</\1\s*>", re.S | re.I
)
TEXT_NODE = re.compile(r">([^<>]+)<")
MAIN = re.compile(r"<main\b.*?</main\s*>", re.S)


class Missing(Exception):
    pass


def mask(html: str) -> tuple[str, list[str]]:
    """Erstat hvert kode-stykke med en nummereret pladsholder.

    Pladsholderen er et helt token, ikke et tegn pr. tegn: en tekstnode som
    `The EU compliance scan <code>API</code>.` er to prosa-stumper og en
    kodepladsholder, og kun de to stumper skal have en sætning. Derfor deles
    hver tekstnode op omkring pladsholderne, og kode røres aldrig.
    """
    blocks: list[str] = []

    def keep(m: re.Match[str]) -> str:
        blocks.append(m.group(0))
        return f"\x00{len(blocks) - 1}\x00"

    return MASK.sub(keep, html), blocks


def unmask(html: str, blocks: list[str]) -> str:
    return re.sub(r"\x00(\d+)\x00", lambda m: blocks[int(m.group(1))], html)


def pieces(raw: str) -> list[tuple[str, bool]]:
    """[(tekst, er_kode)] for én rå tekstnode med pladsholdere i."""
    out: list[tuple[str, bool]] = []
    for part in re.split(r"(\x00\d+\x00)", raw):
        if not part:
            continue
        out.append((part, bool(re.fullmatch(r"\x00\d+\x00", part))))
    return out


def texts(html: str) -> list[str]:
    """De tekststumper, der skal have en sætning: alt med bogstaver i."""
    masked, _ = mask(html)
    seen: list[str] = []
    for m in TEXT_NODE.finditer(masked):
        for raw, is_code in pieces(m.group(1)):
            if is_code:
                continue
            node = raw.strip()
            if not node or not re.search(r"[A-Za-z]", node):
                continue
            if node in KEEP or node in seen:
                continue
            seen.append(node)
    return seen


def translate(html: str, table: dict[str, str]) -> tuple[str, list[str]]:
    masked, blocks = mask(html)
    missing: list[str] = []

    def swap(m: re.Match[str]) -> str:
        out = []
        for raw, is_code in pieces(m.group(1)):
            if is_code:
                out.append(raw)
                continue
            node = raw.strip()
            if not node or not re.search(r"[A-Za-z]", node) or node in KEEP:
                out.append(raw)
                continue
            if node not in table:
                missing.append(node)
                return m.group(0)
            lead = raw[: len(raw) - len(raw.lstrip())]
            trail = raw[len(raw.rstrip()) :]
            out.append(lead + table[node] + trail)
        return ">" + "".join(out) + "<"

    return unmask(TEXT_NODE.sub(swap, masked), blocks), missing


def set_head(doc: str, table: dict[str, str]) -> str:
    doc = re.sub(r"<title>.*?</title>",
                 lambda m: "<title>" + table["<title>"] + "</title>", doc, count=1, flags=re.S)
    doc = re.sub(r'(<meta name="description" content=")[^"]*(")',
                 lambda m: m.group(1) + table["<description>"] + m.group(2), doc, count=1)
    return doc


def render(locale: str) -> str:
    doc = SOURCE.read_text(encoding="utf-8")
    m = MAIN.search(doc)
    if not m:
        raise SystemExit(f"FEJL  {SOURCE} har ingen <main>")
    table = dict(TRANSLATIONS[locale])
    table["<title>"] = table[TITLE_EN]
    table["<description>"] = table[DESC_EN]

    body, missing = translate(m.group(0), table)
    if missing:
        raise Missing("\n".join(f"    mangler sætning ({locale}): {s[:90]!r}" for s in missing))
    doc = doc[: m.start()] + body + doc[m.end() :]
    doc = set_head(doc, table)
    # Skal kun have sit eget sprog — apply_shelens process() sætter resten
    # (canonical, hreflang, JSON-LD, og:locale, shell) bagefter.
    doc = re.sub(r'\slang="[^"]*"', ' lang="%s"' % locale, doc, count=1)
    return doc


def apply_shell(paths: list[Path]) -> None:
    """Kør den fælles shell på de nye filer — og kun på dem."""
    shell = load_shell()
    shell.catalogue()
    for p in paths:
        shell.process(p)
    shell.build_sitemap()
    shell.build_search_index()


TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"')


def load_shell():
    spec = importlib.util.spec_from_file_location("apply_shell", ROOT / "tools" / "apply_shell.py")
    shell = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(shell)
    return shell


def expected_files() -> dict[str, str]:
    """De tre spejlinger, som de ser ud efter hele kæden.

    `render()` giver prosa'en, men den fælles shell (`apply_shell.process()`)
    skriver header, breadcrumb, TOC, ids og head-strenge bagefter — og den
    afkorter meta-descriptionen ved en punktumgrænse. En fuld sammenligning af
    filerne kræver derfor at kæden køres igen, så `--check` gør det i en
    midlertidig kopi af `site/` og sammenligner **byte for byte** med de
    committede filer. Det er den eneste måde, en håndskrevet rettelse i en
    spejling kan være rød på.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "site"
        shutil.copytree(SITE, tree)
        shell = load_shell()
        shell.SITE = tree
        shell.PARTIALS = tree / "_partials"
        for locale in LOCALES:
            p = tree / locale / "api" / "index.html"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(render(locale), encoding="utf-8", newline="")
        shell.catalogue()
        for locale in LOCALES:
            shell.process(tree / locale / "api" / "index.html")
        return {
            locale: (tree / locale / "api" / "index.html").read_text(encoding="utf-8")
            for locale in LOCALES
        }


def check() -> int:
    """Mål spejlingerne mod den genererede sætning.

    R1 er fuld byte-identitet efter hele kæden. R2 er, at ingen engelsk
    sætning fra originalen står tilbage i en spejling — den dømmer **retningen
    modsat** R1: en sætning kan være rigtigt oversat og alligevel stå på
    engelsk, fordi en hånd har rettet den.
    """
    failures: list[str] = []
    try:
        expected = expected_files()
    except Missing as exc:
        for locale in LOCALES:
            failures.append(f"{locale}/api/: {exc}")
        return _report(failures)

    english = set(texts(MAIN.search(SOURCE.read_text(encoding="utf-8")).group(0)))
    english |= {TITLE_EN, DESC_EN}
    for locale in LOCALES:
        target = SITE / locale / "api" / "index.html"
        if not target.is_file():
            failures.append(f"{locale}/api/index.html mangler")
            continue
        table = TRANSLATIONS[locale]
        committed = target.read_text(encoding="utf-8")
        if committed != expected[locale]:
            failures.append(
                f"{locale}/api/index.html afviger fra genereringen — originalen "
                f"er ændret uden at spejlingerne er regenereret, eller "
                f"spejlingen er redigeret i hånden"
            )
        masked, _ = mask(committed)
        for m in TEXT_NODE.finditer(masked):
            for raw, is_code in pieces(m.group(1)):
                if is_code:
                    continue
                node = raw.strip()
                # En nøgle hvis oversættelse er sig selv (`parameter` er også
                # det danske ord) er ikke en mangel — den er skrevet med vilje.
                if node in english and node not in KEEP and table.get(node) != node:
                    failures.append(
                        f"{locale}/api/index.html: uoversat engelsk i spejlingen: {node[:70]!r}"
                    )
    return _report(failures)


def _report(failures: list[str]) -> int:
    if failures:
        for f in dict.fromkeys(failures):
            print(f"FEJL  {f}")
        return 1
    print("SPEJLINGER MATCHER — de tre sprog er genereret fra site/api/index.html")
    return 0


def build(check_only: bool = False) -> int:
    if check_only:
        return check()
    written: list[Path] = []
    failures: list[str] = []
    for locale in LOCALES:
        target = SITE / locale / "api" / "index.html"
        try:
            doc = render(locale)
        except Missing as exc:
            failures.append(f"{locale}/api/: {exc}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(doc, encoding="utf-8", newline="")
        written.append(target)
    if failures:
        for f in failures:
            print(f"FEJL  {f}")
        return 1
    apply_shell(written)
    print(f"skrev {len(written)} spejlinger og kørte shellen på dem")
    return 0


def selftest() -> int:
    """Negative cases: mutationer mod repoets egne filer, ikke fixtures."""
    src = SOURCE.read_text(encoding="utf-8")
    out = SITE / "da" / "api" / "index.html"
    da = out.read_text(encoding="utf-8")
    body = MAIN.search(src)
    cases = [
        # 1. en uoversat sætning i originalen → render() skal nævne den
        ("uoversat sætning i originalen",
         lambda: _expect_missing(src.replace("Make a request", "Send a request!"))),
        # 2. en håndskrevet rettelse i spejlingen → --check skal være rød
        ("håndskrevet rettelse i spejlingen", lambda: _expect_drift()),
        # 3. en kodeblok må aldrig oversættes
        ("kodeeksemplet er ikke rørt", lambda: _expect_verbatim(src, da)),
        # 4. en tekstnode skal kunne findes i tabellen for alle tre sprog
        ("dækning i alle tre sprog", lambda: _expect_coverage(src)),
    ]
    bad = 0
    for name, fn in cases:
        try:
            fn()
        except AssertionError as exc:
            bad += 1
            print(f"FEJL  selftest: {name}: {exc}")
        else:
            print(f"OK    selftest: {name}")
    if bad:
        print(f"SELFTEST RØD — {bad} af {len(cases)} negative cases fanges ikke")
        return 1
    print(f"SELFTEST GRØN — alle {len(cases)} negative cases fanges")
    return 0


def _expect_missing(src: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        global SOURCE
        keep, SOURCE = SOURCE, Path(tmp) / "index.html"
        SOURCE.parent.mkdir(parents=True, exist_ok=True)
        SOURCE.write_text(src, encoding="utf-8", newline="")
        try:
            render("da")
        except Missing as exc:
            assert "Send a request!" in str(exc), exc
        else:
            raise AssertionError("render() oversatte en sætning, der ikke står i tabellen")
        finally:
            SOURCE = keep


def _expect_drift() -> None:
    keep = out_bytes(SITE / "da" / "api" / "index.html")
    try:
        p = SITE / "da" / "api" / "index.html"
        p.write_text(p.read_text(encoding="utf-8").replace("Køb Pro", "Køb pro", 1), encoding="utf-8", newline="")
        if check() == 0:
            raise AssertionError("--check var grøn på en håndskrevet spejling")
    finally:
        p = SITE / "da" / "api" / "index.html"
        p.write_bytes(keep)


def _expect_verbatim(src: str, da: str) -> None:
    """Kodeeksemplerne skal stå tegn for tegn som i originalen.

    Kun `<main>` tages med: apply_shell skriver selv en `<style>`-blok i hvert
    hoved, og den er ikke noget spejlingen har oversat — den er bare ikke
    originalens CSS mere.
    """
    def blocks(doc: str) -> list[str]:
        body = MAIN.search(doc)
        assert body, "siden har ingen <main>"
        return [m.group(0) for m in re.finditer(r"<(pre|code)\b[^>]*>.*?</\1\s*>", body.group(0), re.S)]

    want = blocks(src)
    assert want, "originalen har ingen kode-eksempler at holde fast"
    got = blocks(da)
    for block in want:
        assert block in got, f"kode fra originalen mangler i spejlingen: {block[:70]!r}"


def _expect_coverage(src: str) -> None:
    body = MAIN.search(src)
    assert body, "kilden har ingen <main>"
    for locale in LOCALES:
        table = TRANSLATIONS[locale]
        for node in texts(body.group(0)):
            assert node in KEEP or node in table, f"{locale}: {node[:70]!r}"
        for key in (TITLE_EN, DESC_EN):
            assert key in table, f"{locale}: head-streng {key[:50]!r}"


def out_bytes(p: Path) -> bytes:
    return p.read_bytes()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.list:
        body = MAIN.search(SOURCE.read_text(encoding="utf-8"))
        if not body:
            print("FEJL  kilden har ingen <main>")
            return 1
        for node in texts(body.group(0)) + [TITLE_EN, DESC_EN]:
            print(repr(node))
        return 0
    return build(check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
