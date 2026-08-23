#!/bin/zsh
# ceo-loop2.sh — Hermes' fase 2: revurdér beslutningen paa indtjening, research
# videre hvis det goer dig klogere paa hvor pengene er, og byg naar du er sikker.
export PATH="$HOME/.local/bin:$PATH"
DIR="$HOME/hermes-ceo"
LOG="$DIR/ceo.log"
cd "$DIR" || exit 1
MAX=${1:-15}

for i in $(seq 1 $MAX); do
  [ -f "$DIR/STOP" ] && { echo "$(date -Iseconds) STOP-fil - slutter" >> "$LOG"; break; }

  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" -H 'Content-Type: application/json' \
    -d '{"model":"stealth/ox-alpha","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
    https://openrouter.ai/api/v1/chat/completions)
  if [ "$code" != "200" ]; then
    echo "$(date -Iseconds) kvote opbrugt (HTTP $code) - stopper for i dag" >> "$LOG"
    break
  fi

  echo "$(date -Iseconds) === FASE2-iteration $i/$MAX ===" >> "$LOG"
  OPGAVE='Du er CEO og stifter. Laes AGENTS.md (mandatet er AENDRET), DECISION.md, STATUS.md og RESEARCH.md.

MADS HAR AENDRET MANDATET 23. august:
- Kravet om NYTAENKNING er LEMPET. Idéen behoever ikke vaere original. Kedelig er fint.
- Det eneste kriterium der taeller: DEN SKAL TJENE PENGE. Saa mange som muligt, saa hurtigt som muligt.
- Research maa du gerne lave - men kun den slags der goer dig klogere paa HVOR PENGENE ER.
- Domaene: vent ikke. Mads koeber det senere. Byg paa Cloudflare Pages gratis *.pages.dev.

Din opgave i denne iteration - vaelg selv hvad der er rigtigt:

A) HVIS du er i tvivl om din nuvaerende beslutning holder under det nye kriterium:
   Revurdér den mod alternativer, maalt paa fem ting: hvor hurtigt foerste kunde betaler,
   hvor stort beloebet er, hvor mange kunder der realistisk kan naas, hvor tilbagevendende
   indtaegten er, og hvad det koster at levere. Skriv resultatet i DECISION.md.
   Husk: dine tidligere 22 iterationer droppede idéer for at vaere for lidt originale eller
   for konkurrenceudsatte - de kriterier gaelder ikke laengere. Kig paa dem igen med pengelinsen.

B) HVIS beslutningen holder (eller du lige har truffet en ny):
   Begynd at bygge. Opret BUILD.md med den korteste vej til foerste betalende kunde,
   og byg foerste punkt: en landingsside der saelger - hvad det er, hvem det er til,
   hvad det koster, og hvordan man koeber. Rigtige filer, rigtig kode, klar til Cloudflare Pages.

Opdater altid STATUS.md kort til sidst: hvor staar du, og hvad er naeste skridt.

Graenser: ingen udgifter uden Mads ja. Ingen udadvendte henvendelser i hans navn. Intet ulovligt.
Rammer du en rate-limit, saa notér det i STATUS.md og stop - braend ikke kvote paa fejl.'

  perl -e 'alarm shift; exec @ARGV' 5400 hermes -z "$OPGAVE" >> "$LOG" 2>&1
  echo "$(date -Iseconds) iteration $i afsluttet (exit $?)" >> "$LOG"
  sleep 20
done
echo "$(date -Iseconds) ceo-loop2 afsluttet" >> "$LOG"
