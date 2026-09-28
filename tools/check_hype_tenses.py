#!/usr/bin/env python3
"""Port: HYPE-renseren skal bevare boejningen, og ingen publiceret side maa have
en tredjepersonssaetning, som den har brudt.

    python3 tools/check_hype_tenses.py
    python3 tools/check_hype_tenses.py --selftest

Malt 28/9. `apply_shell.py`s HYPE-tabel er den rens, der fjerner markedsfoerings-
ord fra prosaen, naar en side gaar gennem skallen. Den havde **en** erstatning pr.
verbum, uanset hvilken form ordet havde:

    Unlock(s|ed)?  ->  "Get"

Saa "It unlocks the starters" blev "It get the starters". Sprogligt er det ikke en
typo, det er en fejlretning der kun kan ses naar man laeser sætningen, og den er
allerede ude i teksten paa en publiceret side:

    site/deskuptime/thanks/index.html:89
    "Run this once - it get unlimited URLs, faster intervals and ..."

Planen sagde at kun `/api/` var ramt, fordi de øvrige sider er "native" og derfor
skipper renseren. Det er sandt for *den del* af siderne der er skrevet i den nye
skal, men ikke for de 170 legacy-sider, og porten maaler nu det paa traeet frem
for at tro paa en sideklasse.

To regler, og de dømmer hver sin retning:

  R1  Hver bøjet hype-verbum i tabellen skal erstattes med samme bøjning:
      `unlocks` -> `gets`, `unlocked` -> `got`, `supercharges` -> `speeds up`,
      `elevated` -> `improved`. Porten laeser den **rigtige** tabel fra
      `apply_shell.py` (aldrig en kopi), saa de to ikke kan glide fra hinanden,
      og en baseform der mangler en bøjning, eller et nyt verbum i tabellen som
      porten ikke kender, er ogsaa rødt.
  R2  Ingen publiceret side maa have en tredjeperson der faar grundformen af en
      HYPE-erstatning: "It get", "which improve", "Pro speed up". Det er den
      fejl, tabellen laves, naar den engang kører igen - saa porten goer
      rød paa *resultatet* og ikke bare paa kilden.

R1 og R2 loeser intet op i sig selv. De goer fundet permanent, saa en ny side
eller en ny tabel-riktning ikke kan gense den samme fejl i samme stilhed.
"""
import html as htmllib
import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
APPLY_SHELL = ROOT / "tools" / "apply_shell.py"

# Bøjningen hver hype-verbum skal have, efter sin endelse. Nøglen er det ord
# mønsteret starter på, i små bogstaver. En bøjning der mangler her, kan ikke
# bestå R1 — det er derfor porten ikke bare læser tabellen, men beder om
# heleformen for hvert nyt verbum der lægges ind.
EXPECT = {
    "unlock": {"": "get", "s": "gets", "ed": "got"},
    "supercharge": {"": "speed up", "s": "speeds up", "d": "sped up"},
    "elevate": {"": "improve", "s": "improves", "d": "improved"},
}

# 3. person ental kræver en bøjet verbalform. Kun disse ord tæller med, fordi
# de er dem, HYPE-tabellen skriver i, og de er aldrig korrekte i grundform
# efter disse subjekter: "it get" og "which improve" er ikke engelsk.
SUBJECTS = r"(?:It|it|This|this|That|that|Which|which|Pro|pro|He|he|She|she|There|there|These|these|Those|those)"

# Verber der gør at grundformen er korrekt: "what data does it get". Uden
# denne undtagelse ville porten være rød på en rigtig, korrekt sætning.
AUXILIARIES = {
    "does", "do", "did", "to", "can", "could", "will", "would", "may", "might",
    "should", "must", "let", "please", "how", "what", "why", "when", "where",
    "who", "if", "and", "or", "not", "never", "always", "here", "there",
}

BASE_VERBS = sorted({form for forms in EXPECT.values() for suf, form in forms.items() if not suf})

BROKEN = re.compile(rf"\b({SUBJECTS})\s+({BASE_VERBS[0]}|{'|'.join(BASE_VERBS[1:])})\b", re.I)
HYPE_WORD = re.compile(r"\b[A-Za-z-]*\b(?:%s)\b" % "|".join(EXPECT))
SKIP_BLOCK = re.compile(r"<(script|style|pre|code)\b[^>]*>.*?</\1>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")


def load_hype():
    """Den rigtige HYPE-tabel fra `apply_shell.py` — aldrig en kopi her."""
    spec = importlib.util.spec_from_file_location("apply_shell_for_hype", APPLY_SHELL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.HYPE


def parse_pattern(pat):
    """(basisord, endelser) for et bøjt mønster, ellers None.

    `\\bUnlock(s|ed)?\\b` -> ("Unlock", ["s", "ed"]) med tom endelse som eneste
    mulighed. `\\bSupercharge(s|d)?\\b` -> ("Supercharge", ["s", "d"]).
    Adjektiver som `\\bSeamless\\b` har ingen bøjning at bevare -> None.
    """
    source = pat.pattern
    m = re.fullmatch(r"\\b(.+?)\(([^()]*)\)\?\\b", source)
    if m:
        return m.group(1), [s for s in m.group(2).split("|") if s]
    m = re.fullmatch(r"\\b(.+?)\[([^\]]+)\]\?\\b", source)
    if m:
        return m.group(1), list(m.group(2))
    return None


def cased(word, upper):
    return word[:1].upper() + word[1:] if upper else word


def table_findings(hype):
    f = []
    seen = set()
    for pat, rep in hype:
        parsed = parse_pattern(pat)
        if not parsed:
            continue
        base, suffixes = parsed
        key = base.lower()
        seen.add(key)
        if key not in EXPECT:
            f.append(f"R1 {pat.pattern!r} er et bøjet ord porten ikke kender — tilføj det i EXPECT")
            continue
        wanted = EXPECT[key]
        if sorted(suffixes) != sorted(s for s in wanted if s):
            f.append(f"R1 {base!r} dækker {suffixes or ['grundform']}, men porten kræver {sorted(s for s in wanted if s)}")
        upper = base[:1].isupper()
        for suf in sorted(set(suffixes) | set(wanted)):
            word = base + suf
            got = pat.sub(rep, word)
            want = cased(wanted.get(suf, ""), upper)
            if got != want:
                f.append(f"R1 {word!r} bliver {got!r} — porten kræver {want!r} ({pat.pattern})")
    for missing in sorted(set(EXPECT) - seen):
        f.append(f"R1 tabellen har ikke længere en bøjning for {missing!r} — porten kan ikke dømme den")
    return f


def prose_of(text):
    t = SKIP_BLOCK.sub(" ", text)
    t = TAG.sub(" ", t)
    return re.sub(r"\s+", " ", htmllib.unescape(t))


def tree_findings(pages):
    f = []
    for rel, text in pages.items():
        prose = prose_of(text)
        for m in BROKEN.finditer(prose):
            before = prose[: m.start(1)].rstrip().rsplit(" ", 1)
            if len(before) == 2 and before[-1].strip(" ,.;:").lower() in AUXILIARIES:
                continue  # "what data does it get" — korrekt engelsk
            f.append(
                f"R2 {rel}: {m.group(1)} {m.group(2)} … — {prose[max(0, m.start() - 45):m.end() + 25].strip()!r}"
            )
    return f


def pages():
    return {
        p.relative_to(SITE).as_posix(): p.read_text(errors="replace")
        for p in sorted(SITE.rglob("*.html"))
        if "_partials" not in p.parts
    }


def selftest():
    """Bevis at porten kan fejle. Fire muteringer mod de rigtige filer/tabeller."""
    real_pages = pages()
    real_hype = load_hype()
    cases = []

    def case(name, hype=None, mutate=None):
        h = real_hype if hype is None else hype
        p = real_pages
        if mutate:
            p = mutate(dict(real_pages))
        cases.append((name, table_findings(h) + tree_findings(p)))

    # R1: flad tabel igen — den fejl der fandtes 28/9.
    flat = [(re.compile(r"\bUnlock(s|ed)?\b"), "Get")]
    case("R1 grundformen tilbage i tabellen", hype=flat)
    # R1b: et nyt bøjet ord porten ikke kender.
    case("R1 ukendt bøjning i tabellen",
         hype=real_hype + [(re.compile(r"\bDisrupt(s|ed)?\b"), "Improve")])
    # R1c: en bøjning der mangler — mønsteret kender kun "s", porten kræver "ed".
    case("R1 manglende bøjning i mønsteret",
         hype=[(re.compile(r"\bunlock(s)?\b"), lambda m: "gets" if m.group(1) else "get")]
         + [(p_, r_) for p_, r_ in real_hype if "nlock" not in p_.pattern])
    # R2: den fejl der allerede la i den publicerede tekst.
    #
    # Mutationen var engang `replace("unlocks", "get", 1)` paa /api/. Da
    # bøjningsrettelsen i iteration 109 skrev "unlocks" til "gets", holdt den
    # op at virke **uden at gøre noget** — `.replace()` giver ikke en fejl,
    # den giver det uændrede sætning tilbage, og porten fandt korrekt intet.
    # Selftesten sagde så "blev ikke fanget" for en case der ikke længere
    # testede noget. Derfor indsættes den brudte sætning nu, og case'en
    # kræver *også* at mutationen faktisk ændrede siden: en no-op må aldrig
    # kunne passere som en fanget fejl.
    def break_third_person(p):
        out = dict(p)
        text = p["api/index.html"]
        mutated = text.replace("<main", "<p>It get the starters.</p>\n<main", 1)
        assert mutated != text, "mutationen ændrede ikke /api/ — casen tester ingenting"
        out["api/index.html"] = mutated
        return out

    case("R2 tredjeperson med grundform", mutate=break_third_person)
    # R2b: "does it get" er korrekt engelsk og maa ikke give en find. Siden
    # med sætningen laeses fra repoet, ikke skrives i testen.
    correct = {k: v for k, v in real_pages.items() if "does it get" in prose_of(v)}
    if correct:
        cases.append(("R2b 'does it get' er ikke en fejl", tree_findings(correct)))

    passed = 0
    for name, found in cases:
        if name.startswith("R2b"):
            ok = not found
        else:
            ok = bool(found)
        if ok:
            passed += 1
        else:
            print(f"SELFTEST FEJLT: {name} blev ikke fanget")
    print(f"SELFTEST {'GRØN' if passed == len(cases) else 'RØD'} — {passed}/{len(cases)} negative cases fanges")
    return 0 if passed == len(cases) else 1


def main():
    hype = load_hype()
    all_pages = pages()
    f = table_findings(hype) + tree_findings(all_pages)
    verbs = sum(1 for pat, _ in hype if parse_pattern(pat))
    print(f"HYPE-tabel: {len(hype)} poster, {verbs} med boejning — {len(all_pages)} sider laest")
    if not f:
        print("TIDSFORMER GRØN — hver bøjning overlever renseren, og ingen side har en tredjeperson med grundform.")
        return 0
    for line in f:
        print(f"FEJL {line}")
    print(f"\n{len(f)} HYPE-tidsform-fund")
    return 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
