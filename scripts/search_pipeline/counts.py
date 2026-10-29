"""Consolidate the selection counts used in Sect. 3.2, Sect. 3.4, Table 3 and Fig. 4.

Usage: python counts.py <work dir> <directory of the data-extraction sheet>
Writes <work dir>/selection_counts.json.
"""
import csv, json, os, sys

D, EXTRACTION = sys.argv[1], sys.argv[2]
idc = json.load(open(os.path.join(D, "identification_counts.json"), encoding="utf-8"))
scr = json.load(open(os.path.join(D, "screening_counts.json"), encoding="utf-8"))
M = list(csv.DictReader(open(os.path.join(D, "reference_match.csv"), encoding="utf-8")))
dec = {r["cluster"]: r for r in csv.DictReader(open(os.path.join(D, "screening_decisions.csv"), encoding="utf-8"))}

primary = {r["ref_key"] for r in csv.DictReader(open(os.path.join(EXTRACTION, "data_extraction.csv"), encoding="utf-8-sig"))}
for r in csv.DictReader(open(os.path.join(EXTRACTION, "security_schemes.csv"), encoding="utf-8-sig")):
    primary |= {k.strip() for k in r["ref_key"].replace(";", ",").split(",")}
keys = [m["key"] for m in M]
found = {m["key"] for m in M if m["cluster"] and dec[m["cluster"]]["decision"] == "eligible"}
assert all(dec[m["cluster"]]["decision"] == "eligible" for m in M if m["cluster"])

n1 = idc["n_identified"]; n2 = idc["n_duplicates"]; n3 = idc["n_unique"]
n4 = scr["n_excluded"]; n5 = scr["n_eligible"]
in_db = len(found); n6 = n5 - in_db
out = dict(
    per_database=idc["per_database"], not_counted_by_date=idc["excluded_by_date"],
    taylor_francis=idc["taylor_francis"],
    n1_identified=n1, n2_duplicates=n2, n3_screened=n3, n4_excluded=n4, n5_eligible=n5,
    n6_not_assessed=n6, excluded_by_rule=scr["excluded_by_rule"],
    included_from_searches=in_db, included_outside_searches=len(keys) - in_db, included_total=len(keys),
    primary_total=len(primary & set(keys)), primary_from_searches=len(primary & found),
    background_total=len(set(keys) - primary), background_from_searches=len(found - primary),
)
out["primary_outside"] = out["primary_total"] - out["primary_from_searches"]
out["background_outside"] = out["background_total"] - out["background_from_searches"]
# consistency
assert n1 == sum(idc["per_database"].values())
assert n3 == n1 - n2 and n5 == n3 - n4 and n4 == sum(scr["excluded_by_rule"].values())
assert out["included_total"] == out["primary_total"] + out["background_total"] == len(keys)
assert in_db == out["primary_from_searches"] + out["background_from_searches"]
json.dump(out, open(os.path.join(D, "selection_counts.json"), "w", encoding="utf-8"), indent=1)
print(json.dumps(out, indent=1))
