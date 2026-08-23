#!/bin/zsh
# ceo-loop.sh — koerer Hermes' CEO-research i iterationer indtil den har truffet
# en beslutning (DECISION.md) eller kvoten er opbrugt. Stopper paent ved rate-limit.
export PATH="$HOME/.local/bin:$PATH"
DIR="$HOME/hermes-ceo"
LOG="$DIR/ceo.log"
cd "$DIR" || exit 1
MAX=${1:-12}

for i in $(seq 1 $MAX); do
  [ -f "$DIR/STOP" ] && { echo "$(date -Iseconds) STOP-fil - slutter" >> "$LOG"; break; }
  if [ -f "$DIR/DECISION.md" ]; then
    echo "$(date -Iseconds) DECISION.md findes - research-fasen er slut" >> "$LOG"; break
  fi

  # kvote-tjek foer hver iteration
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" -H 'Content-Type: application/json' \
    -d '{"model":"stealth/ox-alpha","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
    https://openrouter.ai/api/v1/chat/completions)
  if [ "$code" != "200" ]; then
    echo "$(date -Iseconds) kvote opbrugt (HTTP $code) - stopper for i dag" >> "$LOG"
    break
  fi

  echo "$(date -Iseconds) === CEO-iteration $i/$MAX ===" >> "$LOG"
  OPGAVE="Du er CEO og stifter. Laes AGENTS.md, STATUS.md og RESEARCH.md i denne mappe foerst - de er dit mandat og din hidtidige research.

Fortsaet research-fasen med naeste iteration. Foelg planen du selv skrev i STATUS.md.

I denne iteration skal du:
1. Grave dybere i de finalister der stadig staar - konkurrenter, reel markedsstoerrelse, prissaetning, hvordan man naar kunderne, og hvad det koster.
2. Droppe dem der ikke holder, og skrive hvorfor.
3. Opdatere RESEARCH.md med nye fund og kilder, og STATUS.md med hvor du er og hvad naeste iteration skal.

Er du efter denne iteration overbevist om ÉN idé - og kan du forsvare den mod din egen haardeste kritik - saa skriv DECISION.md med: hvad, til hvem, hvorfor nu, indtjeningsmodel, hvad der kan slaa den ihjel, hvorfor den slog de naestbedste, samt 3-5 forslag til domaenenavn i prioriteret raekkefoelge.
Er du ikke overbevist endnu, saa lad vaere - tag en iteration mere. Det er bedre at bruge flere runder end at vaelge for tidligt.

Skriv ikke produktkode endnu. Brug ingen penge."

  perl -e 'alarm shift; exec @ARGV' 5400 hermes -z "$OPGAVE" >> "$LOG" 2>&1
  echo "$(date -Iseconds) iteration $i afsluttet (exit $?)" >> "$LOG"
  sleep 20
done
echo "$(date -Iseconds) ceo-loop afsluttet" >> "$LOG"
