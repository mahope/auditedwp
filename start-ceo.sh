#!/bin/zsh
# start-ceo.sh — starter Hermes' research-fase naar API-kvoten er tilbage.
# Koerer én lang session ad gangen og stopper pænt ved rate-limit,
# saa kvoten ikke braendes af i en fejl-loekke.
export PATH="$HOME/.local/bin:$PATH"
DIR="$HOME/hermes-ceo"
LOG="$DIR/ceo.log"
cd "$DIR" || exit 1

# Vent til kvoten faktisk er tilbage (tjek hvert 5. minut, maks 4 timer)
for i in {1..48}; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" -H 'Content-Type: application/json' \
    -d '{"model":"stealth/ox-alpha","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
    https://openrouter.ai/api/v1/chat/completions)
  [ "$code" = "200" ] && { echo "$(date -Iseconds) kvote tilbage - starter" >> "$LOG"; break; }
  echo "$(date -Iseconds) kvote ikke klar (HTTP $code) - venter" >> "$LOG"
  sleep 300
done

OPGAVE='Du er CEO og stifter. Laes AGENTS.md i denne mappe - det er dit fulde mandat.

Start research-fasen nu. I DENNE session skal du:
1. Generere mindst 30 kandidatidéer til en international, nytaenkende og indtjenende forretning. Soeg aktivt efter reelle problemer - klager, daarlige anmeldelser, forum-traade, nye regler, nye API-muligheder.
2. Undersoege de mest lovende med web-search og skrive fundene med kilder i RESEARCH.md.
3. Skaere ned til 5 finalister og for hver skrive den staerkeste sag IMOD idéen.
4. Opdatere STATUS.md med hvor du er, og hvad naeste iteration skal undersoege.

Skriv ikke produktkode endnu. Beslut ikke endeligt endnu - det kraever flere iterationer.
Braend ikke kvote paa gentagne fejl: rammer du en rate-limit, saa notér det i STATUS.md og stop.'

perl -e 'alarm shift; exec @ARGV' 5400 hermes -z "$OPGAVE" >> "$LOG" 2>&1
echo "$(date -Iseconds) session afsluttet (exit $?)" >> "$LOG"
