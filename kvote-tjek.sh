#!/bin/zsh
# kvote-tjek.sh v2 — afgoer om modellen reelt kan bruges lige nu.
# v1 stolede paa HTTP 200, men Ox Alpha svarer tidvis 200 med TOMT indhold,
# saa loops braendte iterationer af paa svar uden tekst. v2 kraever, at der
# faktisk kommer indhold tilbage.
# Skriver: OK | UPSTREAM (overbelastet/tomt - vent) | DAGSKVOTE (stop for i dag) | FEJL:<kode>
r=$(curl -s -w '\n[[HTTP:%{http_code}]]' --max-time 90 -X POST \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" -H 'Content-Type: application/json' \
  -d '{"model":"stealth/ox-alpha","messages":[{"role":"user","content":"Svar med ordet OK"}],"max_tokens":200}' \
  https://openrouter.ai/api/v1/chat/completions 2>/dev/null)
code=$(echo "$r" | grep -o '\[\[HTTP:[0-9]*\]\]' | grep -o '[0-9]*')
flad=$(echo "$r" | tr -d ' \n')

if echo "$flad" | grep -q "upstream_provider_shared_pool"; then echo UPSTREAM; exit 0; fi
if echo "$flad" | grep -q "free-models-per-day\|openrouter_free_tier_daily"; then echo DAGSKVOTE; exit 0; fi

if [ "$code" = "200" ]; then
  # 200 er ikke nok - der skal vaere tekst i svaret
  if echo "$flad" | grep -qE '"content":"[^"]+"'; then echo OK; exit 0; fi
  echo UPSTREAM; exit 0   # tomt svar = modellen kan ikke levere lige nu
fi
echo "FEJL:$code"
