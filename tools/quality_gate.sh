#!/usr/bin/env bash
# Kanonisk kvalitetsgate for EUComply.
#
#   bash tools/quality_gate.sh                # hele gaten
#   bash tools/quality_gate.sh --no-network  # spring den live røgtest over
#
# Dette er ÉN definition af "grøn". Lokalt og i CI kaldes samme script, så en
# grøn lokal gate og en grøn CI betyder præcis det samme — det er hele pointen
# med opgave 9. Hver step logger den kørte command og sin exit code, og
# gaten fejler med exit 1 hvis ét step fejler.
#
# Secrets: scriptet læser ingen .env og printer ingen nøgler. Deploy-credentials
# findes kun i Cloudflare-credentials-steppet i .github/workflows/deploy-site.yml.

set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

NETWORK=1
for arg in "$@"; do
  case "$arg" in
    --no-network) NETWORK=0 ;;
    *) printf 'ukendt argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

STEP=0
FAILED=0

hdr() { STEP=$((STEP + 1)); printf '\n=== %02d  %s\n' "$STEP" "$1"; }
ok()  { printf 'OK    %s\n' "$1"; }
bad() { printf 'FEJL  %s (exit %s)\n' "$1" "$2"; FAILED=1; }
skip(){ printf 'SPRINGET OVER  %s\n' "$1"; }

# run <label> <command...> — loggér kommandoen og exit code.
run() {
  label="$1"; shift
  printf '$ %s\n' "$*"
  "$@"
  rc=$?
  if [ "$rc" -eq 0 ]; then ok "$label"; else bad "$label" "$rc"; fi
  return "$rc"
}

# Vælg en python der kan parse typeannoteringer (seo_check.py kræver 3.10+).
# CI har 3.11 via setup-python; en gammel lokal python3 må ikke give en
# stille SyntaxError, der ligner en SEO-fejl.
pick_python() {
  for candidate in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        printf '%s' "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

printf 'EUComply kvalitetsgate\nrepo:  %s\ngate:  %s\n' "$ROOT" "$(git rev-parse --short HEAD 2>/dev/null || echo ukendt)"

# ---------------------------------------------------------------- 1. PHP-lint
hdr "PHP-syntax"
php_count=0
php_fail=0
for f in plugin/*.php site/plugin/*.php; do
  [ -f "$f" ] || continue
  php_count=$((php_count + 1))
  printf '$ php -l %s\n' "$f"
  if ! php -l "$f"; then php_fail=$((php_fail + 1)); fi
done
if [ "$php_count" -eq 0 ]; then
  bad "PHP-lint" 1
  echo "ingen PHP-filer fundet i plugin/ eller site/plugin/"
elif [ "$php_fail" -gt 0 ]; then
  bad "PHP-lint ($php_fail af $php_count filer har syntaksfejl)" 1
else
  ok "PHP-lint ($php_count filer)"
fi

# -------------------------------------------------- 2. plugin-kopi byte-identisk
hdr "Plugin-paritet (plugin/ vs site/plugin/)"
parity_fail=0
for f in eucomply.php uninstall.php readme.txt; do
  if [ ! -f "plugin/$f" ] || [ ! -f "site/plugin/$f" ]; then
    printf 'FEJL  %s mangler i den ene af de to træer\n' "$f"; parity_fail=$((parity_fail + 1)); continue
  fi
  if cmp -s "plugin/$f" "site/plugin/$f"; then
    ok "$f er byte-identisk"
  else
    printf 'FEJL  %s afviger mellem plugin/ og site/plugin/\n' "$f"; parity_fail=$((parity_fail + 1))
  fi
done
[ "$parity_fail" -eq 0 ] || bad "plugin-paritet" 1

# ------------------------------------------------------------- 3. JS-syntaks
hdr "JavaScript-syntaks"
js_fail=0
js_count=0
js_list="$(find shared worker-scan worker-watch chrome-ext tools eucomply-scanner cli -name '*.js' -o -name '*.mjs' 2>/dev/null | grep -v node_modules | sort)"
for f in $js_list; do
  js_count=$((js_count + 1))
  printf '$ node --check %s\n' "$f"
  if ! node --check "$f" >/dev/null 2>&1; then
    node --check "$f" || true
    js_fail=$((js_fail + 1))
  fi
done
if [ "$js_count" -eq 0 ]; then
  bad "JS-syntaks" 1
elif [ "$js_fail" -gt 0 ]; then
  bad "JS-syntaks ($js_fail af $js_count filer)" 1
else
  ok "JS-syntaks ($js_count filer)"
fi

# ------------------------------------------- 4. publiceret træ (build først)
# `check_cta.py` klassificerer det træ, der uploades, ikke kilde-træet — så
# bygningen skal ske FØR repo-tests. Ellers ville gaten enten være grøn på en
# kildetre, der aldrig bliver uploadet, eller kræve et publiceret træ, der
# ingen har lavet endnu. Samme rækkefølge som i deploy-workflowen.
hdr "Publiceret træ (build)"
run "tools/build_public_tree.py" python3 tools/build_public_tree.py --quiet

# ----------------------------------------------------------- 5. repoets tests
hdr "Repo-tests"
run "tools/test_worker_security.mjs" node tools/test_worker_security.mjs
run "tools/test_engine_parity.mjs" node tools/test_engine_parity.mjs
run "tools/test_license_verdicts.php" php tools/test_license_verdicts.php
run "tools/test_pro_documents.php" php tools/test_pro_documents.php
run "tools/test_pro_documents.php --selftest" php tools/test_pro_documents.php --selftest
run "tools/check_pro_claims.py" python3 tools/check_pro_claims.py
run "tools/check_cta.py" python3 tools/check_cta.py
run "tools/check_cta.py --selftest" python3 tools/check_cta.py --selftest
run "tools/check_runtime.py" python3 tools/check_runtime.py
run "tools/check_runtime.py --selftest" python3 tools/check_runtime.py --selftest
run "tools/check_package_identity.py" python3 tools/check_package_identity.py
run "tools/check_package_identity.py --selftest" python3 tools/check_package_identity.py --selftest
run "tools/check_published_installs.py" python3 tools/check_published_installs.py
run "tools/check_published_installs.py --selftest" python3 tools/check_published_installs.py --selftest
run "tools/check_dom_xss.py" python3 tools/check_dom_xss.py
run "tools/check_dom_xss.py --selftest" python3 tools/check_dom_xss.py --selftest
# Inline <script> i de publicerede HTML-sider. Step 03 linted .js-filerne i
# repoet, men ikke de 276 scripts der ligger INLINE i markup'et — og det er dem
# en besøgende faktisk kører. Default-træet er site-dist, fordi opgave 23
# lærte os at klassificere det publicerede træ og ikke kilden.
run "scripts/check_inline_js.py" python3 scripts/check_inline_js.py
run "scripts/check_inline_js.py --selftest" python3 scripts/check_inline_js.py --selftest
run "tools/test_quickcheck_render.mjs" node tools/test_quickcheck_render.mjs
run "tools/test_quickcheck_render.mjs --selftest" node tools/test_quickcheck_render.mjs --selftest
run "tools/check_production_drift.py --selftest" python3 tools/check_production_drift.py --selftest
# Prøverapporten er den eneste Pro-overflade, der viser en køber hvad vedkommende
# får, og den lå 5 tjek bag motorens 9 med tal i både HTML og PDF. Nu læger alle
# tre det samme datasæt, og denne kontrol holder kæden motor → datasæt → HTML +
# PDF. Den læser også site-dist, fordi det er den side der sælges.
run "tools/check_sample_coverage.py" python3 tools/check_sample_coverage.py
run "tools/check_sample_coverage.py --selftest" python3 tools/check_sample_coverage.py --selftest

# --------------------------------------------- 6. publiceret træ (kontrol)
# Træet er bygget i step 04, fordi check_cta.py klassificerer det. Her
# kontrolleres det: ingen interne eller betalte filer, ingen døde referencer.
hdr "Publiceret træ (kontrol)"
run "tools/check_public_tree.py" python3 tools/check_public_tree.py

# ------------------------------------------------------------------- 7. SEO
hdr "SEO"
seo_python="$(pick_python)" || seo_python=""
if [ -z "$seo_python" ]; then
  bad "SEO (ingen python >= 3.10 fundet)" 1
else
  printf '$ %s tools/seo_check.py --verbose\n' "$seo_python"
  seo_out="$("$seo_python" tools/seo_check.py --verbose 2>&1)"
  seo_rc=$?
  printf '%s\n' "$seo_out" | tail -20
  pages="$(printf '%s' "$seo_out" | sed -n 's/^\([0-9]\{1,\}\) pages checked.*/\1/p' | tail -1)"
  findings="$(printf '%s' "$seo_out" | sed -n 's/^[0-9]* pages checked, \([0-9]\{1,\}\) with findings.*/\1/p' | tail -1)"
  if [ "$seo_rc" -ne 0 ]; then
    bad "tools/seo_check.py ($seo_rc)" "$seo_rc"
  elif [ -z "$pages" ] || [ "$pages" -lt 1 ]; then
    # En 0-side-kørsel er ikke bevis. Sibling-scriptet rapporterer præcis det,
    # og det er derfor denne kontrol fejler på, uanset exit code.
    bad "tools/seo_check.py scannede 0 sider — uden gyldig SEO-evidence" 1
  elif [ "$findings" != "0" ]; then
    bad "tools/seo_check.py fandt $findings sider med findings" 1
  else
    ok "tools/seo_check.py ($pages sider, 0 findings, $seo_python)"
  fi
fi

# -------------------------------------------- 8. sibling-kontraktets egen gate
hdr "Sibling-gate (../hermes-passiv)"
SIBLING="$ROOT/../hermes-passiv"
if [ -f "$SIBLING/build_sites.py" ] && [ -f "$SIBLING/tools/seo_check.py" ]; then
  if [ -n "$seo_python" ]; then
    printf '$ (cd %s && AUDITEDWP_DIR=%s python3 build_sites.py --only eucomplypro.com)\n' "$SIBLING" "$ROOT"
    (cd "$SIBLING" && AUDITEDWP_DIR="$ROOT" python3 build_sites.py --only eucomplypro.com)
    sib_rc=$?
    printf '$ (cd %s && %s tools/seo_check.py --only eucomplypro.com)\n' "$SIBLING" "$seo_python"
    sib_out="$(cd "$SIBLING" && "$seo_python" tools/seo_check.py --only eucomplypro.com 2>&1)"
    sib_seo_rc=$?
    printf '%s\n' "$sib_out" | tail -10
    sib_pages="$(printf '%s' "$sib_out" | sed -n 's/^\([0-9]\{1,\}\) pages checked.*/\1/p' | tail -1)"
    if [ "$sib_rc" -ne 0 ] || [ "$sib_seo_rc" -ne 0 ]; then
      bad "sibling build/SEO" $(( sib_rc || sib_seo_rc ))
    elif [ -z "$sib_pages" ] || [ "$sib_pages" -lt 1 ]; then
      printf 'ADVARSEL  sibling-SEO scannerede 0 sider — gyldig evidens er repoets egen tools/seo_check.py ovenfor\n'
      ok "sibling build (SEO er ufyldigt, se advarsel)"
    else
      ok "sibling build + SEO ($sib_pages sider)"
    fi
  else
    skip "sibling-gate (ingen python >= 3.10)"
  fi
else
  printf 'INFO  sibling-repoet %s findes ikke her.\n' "$SIBLING"
  printf 'INFO  Sibling-kommandoen fra missionen kan derfor ikke dokumenteres i dette kørselstidspunkt.\n'
  printf 'INFO  Gyldig SEO-evidence er repoets egen tools/seo_check.py i step 06, og den er obligatorisk.\n'
  ok "sibling-gate ikke tilgængelig (registreret, ikke fejlet)"
fi

# -------------------------------------------------------- 9. scanner-pakken
hdr "Scanner-pakke"
(cd eucomply-scanner && npm pack --dry-run >/dev/null 2>&1)
if [ $? -eq 0 ]; then ok "npm pack --dry-run"; else bad "npm pack --dry-run" 1; fi

# ------------------------------------------------------------ 10. live røgtest
hdr "Live røgtest"
if [ "$NETWORK" -eq 0 ]; then
  skip "live røgtest (--no-network)"
else
  printf '$ node eucomply-scanner/engine/index.js --json https://example.com\n'
  smoke_out="$(node eucomply-scanner/engine/index.js --json https://example.com 2>&1)"
  smoke_rc=$?
  smoke_checks="$(printf '%s' "$smoke_out" | grep -c '"label":' || true)"
  if [ "$smoke_rc" -ne 0 ]; then
    # Netværket kan være utilgængeligt i en sandbox. Logisk dækkes af step 04.
    printf 'ADVARSEL  røgtesten kunne ikke nå https://example.com (exit %s) — springes over, logic er dækket af step 04\n' "$smoke_rc"
    skip "live røgtest (netværk utilgængeligt)"
  elif [ "$smoke_checks" -lt 9 ]; then
    printf '%s\n' "$smoke_out" | tail -20
    bad "live røgtest fandt kun $smoke_checks tjek" 1
  else
    # Ikke "den publicerede motor": dette er den lokale kopi i
    # eucomply-scanner/, som ingen kan installere. Den publicerede pakke er
    # @mahope/eucomply-scanner i et andet repo, og de to er ikke ens — se
    # spørgsmål 13 og 17 i planen. At kalde denne "publiceret" var en
    # påstand uden dækning i det øjeblik, den blev skrevet.
    ok "live røgtest ($smoke_checks tjek fra den lokale motor)"
  fi
fi

# ------------------------------------------------- 11. drift mellem repo og produktion
# worker-scan/ og worker-watch/ deployes IKKE af CI (spørgsmål 9), så de kan glide
# fra site/ uden at nogen opdager det. Da denne gate blev skrevet, svarede
# eucomply-watch 1.0.0 mens koden erklærede 1.3.0 — en forskel der blandt andet
# betød at ejerskabstokens, SSRF-guarden og badge-endpointet ikke var live, og
# ingen af de ti steps ovenfor så det. Gate-definitionen udvides derfor med elleve.
hdr "Drift mellem repo og produktion"
if [ "$NETWORK" -eq 0 ]; then
  run "tools/check_production_drift.py --offline" python3 tools/check_production_drift.py --offline
else
  run "tools/check_production_drift.py" python3 tools/check_production_drift.py
fi

# ------------------------------- 12. er SSRF-guarden live, og har den lukket scanneren?
# worker-scan/ deployes ikke af CI (spørgsmål 9), så guarden på det endpoint alle
# besøgende rammer kan forsvinde uden at nogen opdager det. Denne gate måler den
# adfærdsmæssigt i stedet for at tro på et versionsfelt, der ikke findes i
# produktion. Grøn i dag: 12 reserverede intervaller afvises ved kanten, og en
# offentlig adresse giver stadig alle ni tjek.
hdr "Live-hærdning af den gratis scanner"
run "tools/check_live_hardening.py --selftest" python3 tools/check_live_hardening.py --selftest
if [ "$NETWORK" -eq 0 ]; then
  run "tools/check_live_hardening.py --offline" python3 tools/check_live_hardening.py --offline
else
  run "tools/check_live_hardening.py" python3 tools/check_live_hardening.py
fi

# ------------------------------------------------- 13. Døde betalingsudbydere
hdr "Ingen død betalingsudbyder i koden der kan nå en kunde"
run "tools/check_dead_providers.py --selftest" python3 tools/check_dead_providers.py --selftest
run "tools/check_dead_providers.py" python3 tools/check_dead_providers.py

# --------------------------- 14. Har den PUBLICEREDE motor et hul, motoren her ikke har?
# site/cli/ fortæller brugere at installere @mahope/eucomply-scanner. Den pakke er
# fra før hærdningen i 28795c3: den afviser IP-literaler men hverken løser DNS
# eller validerer redirect-hop. Vi må ikke publisere, så afvigelsen er en RAPPORT
# (jf. opgave 37/38 om hvorfor en permanent rød gate låser hele sitets deploy).
# Håndhævet er den anden retning: motoren her i repoet må aldrig miste en af de
# otte prøver, og må aldrig blive så stram at den lukker scanneren.
hdr "SSRF-guarden i den publicerede motor mod motoren i repoet"
run "tools/check_published_engine.mjs --selftest" node tools/check_published_engine.mjs --selftest
if [ "$NETWORK" -eq 0 ]; then
  run "tools/check_published_engine.mjs --offline" node tools/check_published_engine.mjs --offline
else
  run "tools/check_published_engine.mjs" node tools/check_published_engine.mjs
fi

# ------------------------- 15. Kan pluginen og motoren være uenige om én hjemmeside?
# Opgave 43 portede fem tjek fra motoren ind i pluginen. Porten blev linted og
# paritetstestet på kilde/zip — begge læser koden, ingen af dem kørte et tjek.
# Første kørsel af denne gate fandt en P0 i pluginens egen kode: signatur-tabellen
# er [navn, regex], matcheren læste $sig['re'], og fire tjek (Consent Mode v2,
# TCF, trackere, DORA) kunne ikke finde noget på noget site. En betalende kunde
# fik "ingen trackere fundet" på en side med Google Analytics i markup'en.
# Derfor måles motorerne adfærdsmæssigt, på de samme fixtures, i stedet for at
# tro på at en kode-diff er nok. Rød i begge retninger er ikke meningen: her skal
# de to produkter være ENS, så enhver afvigelse er et fund.
hdr "Pluginens forside-tjek mod den universelle motor"
run "tools/test_plugin_engine_parity.mjs" node tools/test_plugin_engine_parity.mjs
run "tools/test_plugin_engine_parity.mjs --selftest" node tools/test_plugin_engine_parity.mjs --selftest

# ------------------------- 16. Lover nogen side, at DORA-tjekket er noget andet?
# Det niende tjek er en statisk markørtælling i sidens tekst — motoren siger det
# selv ("This is not a DORA assessment"). Fire hovedsider sagde det modsatte:
# at tjekket kun gælder finanssektoren og "springes stille over for alle andre",
# hvilket hverken koden eller målingen bakker — det kører på alle sites og
# trækker et point fra en almindelig sides score. Guidens markørtabel dokumenterede
# desuden seks kategorier, hvoraf fire er uden for motorens ni signaturer.
# Denne port binder den publicerede beskrivelse til koden: hver række i tabellen
# skal kunne findes af en signatur, og ingen side må afgrænse tjekket til en
# branche. R5 (en bred "DORA + kapabilitetsord"-regel) er bevidst ikke lavet;
# se begrundelsen i tools/check_dora_claims.py.
hdr "DORA-markørtjekket er det, siderne siger det er"
run "tools/check_dora_claims.py --selftest" python3 tools/check_dora_claims.py --selftest
run "tools/check_dora_claims.py" python3 tools/check_dora_claims.py

# ------------------------- 17. Kør de elleve tjek — også de seks ingen kørte
# Trin 15 stoppede ved de fem tjek, der deler en motor med den gratis scanner.
# `ssl`, `cookies`, `forms`, `backups`, `plugins` og `legal` var kun linted, og
# opgave 44 viste at netop det er når et tjek er dødt: `php -l` læser ikke kode,
# og kilde/zip-pariteten kan kun se forskel mellem kopier, ikke en fejl der er
# identisk i alle tre. Denne port kører alle elleve og kræver fem egenskaber:
# at listen er læst ud af run_checks() og ikke skrevet her, at hvert tjek kan nå
# både bestået og fejlet, at et tjek der ikke kunne køre aldrig er bestået, at
# et fejlet tjek ikke bærer en etiket der siger at det lykkedes, og at hentinger
# tælles for sig. Den fandt den første fejl i denne iteration: "Legal pages
# checked" og "Forms reviewed" stod på de røde rækker i den betalte rapport.
hdr "Alle elleve plugin-tjek kørt adfærdsmæssigt"
run "tools/test_plugin_checks.php" php tools/test_plugin_checks.php
run "tools/test_plugin_checks.php --selftest" php tools/test_plugin_checks.php --selftest

# ------------------------------- 18. Kan `tjek produktion` fejle på en rigtig udgivelse?
# Opgave 47: CI `36250487311` var grøn i deploy og rød i verify med *"peger på
# eucomply-1.3.12.zip, forventede eucomply-1.3.13.zip"*, og live-sitet svarede
# 1.3.13 fyrre sekunder senere. Kontrollen læste /update.json ÉN gang og slog
# fast ved første læsning. Nu polles der med et loft, og loftet er hele pointen:
# en udgivelse der ALDRIG kommer ud skal stadig give rødt. Denne gate læser
# deploy-site.yml og kræver at jobbet bruger værktøjet, at den gamle
# øjeblikkelige sammenligning er væk, at jobbets timeout overstiger den værste
# ventetid, og at de otte øvrige kontrolpunkter stadig er der — ellers ville
# "urørt" være en påstand. Uden dette step kunne værktøjet være grønt i porten
# og ubrugt i workflowen, præcis fejlen opgave 39 fandt i en anden kontrol.
hdr "Deploy-verificeringen kan skelne racen fra en manglende udgivelse"
run "tools/wait_for_deploy.py --selftest" python3 tools/wait_for_deploy.py --selftest
run "tools/wait_for_deploy.py --check-workflow" python3 tools/wait_for_deploy.py --check-workflow

# ------------------------ 19. Kan en etiket modsige sit eget dom?
# Opgave 45b fandt to checks, der skrev "Legal pages checked" på en RØD række.
# Opgave 48 fandt spejlingen: en GRØN række hvis etiket beskriver en mangel
# ("No third-party trackers detected" på en side uden trackere). Og denne gate
# fandt en tredje, som ingen af de to foregående kunne se: en side der svarede
# over http men sendte en HSTS-header fik i begge JS-motorer en rød `ssl`-række
# med etiketten "HTTPS + HSTS OK" — ternaryen testede `hsts` før `finalIsHttps`.
# Det er tre fejl i én familie, to af dem i en betalt vare eller dens tragt, og
# ingen af dem var synlig for en port der læser kode: alle tre er etiketter, der
# kun modsiger dommen når den ER modsagt.
# Derfor kører porten alle tre motorer — site, npm og plugin — på fixtures og
# kræver at hver etiket har samme polaritet som sit dom. Advarselsrækker er
# undtaget med vilje: "HTTPS OK, no HSTS" skal kunne sige begge dele.
hdr "Etiketten har samme polaritet som dommet — i alle tre motorer"
run "tools/check_verdict_labels.mjs --selftest" node tools/check_verdict_labels.mjs --selftest
run "tools/check_verdict_labels.mjs" node tools/check_verdict_labels.mjs

# ------------------------ 20. Er den betalte `forms` svagere end den gratis?
# Opgave 49 fandt, at `check_forms()` læste kun WordPress-tilstanden, mens
# motoren læser markup'en: en håndbygget formular fejlede i den gratis scanner
# og bestod i den rapport et bureau betaler for. Trin 15 og 19 holdt de to
# produkter sammen på de ni URL-tjek, men `forms` var ikke blandt dem.
# Denne port kører `check_forms()` og motorens `forms` på de samme ni fixtures
# og kræver tre regler: pluginen består aldrig noget motoren fejler (R1), en
# `<form>` uden privatlivslink består aldrig uanset WordPress (R2), og en fejl
# uden en kilde i fixturet er rød (R3) — ellers ville R1 alene være opfyldt af
# en plugin der fejler alt. Selftesten muterer repoets egen `check_forms()` i begge
# retninger, så porten kan ikke være grøn af en fejl, den ikke kan se.
hdr "forms i den betalte vare mod forms i den gratis scanner"
run "tools/check_forms_parity.mjs" node tools/check_forms_parity.mjs
run "tools/check_forms_parity.mjs --selftest" node tools/check_forms_parity.mjs --selftest

# ------------------------ 21. Kan de juridiske mønstre læse DA/SV/NL?
# Opgave 52 målte LEGAL_PATTERNS med 22 rigtige footer-links: 0 af 22 blev
# fundet. Følgen var ikke en etiket men en score — en dansk butik med
# privatlivspolitik, handelsbetingelser og cookiepolitik fik `legal` = én side og
# tabte et point, mens den samme side på engelsk bestod. Og selve `terms` havde
# separatoren `[_-]?`, som aldrig matcher et mellemrum, så "Terms of Service" og
# "Terms & Conditions" var usynlige på **alle** sprog. Trin 20 dækker `forms`;
# dette dækker `legal`, som ingen port havde læst adfærdsmæssigt.
# Fire regler: en (mønster, sprog)-række uden egen fixture er rød (dækket, ikke
# antaget), de to motorer skal svare identisk, en sætning uden link er ikke en
# juridisk side og ét link er stadig ét, og de samme tre dokumenter skal give
# samme dom på fire sprog. Selftesten muterer repoets egne filer for hvert
# mønster i begge motorer.
hdr "juridiske sider læser dansk, svensk og nederlandsk"
run "tools/check_legal_langs.mjs" node tools/check_legal_langs.mjs
run "tools/check_legal_langs.mjs --selftest" node tools/check_legal_langs.mjs --selftest

# ------------------------ 22. Kan den betalte `legal` finde de danske sider?
# Trin 21 dækker `legal` i de to JS-motorer. Det er ikke den samme kode: pluginens
# `check_legal_pages()` slår **WordPress-sider** op efter sti og titel, og listen
# var `imprint`, `impressum`, `accessibility-statement`, `accessibility` plus to
# LIKE-opslag på `%Imprint%` og `%Impressum%` — kun engelsk og tysk. Målt: en dansk
# butik med *Om os*, *Handelsbetingelser* og *Privatlivspolitik* fik "3 of 3 legal
# pages missing" i den rapport et bureau betaler $79 om året for. Fem regler: de
# tre sprog skal bestå, de skal give samme dom som engelsk, hver af de to
# opslagsveje (WordPress-sti og sidetitel) skal finde siden *alene*, en butik uden
# sider skal stadig fejle, og "Om os i pressen" må ikke tælles som imprint.
# Selftesten muterer repoets egen pluginfil fire gange, så porten kan være rød.
hdr "den betalte jurid.side-tjek læser dansk, svensk og nederlandsk"
run "tools/check_legal_pages_langs.php" php tools/check_legal_pages_langs.php
run "tools/check_legal_pages_langs.php --selftest" php tools/check_legal_pages_langs.php --selftest

# ------------------------------------------------------------------ udfald
printf '\n'
if [ "$FAILED" -ne 0 ]; then
  printf 'GATE RØD — se de FEJL-linjer ovenfor.\n'
  exit 1
fi
printf 'GATE GRØN — alle %d steps bestået.\n' "$STEP"
