#!/usr/bin/env python3
"""add_dynamic_checkout.py — giver ComplianceDocs-siderne samme runtime-flip som Pro/DevNotify/QuickFormat.

Tilfoejer til hver side under site/store/:
- Et <script> der henter /config fra waitlist-workeren.
- Er CHECKOUT_URL sat paa workeren, erstattes waitlist-formularen (#buyform/#bundleform)
  og alle "get notified"-knappper med direkte Lemon Squeezy-links. Ingen redeploy noedvendig.
Idempotent: markerer indsaettelsen med <!-- DYNAMIC-CHECKOUT --> og goerer intet hvis den findes.
"""
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"

PRICES = {
    "dpa": ("$59", "DPA template"),
    "nis2-clauses": ("$49", "NIS2 clause set"),
    "nda-clauses": ("$29", "NDA clauses"),
    "eaa-statement": ("$39", "EAA statement"),
    "report-kit": ("$69", "Report kit"),
}

SNIPPET = """
<!-- DYNAMIC-CHECKOUT -->
<script>
(async function(){
  try{
    var r = await fetch('https://waitlist-eucomply.mahope-eeb.workers.dev/config');
    if(!r.ok) return;
    var cfg = await r.json();
    if(!(cfg && cfg.checkout_url)) return;
    var url = cfg.checkout_url;
    // 1. Erstat venteliste-formular med koeb-link
    document.querySelectorAll('#buyform, #bundleform').forEach(function(f){
      var price = f.textContent.match(/\\$(\\d+)/);
      var label = 'Buy now' + (price ? ' — $' + price[1] : '') + ' · instant download';
      var a = document.createElement('a');
      a.className = f.className.replace('wform','btn') || 'btn';
      if(!a.classList.contains('btn')) a.classList.add('btn');
      a.href = url; a.target = '_blank'; a.rel = 'noopener';
      a.style.cssText = 'display:inline-block;padding:8px 14px;background:var(--acc,#2868d0);color:#fff;border-radius:4px;text-decoration:none;font-weight:600';
      a.textContent = label;
      f.parentNode.replaceChild(a, f);
    });
    // 2. Konvertér "Get notified"-knappper til koeb-links
    document.querySelectorAll('button[onclick*="buyform"]').forEach(function(b){
      var a = document.createElement('a');
      a.href = url; a.target = '_blank'; a.rel = 'noopener'; a.className = b.className;
      a.textContent = b.textContent.replace(/Get notified/i, 'Buy now');
      b.parentNode.replaceChild(a, b);
    });
    // 3. Skjul "notify me"-tekster
    document.querySelectorAll('.wmsg').forEach(function(m){ m.textContent = ''; });
  }catch(e){ /* worker ikke tilgaengelig — behold venteliste */ }
})();
</script>
"""


def process(path: Path, marker: str) -> bool:
    text = path.read_text()
    if "DYNAMIC-CHECKOUT" in text:
        return False
    assert "</body>" in text, f"{path}: </body> ikke fundet"
    text = text.replace("</body>", SNIPPET + "</body>")
    path.write_text(text)
    return True


def main():
    changed = []
    for slug in PRICES:
        p = SITE / "store" / slug / "index.html"
        if p.exists() and process(p, slug):
            changed.append(str(p.relative_to(SITE)))
    idx = SITE / "store" / "index.html"
    if idx.exists() and process(idx, "index"):
        changed.append("store/index.html")
    print("Opdateret:")
    for c in changed:
        print(" -", c)
    if not changed:
        print("Intet at opdatere (allerede patchet).")


if __name__ == "__main__":
    main()
