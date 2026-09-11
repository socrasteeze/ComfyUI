"""Mechanical pass over dryrun.json. Flags only what is objectively checkable.

Semantic criteria (subject binding, reference roles, clarification quality) are
graded by reading, not here.
"""
import json
import os
import re

import sys
here = os.path.dirname(os.path.abspath(__file__))
name = sys.argv[1] if len(sys.argv) > 1 else "dryrun.json"
path = name if os.path.exists(name) else os.path.join(here, "..", "results", name)
data = json.load(open(path, encoding="utf-8"))

FENCE = re.compile(r"```")
PREAMBLE = re.compile(r"^\s*(here('s| is)|sure|certainly|okay|of course|i['’]ve|"
                      r"below is|this (prompt|is))", re.I)
HEADING = re.compile(r"^\s*#{1,6}\s", re.M)
WRAPQUOTE = re.compile(r'^\s*".*"\s*$', re.S)
NEGSECTION = re.compile(r"^\s*NEGATIVE:", re.M)
PROMPTSECTION = re.compile(r"^\s*PROMPT:", re.M)
NOTES = re.compile(r"^\s*NOTES:", re.M)
DECOR = re.compile(
    r"\b(cinematic|dramatic lighting|bokeh|depth of field|8k|4k|ultra[- ]detailed|"
    r"photorealistic|hyperreal|masterpiece|best quality|award[- ]winning|35mm|50mm|"
    r"85mm|dslr|golden hour|volumetric|rim light|intricate|highly detailed|"
    r"trending on artstation|score_\d)\b", re.I)

# Cases where an ordinary bare positive prompt is the ONLY correct shape.
ORDINARY = {"1 faithful style", "14a clean default", "2 scoped edit",
            "11 subject binding", "13 everyday edit", "8a anima aesthetic",
            "7a deliberate artifacts", "5a multi-view sheet"}
# Cases where a negative section is legitimately requested.
NEGOK = {"7b artifacts + negative", "14b default + negative", "8b anima turbo+neg"}

rows = []
for r in data["results"]:
    case, prof, replies = r["case"], r["profile"], r["replies"]
    out = replies[-1]
    flags = []
    if out.startswith("<<ERROR"):
        flags.append("ERROR")
    elif out.lstrip().startswith("NEEDS INPUT"):
        # Fatal for a node: this string would reach the encoder as the prompt.
        flags.append("NEEDS-INPUT")
    elif out.lstrip().startswith("CONFLICT:"):
        # Correct behaviour on case 6; wrong anywhere else.
        if case != "6 conflicting framing":
            flags.append("SPURIOUS-CONFLICT")
    else:
        if case == "6 conflicting framing":
            flags.append("NO-CONFLICT-DETECTED")
        # Subject-count tags invented where the request never stated a count.
        if case not in ("11 subject binding",):
            inv = sorted({m.group(0).lower() for m in
                          re.finditer(r"\b(1girl|1boy|solo|2girls|2boys)\b", out, re.I)})
            # "solo" is stated, not invented, when the request says one subject.
            req = " ".join(t.lower() for t in r.get("turns", [])) if "turns" in r else ""
            stated_one = case.startswith(("1 ", "14")) or "one output image" in req
            if stated_one:
                inv = [t for t in inv if t != "solo"]
            if inv:
                flags.append("INVENTED-SUBJECT:" + ",".join(inv))
        # Wording lifted from the pack's own worked examples.
        for leak in ("short black hair", "green eyes", "black leather jacket",
                     "red hair, black hair, shaking hands", "blue teapot, wooden table, watercolor"):
            if case.startswith("8") and "teapot" in leak:
                continue  # case 8 legitimately asks for the teapot
            if leak in out.lower():
                flags.append("EXAMPLE-LEAK")
                break
        if case in ORDINARY:
            if FENCE.search(out):
                flags.append("FENCE")
            if PREAMBLE.search(out):
                flags.append("PREAMBLE")
            if HEADING.search(out):
                flags.append("HEADING")
            if WRAPQUOTE.match(out):
                flags.append("WRAPPED-QUOTES")
            if NEGSECTION.search(out):
                flags.append("UNASKED-NEGATIVE")
            if NOTES.search(out):
                flags.append("NOTES-ON-ORDINARY")
            d = sorted({m.group(0).lower() for m in DECOR.finditer(out)})
            if d:
                flags.append("DECOR:" + ",".join(d))
        if case in NEGOK and not NEGSECTION.search(out) and "negative" not in out.lower():
            flags.append("NO-NEGATIVE-HANDLING")
        if case == "9 runtime/lora":
            s = re.sub(r"^```\w*\s*|\s*```$", "", out.strip())
            if FENCE.search(out):
                flags.append("JSON-FENCED")
            try:
                o = json.loads(s)
                if "myStyleToken" not in (o.get("positive_prompt") or ""):
                    flags.append("TRIGGER-NOT-IN-POSITIVE")
                if not o.get("parameters"):
                    flags.append("NO-PARAMS")
                if not o.get("notes"):
                    flags.append("NO-NOTES")
            except Exception:
                flags.append("INVALID-JSON")
    rows.append((case, prof, len(out), flags))

by_case = {}
for case, prof, n, flags in rows:
    by_case.setdefault(case, []).append((prof, n, flags))

clean = sum(1 for *_, f in rows if not f)
print(f"model: {data['model']}")
print(f"{clean}/{len(rows)} mechanically clean\n")
for case in sorted(by_case):
    print(f"== {case}")
    for prof, n, flags in by_case[case]:
        mark = "ok  " if not flags else "FAIL"
        print(f"   {mark} {prof:<12} {n:>5}ch  {' '.join(flags)}")
