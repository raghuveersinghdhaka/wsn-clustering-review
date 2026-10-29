"""Title/abstract/keyword screening of the de-duplicated records by fixed rules.

Usage: python screen.py <work dir>
Reads <work dir>/records_unique.csv and <work dir>/reference_match.csv; writes
  <work dir>/screening_decisions.csv   one row per unique record: decision, rule, evidence base flag
  <work dir>/screening_counts.json
The rules implement the title/abstract criteria of Table 4 (I1, I2, E1, E3):
  S1 (E3) the record is not a paper: front or back matter, a whole proceedings volume, a thesis
          or dissertation, or a citation-only entry.
  S2 (I2, E3) the title is not in English.
  S3 (I1, E1) the export carries a full abstract and none of title, abstract and keywords names a
          sensor or IoT network.
  S4 (I1, E1) the export carries a full abstract and none of title, abstract and keywords names
          clustering or a cluster-based structure.
  S3 and S4 are not applied to SpringerLink, Taylor & Francis Online and Google Scholar records
  (no abstract, or a snippet only): their searches matched the concept blocks in the full text
  or in all fields, so a title alone cannot show that a record fails them.
"""
import csv, json, os, re, sys
from collections import Counter

csv.field_size_limit(10**9)
D = sys.argv[1]
U = list(csv.DictReader(open(os.path.join(D, "records_unique.csv"), encoding="utf-8")))
M = list(csv.DictReader(open(os.path.join(D, "reference_match.csv"), encoding="utf-8")))
in_review = {m["cluster"]: m["key"] for m in M if m["cluster"]}

FRONT = re.compile(r"^(front cover|back cover|cover|title page|table of contents|contents|copyright( page| notice)?|"
                   r"preface|foreword|editorial|guest editorial|index|author index|subject index|keynote.*|"
                   r"message from .*|welcome .*|committees?|organizing committee|program committee|"
                   r"conference program|front matter|back matter|masthead|reviewers|list of reviewers|"
                   r"\[?front matter\]?|proceedings.*)$")
THESIS = re.compile(r"\b(thesis|dissertation|ph\.? ?d|m\.? ?tech|master'?s|doctoral)\b", re.I)
NET = re.compile(r"sensor|\bwsns?\b|\biot\b|internet of things|\bm2m\b|machine[- ]to[- ]machine|"
                 r"\bad[- ]hoc\b|\bmanets?\b|\bvanets?\b|\bfanets?\b|\buavs?\b|body area|\bwbans?\b|"
                 r"\buwsns?\b", re.I)
CLU = re.compile(r"cluster|\bleach\b|leach[- ]|\bheed\b|\bpegasis\b|\bteen\b|\bapteen\b|\bdeec\b|\bsep\b|"
                 r"hierarch|cluster[- ]head|\bchs?\b|coalition", re.I)
EN_STOP = set("the of and in for a an to on with by from using based is are via its at as".split())
FOREIGN = set("de la le les des et para por con una uno los las del em do da dos das um uma und der die das "
              "mit fur für von zur zum sur dans pour une du au aux".split())

def not_english(title):
    t = title.strip()
    if not t:
        return False
    if sum(1 for c in t if ord(c) > 0x2FF) > 3:            # CJK, Cyrillic, Arabic ... scripts
        return True
    w = re.findall(r"[a-zà-ÿ]+", t.lower())
    fe, en = sum(1 for x in w if x in FOREIGN), sum(1 for x in w if x in EN_STOP)
    return fe >= 2 and fe > en

out, cnt = [], Counter()
for r in U:
    title = r["title"]; nt = r["ntitle"]; ab = (r["abstract"] or "") + " " + (r["keywords"] or "")
    src = r["sources"].split("; ")
    full_abstract = any(s in ("IEEE Xplore", "ACM Digital Library", "ScienceDirect", "Wiley Online Library")
                        for s in src) and len(r["abstract"] or "") > 200
    rule = ""
    if (FRONT.match(nt) or r["type"] in ("proceedings", "CITATION")
            or (r["source"] == "Google Scholar" and THESIS.search(r["venue"] + " " + title))):
        rule = "S1"
    elif not_english(title):
        rule = "S2"
    elif full_abstract and not NET.search(title + " " + ab):
        rule = "S3"
    elif full_abstract and not CLU.search(title + " " + ab):
        rule = "S4"
    dec = "excluded" if rule else "eligible"
    key = in_review.get(r["cluster"], "")
    cnt[rule or "eligible"] += 1
    out.append(dict(cluster=r["cluster"], sources=r["sources"], year=r["year_used"], doi=r["doi"],
                    title=title, decision=dec, rule=rule, in_review=key))

ev = [o for o in out if o["in_review"]]
res = dict(n_screened=len(out), n_excluded=sum(1 for o in out if o["decision"] == "excluded"),
           n_eligible=sum(1 for o in out if o["decision"] == "eligible"),
           excluded_by_rule={k: cnt[k] for k in ("S1", "S2", "S3", "S4")},
           review_works_among_records=len(ev),
           review_works_excluded_by_rules=[o["in_review"] for o in ev if o["decision"] == "excluded"])
res["eligible_not_in_review"] = res["n_eligible"] - sum(1 for o in ev if o["decision"] == "eligible")
json.dump(res, open(os.path.join(D, "screening_counts.json"), "w"), indent=1)
with open(os.path.join(D, "screening_decisions.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
print(json.dumps(res, indent=1))
