"""Recompute every search and selection count of the review from the search records in data/search and compare it with
the value printed in the manuscript (Sect. 3.2, Table 3, Sect. 3.4 and Fig. 4).

Usage:  python scripts/verify_counts.py [data/search]
Needs only the Python standard library. Exit code 0 when every count agrees, 1 otherwise.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "search"
FILES = ["search_records.csv", "reference_list_vs_searches.csv"]
for f in FILES:
    if not (D / f).is_file():
        sys.exit(f"missing input file: {D / f}")


def rows(name):
    with open(D / name, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


R, W = rows(FILES[0]), rows(FILES[1])

PRINTED = {   # values printed in the manuscript
    "IEEE Xplore": 2460, "ACM Digital Library": 124, "ScienceDirect": 734, "SpringerLink": 1216,
    "Taylor & Francis Online": 41, "Wiley Online Library": 33, "Google Scholar": 1265,
    "records identified (n1)": 5873,
    "duplicates removed (n2)": 462, "records screened (n3)": 5411, "excluded by the rules (n4)": 54,
    "excluded by S1": 11, "excluded by S2": 11, "excluded by S3": 0, "excluded by S4": 32,
    "eligible records (n5)": 5357, "eligible records included in the review": 26,
    "eligible records not examined further (n6)": 5331,
    "included works not returned by the searches": 60, "included works": 86,
    "primary studies": 31, "background sources": 55,
    "primary studies from the searches": 12, "background sources from the searches": 14,
}

db = Counter(r["database"] for r in R)
screened = [r for r in R if r["screened"] == "yes"]
excl = [r for r in screened if r["screening_result"].startswith("excluded")]
rule = Counter(r["screening_result"].split(":", 1)[1].strip().split()[0] for r in excl)
elig = [r for r in screened if r["screening_result"] == "eligible"]
inc_db = [r for r in elig if r["in_evidence_base"]]
prim = [w for w in W if w["role"] == "primary study"]
back = [w for w in W if w["role"] == "background"]
yes = [w for w in W if w["returned_by_searches"] == "yes"]

COMPUTED = dict(db)
COMPUTED.update({
    "records identified (n1)": len(R),
    "duplicates removed (n2)": sum(1 for r in R if r["screened"] == "no (duplicate)"),
    "records screened (n3)": len(screened), "excluded by the rules (n4)": len(excl),
    "excluded by S1": rule["S1"], "excluded by S2": rule["S2"], "excluded by S3": rule["S3"], "excluded by S4": rule["S4"],
    "eligible records (n5)": len(elig), "eligible records included in the review": len(inc_db),
    "eligible records not examined further (n6)": len(elig) - len(inc_db),
    "included works not returned by the searches": len(W) - len(yes), "included works": len(W),
    "primary studies": len(prim), "background sources": len(back),
    "primary studies from the searches": sum(1 for w in prim if w["returned_by_searches"] == "yes"),
    "background sources from the searches": sum(1 for w in back if w["returned_by_searches"] == "yes"),
})

bad = 0
for k, v in PRINTED.items():
    ok = COMPUTED.get(k) == v
    bad += not ok
    print(f"{'ok  ' if ok else 'DIFF'} {k:48s} computed {COMPUTED.get(k)!s:>6}  printed {v:>6}")
# internal consistency of the two files
assert {r["in_evidence_base"] for r in inc_db} == {w["reference_key"] for w in yes}, "the search record files disagree"
print("all counts agree" if not bad else f"{bad} counts differ")
sys.exit(1 if bad else 0)
