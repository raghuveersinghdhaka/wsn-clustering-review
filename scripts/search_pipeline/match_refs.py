"""Match the manuscript's reference list against the de-duplicated database records.

Usage: python match_refs.py <refs.bib> <work dir>
Writes <work dir>/reference_match.csv: one row per bib entry with role (primary/background),
match method, matched cluster and the databases that returned it.
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from bibparse import parse_bib, clean_bib, norm_doi, norm_title

csv.field_size_limit(10**9)
BIB, D = sys.argv[1], sys.argv[2]
bib = parse_bib(open(BIB, encoding="utf-8").read())
U = list(csv.DictReader(open(os.path.join(D, "records_unique.csv"), encoding="utf-8")))
I = list(csv.DictReader(open(os.path.join(D, "records_identified.csv"), encoding="utf-8")))
src_of = {}
for r in I:
    src_of.setdefault(r["cluster"], set()).add(r["source"])

bydoi, bytitle = {}, {}
for r in I:
    if r["doi"]:
        bydoi.setdefault(r["doi"], r["cluster"])
    bytitle.setdefault(r["ntitle"], r["cluster"])

rows = []
for et, key, f in bib:
    t = clean_bib(f.get("title", ""))
    nt = norm_title(t)
    doi = norm_doi(f.get("doi", ""))
    how, cl = "", ""
    if doi and doi in bydoi:
        how, cl = "DOI", bydoi[doi]
    elif nt in bytitle:
        # same normalized title; accepted only with a publication year at most two years apart
        ys = [int(r["year_used"]) for r in I if r["cluster"] == bytitle[nt]]
        if any(abs(y - int(f.get("year", "0") or 0)) <= 2 for y in ys):
            how, cl = "title (exact)", bytitle[nt]
    rows.append(dict(key=key, year=f.get("year", ""), title=t, doi=doi, match=how, cluster=cl,
                     databases="; ".join(sorted(src_of.get(cl, []))) if cl else ""))
with open(os.path.join(D, "reference_match.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print("entries", len(rows), "matched", sum(1 for r in rows if r["match"]))
for r in rows:
    print(f"{r['key']:22s} {r['year']:5s} {r['match'][:24]:24s} {r['databases'][:60]:60s} | {r['title'][:70]}")
