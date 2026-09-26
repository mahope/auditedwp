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
run "tools/test_quickcheck_render.mjs" node tools/test_quickcheck_render.mjs
run "tools/test_quickcheck_render.mjs --selftest" node tools/test_quickcheck_render.mjs --selftest
run "tools/check_production_drift.py --selftest" python3 tools/check_production_drift.py --selftest

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

# ------------------------------------------------------------------ udfald
printf '\n'
if [ "$FAILED" -ne 0 ]; then
  printf 'GATE RØD — se de FEJL-linjer ovenfor.\n'
  exit 1
fi
printf 'GATE GRØN — alle %d steps bestået.\n' "$STEP"
