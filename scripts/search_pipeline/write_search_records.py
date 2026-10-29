"""Write the search records (de-duplication, screening decisions) and the reference list against the searches.

Usage: python write_search_records.py <work dir> <directory of the data-extraction sheet> <out dir>
No abstracts are written (they belong to the publishers); titles, years and DOIs only.
"""
import csv, json, os, re, sys

csv.field_size_limit(10**9)
D, EXTRACTION, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
I = list(csv.DictReader(open(os.path.join(D, "records_identified.csv"), encoding="utf-8")))
A = list(csv.DictReader(open(os.path.join(D, "records_all.csv"), encoding="utf-8")))
dec = {r["cluster"]: r for r in csv.DictReader(open(os.path.join(D, "screening_decisions.csv"), encoding="utf-8"))}
M = list(csv.DictReader(open(os.path.join(D, "reference_match.csv"), encoding="utf-8")))
c = json.load(open(os.path.join(D, "selection_counts.json"), encoding="utf-8"))
primary = {r["ref_key"] for r in csv.DictReader(open(os.path.join(EXTRACTION, "data_extraction.csv"), encoding="utf-8-sig"))}
for r in csv.DictReader(open(os.path.join(EXTRACTION, "security_schemes.csv"), encoding="utf-8-sig")):
    primary |= {k.strip() for k in r["ref_key"].replace(";", ",").split(",")}
key_of = {m["cluster"]: m["key"] for m in M if m["cluster"]}
tf3 = {r["doi"] for r in A if r["source"].startswith("Taylor") and r["file"].endswith("-3.csv")}

# each export is named by its database and number (file-name order); Taylor & Francis Online by search, Google
# Scholar by the publication year of its query
def label(r):
    if r["source"].startswith("Taylor"):
        return "Taylor & Francis Online, search " + r["file"].rsplit("-", 1)[1][0]
    if r["source"] == "Google Scholar":
        return "Google Scholar, query for " + re.search(r"\((\d{4})\)", r["file"]).group(1)
    files = sorted({x["file"] for x in A if x["source"] == r["source"]})
    return f"{r['source']}, export {files.index(r['file']) + 1:02d}"


RULE = {"S1": "S1 not a paper", "S2": "S2 title not in English", "S3": "S3 no sensor or IoT network",
        "S4": "S4 no clustering or cluster-based structure"}
rows = []
for n, r in enumerate(I, 1):
    d = dec[r["cluster"]]
    first = r["kept"] == "yes"
    rows.append({
        "record_no": n, "database": r["source"], "export": label(r), "title": r["title"],
        "year": r["year_used"], "year_basis": r["year_rule"], "doi": r["doi"],
        "duplicate_group": r["cluster"], "screened": "yes" if first else "no (duplicate)",
        "screening_result": (("excluded: " + RULE[d["rule"]]) if d["rule"] else "eligible") if first else "",
        "in_evidence_base": key_of.get(r["cluster"], "") if first else "",
        "tf_in_search3_export": ("yes" if r["doi"] in tf3 else "no") if r["source"].startswith("Taylor") else "",
    })
with open(os.path.join(OUT, "search_records.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

ref_rows = []
for m in M:
    ref_rows.append({"reference_key": m["key"], "role": "primary study" if m["key"] in primary else "background",
                     "title": m["title"], "year": m["year"], "doi": m["doi"],
                     "returned_by_searches": "yes" if m["cluster"] else "no",
                     "databases": m["databases"], "duplicate_group": m["cluster"],
                     "match": m["match"]})
with open(os.path.join(OUT, "reference_list_vs_searches.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(ref_rows[0]))
    w.writeheader()
    w.writerows(ref_rows)

# consistency of the files with the printed counts
assert len(rows) == c["n1_identified"]
assert sum(1 for x in rows if x["screened"] == "yes") == c["n3_screened"]
assert sum(1 for x in rows if x["screening_result"].startswith("excluded")) == c["n4_excluded"]
assert sum(1 for x in rows if x["screening_result"] == "eligible") == c["n5_eligible"]
assert sum(1 for x in rows if x["in_evidence_base"]) == c["included_from_searches"]
assert sum(1 for x in ref_rows if x["returned_by_searches"] == "yes") == c["included_from_searches"]
for db, n in c["per_database"].items():
    assert sum(1 for x in rows if x["database"] == db) == n
print("search records written:", len(rows), "records,", len(ref_rows), "references")
