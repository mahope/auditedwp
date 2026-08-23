#!/bin/zsh
# kvote-tjek.sh — skelner mellem de to slags 429 fra OpenRouter.
# Skriver: OK | UPSTREAM (modellen overbelastet globalt - vent og proev igen)
#        | DAGSKVOTE (vores egen kvote opbrugt - stop for i dag) | FEJL:<kode>
r=$(curl -s -w '\n[[HTTP:%{http_code}]]' -X POST \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" -H 'Content-Type: application/json' \
  -d '{"model":"stealth/ox-alpha","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
  https://openrouter.ai/api/v1/chat/completions 2>/dev/null)
code=$(echo "$r" | grep -o '\[\[HTTP:[0-9]*\]\]' | grep -o '[0-9]*')
if [ "$code" = "200" ]; then echo OK; exit 0; fi
if echo "$r" | tr -d ' \n' | grep -q "upstream_provider_shared_pool"; then echo UPSTREAM; exit 0; fi
if echo "$r" | tr -d ' \n' | grep -q "free-models-per-day\|openrouter_free_tier_daily"; then echo DAGSKVOTE; exit 0; fi
echo "FEJL:$code"
