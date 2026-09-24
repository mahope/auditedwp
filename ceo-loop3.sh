#!/bin/zsh
# ceo-loop3.sh — Hermes' CEO-loop med korrekt haandtering af de to 429-typer:
#   UPSTREAM  = Ox Alpha overbelastet globalt -> vent og proev igen (op til 2 timer)
#   DAGSKVOTE = vores egen kvote brugt -> stop for i dag
export PATH="$HOME/.local/bin:$PATH"
DIR="$HOME/hermes-ceo"
# hver agent maa KUN skrive i sin egen mappe
export HERMES_WRITE_SAFE_ROOT="$DIR"
LOG="$DIR/ceo.log"
cd "$DIR" || exit 1
MAX=${1:-15}

for i in $(seq 1 $MAX); do
  [ -f "$DIR/STOP" ] && { echo "$(date -Iseconds) STOP-fil - slutter" >> "$LOG"; break; }

  # vent paa modellen, hvis den er globalt overbelastet
  vent=0
  while true; do
    st=$("$DIR/kvote-tjek.sh")
    [ "$st" = "OK" ] && break
    if [ "$st" = "DAGSKVOTE" ]; then
      echo "$(date -Iseconds) egen dagskvote opbrugt - stopper for i dag" >> "$LOG"; exit 0
    fi
    vent=$((vent+1))
    if [ "$vent" -gt 24 ]; then
      echo "$(date -Iseconds) modellen har vaeret utilgaengelig i 2 timer ($st) - stopper" >> "$LOG"; exit 0
    fi
    echo "$(date -Iseconds) $st - venter 5 min (forsoeg $vent/24)" >> "$LOG"
    sleep 300
  done

  echo "$(date -Iseconds) === iteration $i/$MAX ===" >> "$LOG"
  OPGAVE='Du er CEO og stifter.

NYE RAMMER FRA MADS (23. august) - se AGENTS.md for detaljerne:
1. UNIVERSELT: alt du bygger skal virke paa andet end WordPress. Kernen skal tage en almindelig URL og fungere uanset CMS. Platform-integrationer er indpakninger, ikke selve produktet.
2. FLERE PRODUKTER: du maa gerne bygge en lille portefoelje. Men goer ÉT faerdigt (virker, udgivet, kan tage imod penge) foer du starter det naeste.
3. IKKE KUN HJEMMESIDER: desktop-programmer (Tauri/Electron med licensnoegle), CLI-vaerktoejer (npm/pip/brew), browser-udvidelser, udvidelser til VS Code/Figma/Obsidian/Shopify/Raycast, API-tjenester, eller digitale produkter paa en markedsplads med indbygget betaling - alt taeller. Vaelg efter hvad der giver penge hurtigst, ikke hvad der er nemmest at bygge.
4. MARKETING OG DRIFT er ogsaa dit ansvar - Mads hjaelper kun med opsaetning. Du staar selv for indhold, SEO, produkttekster, priser, vilkaar og selvbetjent support paa dine EGNE flader, uden at spoerge. Men alt der rammer et andet menneske direkte i hans navn (kolde mails, DM, opslag i grupper, kommentarer, betalte annoncer) skriver du faerdigt og lader vente paa hans ja - notér det i STATUS.md.
5. BLIV VED MED AT FORBEDRE: et produkt er aldrig faerdigt. Er du blokeret paa Mads konti, saa stop IKKE - forbedr det du har, eller byg det naeste der ikke er blokeret. Ventetid er arbejdstid. Prioritér i denne raekkefoelge: det der staar mellem besoegende og betaling, selve produktet, det der traekker folk til, og til sidst bredden.

Foerste opgave i denne iteration: vurdér aerligt om det du har opfylder punkt 1. Er det bundet til én platform, saa traek kernen ud og behold det du har bygget som ÉN indpakning. Smid ikke arbejde vaek - byg det om. Skriv vurderingen i STATUS.md.

 Laes AGENTS.md (mandatet er AENDRET), DECISION.md, STATUS.md og RESEARCH.md.

MADS HAR AENDRET MANDATET 23. august:
- Kravet om NYTAENKNING er LEMPET. Idéen behoever ikke vaere original. Kedelig er fint.
- Det eneste kriterium der taeller: DEN SKAL TJENE PENGE. Saa mange som muligt, saa hurtigt som muligt.
- Research maa du gerne lave - men kun den slags der goer dig klogere paa HVOR PENGENE ER.
- Domaene: KOEB ER AABENT. Cloudflare Registrar-adgang er verificeret 23/8. Vaelg navn, skriv det i DECISION.md, sig til.

ENDNU NYERE RAMMER (23. august, aften):
- BETALING: Alt salg koerer via Stripe-betalingslinks og licensserveren paa mahope.tools (tidligere Lemon Squeezy, som afviste kontoen 24/9). Kontrakten med links og licens-API: business/planer/2026-09-24-stripe-kontrakt.md i workspacet. Ingen Stripe-noegler i kode eller sider.
- AMAZON KDP KAN ALDRIG AUTOMATISERES. Ingen offentlig API. Mads skal uploade manuelt. Planlaeg aldrig omkring det.
- HELT FRIE RAMMER: Mads siger du maa gaa videre til HELT NYE PROJEKTER, ogsaa uden for hans fagomraade. Web/compliance er hvor vi startede, ikke en graense.
- ER DU BLOKERET: start noget NYT frem for at pudse det gamle igen. Skriv blokeringen som EN linje i STATUS.md og gaa videre. Gentag den ALDRIG iteration efter iteration.
- MAAL ALDRIG SUCCES PAA DINE EGNE TESTS. Du rapporterede 6 tilmeldinger; alle seks var dine egne. Det rigtige tal var 0. Er tallet 0, saa skriv 0.

Vaelg selv hvad der er rigtigt i denne iteration:

A) Er du i tvivl om din nuvaerende beslutning holder under pengekriteriet, saa revurdér den.
   Maal hver kandidat paa fem ting: hvor hurtigt foerste kunde betaler, hvor stort beloebet er,
   hvor mange kunder der realistisk kan naas, hvor tilbagevendende indtaegten er, og hvad det
   koster at levere. Dine tidligere iterationer droppede idéer for at vaere for lidt originale
   eller for konkurrenceudsatte - de kriterier gaelder IKKE laengere. Kig paa dem igen med pengelinsen.

B) Holder beslutningen, saa BYG. Opret BUILD.md med den korteste vej til foerste betalende kunde,
   og byg naeste punkt: foerst en landingsside der saelger - hvad det er, hvem det er til, hvad det
   koster, og hvordan man koeber. Rigtige filer, rigtig kode, klar til Cloudflare Pages.

Opdater altid STATUS.md kort til sidst: hvor staar du, og hvad er naeste skridt.

Graenser: ingen udgifter uden Mads ja. Ingen udadvendte henvendelser i hans navn. Intet ulovligt.'

  perl -e 'alarm shift; exec @ARGV' 5400 hermes -z "$OPGAVE" >> "$LOG" 2>&1
  echo "$(date -Iseconds) iteration $i afsluttet (exit $?)" >> "$LOG"
  sleep 20
done
echo "$(date -Iseconds) ceo-loop3 afsluttet" >> "$LOG"
