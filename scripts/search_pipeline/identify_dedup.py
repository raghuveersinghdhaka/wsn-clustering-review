"""Identification and de-duplication of the database records (publication years 2002-2025).

Usage: python identify_dedup.py <work dir>
Reads <work dir>/records_all.csv (from load_records.py); writes
  <work dir>/records_identified.csv   records counted as identified, with year rule and cluster id
  <work dir>/records_unique.csv       one row per de-duplicated record (first occurrence kept)
  <work dir>/identification_counts.json
"""
import csv, json, os, re, sys, unicodedata
from collections import Counter, defaultdict

csv.field_size_limit(10**9)
D = sys.argv[1]
R = list(csv.DictReader(open(os.path.join(D, "records_all.csv"), encoding="utf-8")))

ORDER = ["IEEE Xplore", "ACM Digital Library", "ScienceDirect", "SpringerLink",
         "Taylor & Francis Online", "Wiley Online Library", "Google Scholar"]

def online_year(extra):
    m = re.search(r"(\d{4})$", extra.strip())
    return int(m.group(1)) if m else None

ident = []
excluded = Counter()
# Taylor & Francis: the three concept blocks were run as separate searches; block 3 (13,403 hits)
# could be exported only up to 2,000 records, so the identified set is block 1 AND block 2 (both
# complete), intersected by DOI.  Block-3 membership is recorded for information.
tf = defaultdict(dict)
for r in R:
    if r["source"].startswith("Taylor"):
        b = r["file"].rsplit("-", 1)[1][0]
        tf[b][r["doi"]] = r
tf_ids = set(tf["1"]) & set(tf["2"])
for r in R:
    s = r["source"]
    if s.startswith("Taylor"):
        if not r["file"].endswith("-1.csv") or r["doi"] not in tf_ids:
            continue
        y = online_year(r["extra"])          # T&F date filter is on the online publication date
        r["year_used"], r["year_rule"] = y, "online date"
        r["tf_block3_export"] = "yes" if r["doi"] in tf["3"] else "no"
    elif s == "Google Scholar":
        batch = int(re.search(r"\((\d{4})\)", r["file"]).group(1))
        if r["year"]:
            r["year_used"], r["year_rule"] = int(r["year"]), "record year"
        elif batch != 2024:                  # single-year query (as_ylo = as_yhi = batch year)
            r["year_used"], r["year_rule"] = batch, "single-year query"
        else:                                # 2024 batch ran with as_yhi = 2099: year unknown
            r["year_used"], r["year_rule"] = None, "open-ended query, no year"
    else:
        r["year_used"], r["year_rule"] = int(r["year"]), "record year"
    y = r["year_used"]
    if y is None or y > 2025 or y < 2002:
        excluded[(s, "year outside 2002-2025 or unknown")] += 1
        continue
    # date threshold: no date of the export record after 31 December 2025
    if r.get("date_max_year") and int(r["date_max_year"]) > 2025:
        excluded[(s, "dated after 31 December 2025")] += 1
        continue
    ident.append(r)

# within- and across-database de-duplication: union-find on DOI and normalized title
parent = list(range(len(ident)))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i
def union(a, b):
    a, b = find(a), find(b)
    if a != b:
        parent[max(a, b)] = min(a, b)
# Rule 1: the same DOI is the same record.
first = {}
for i, r in enumerate(ident):
    if r["doi"]:
        k = r["doi"]
        if k in first:
            union(i, first[k])
        else:
            first[k] = i
# Rule 2: the same normalized title is the same record only if (a) the two records do not carry
# two different DOIs (two DOIs are two publications, e.g. a conference and a journal version),
# (b) the author lists share a name token, and (c) the years differ by at most 3 (online vs issue year).
def name_tokens(a):
    a = unicodedata.normalize("NFKD", a or "")
    a = "".join(ch for ch in a if not unicodedata.combining(ch))   # accents removed
    a = re.sub(r"([a-z])([A-Z])", r"\1 \2", a)                      # SpringerLink concatenates author names
    return {t for t in re.findall(r"[^\W\d_]{2,}", a.lower())} - {"and", "others"}   # letters of any script
# DOIs held by each group: a group never holds two different DOIs (checked on the whole group,
# not only on the pair, so that a record without a DOI cannot join two publications)
gdoi = {i: ({r["doi"]} if r["doi"] else set()) for i, r in enumerate(ident)}
for i in range(len(ident)):
    gdoi.setdefault(find(i), set()).update(gdoi[i])
bytitle = defaultdict(list)
for i, r in enumerate(ident):
    # a title without Latin letters or digits is compared by its words in any script
    tk = r["ntitle"] or " ".join(re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", r["title"]).casefold()))
    if len(tk) >= 20:
        bytitle[tk].append(i)
for t, idx in bytitle.items():
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            i, j = idx[a], idx[b]
            ri, rj = ident[i], ident[j]
            if abs(int(ri["year_used"]) - int(rj["year_used"])) > 3:
                continue
            if not (name_tokens(ri["authors"]) & name_tokens(rj["authors"])):
                continue
            gi, gj = find(i), find(j)
            if gi == gj or len(gdoi[gi] | gdoi[gj]) > 1:
                continue
            union(i, j)
            gdoi[find(i)] = gdoi[gi] | gdoi[gj]
clusters = defaultdict(list)
for i in range(len(ident)):
    clusters[find(i)].append(i)
for cid, members in clusters.items():
    for j, i in enumerate(sorted(members)):
        ident[i]["cluster"] = cid + 1
        ident[i]["kept"] = "yes" if j == 0 else "no"   # first in source order (ORDER, then file order)

per_db = Counter(r["source"] for r in ident)
within = Counter()
for cid, members in clusters.items():
    c = Counter(ident[i]["source"] for i in members)
    for s, v in c.items():
        within[s] += v - 1
n1 = len(ident)
n_unique = len(clusters)
out = dict(
    per_database={s: per_db[s] for s in ORDER},
    excluded_by_date={s: sum(v for k, v in excluded.items() if k[0] == s) for s in ORDER},
    taylor_francis=dict(block1=len(tf["1"]), block2=len(tf["2"]), block3_exported=len(tf["3"]),
                        block1_and_2=len(tf_ids),
                        block1_and_2_in_block3_export=sum(1 for d in tf_ids if d in tf["3"])),
    n_identified=n1, n_unique=n_unique, n_duplicates=n1 - n_unique,
    duplicates_within_same_database={s: within[s] for s in ORDER},
    clusters_spanning_databases=sum(1 for m in clusters.values() if len({ident[i]["source"] for i in m}) > 1),
)
json.dump(out, open(os.path.join(D, "identification_counts.json"), "w"), indent=1)
print(json.dumps(out, indent=1))

keys = ["rid", "source", "file", "title", "ntitle", "year", "year_used", "year_rule", "doi", "authors",
        "venue", "type", "extra", "cluster", "kept", "keywords", "abstract"]
with open(os.path.join(D, "records_identified.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
    w.writeheader()
    for r in ident:
        w.writerow(r)
with open(os.path.join(D, "records_unique.csv"), "w", encoding="utf-8", newline="") as f:
    keys2 = keys + ["sources"]
    w = csv.DictWriter(f, fieldnames=keys2, extrasaction="ignore")
    w.writeheader()
    for cid, members in sorted(clusters.items()):
        r = dict(ident[sorted(members)[0]])
        r["sources"] = "; ".join(sorted({ident[i]["source"] for i in members}, key=ORDER.index))
        # carry the longest abstract of the cluster for screening
        r["abstract"] = max((ident[i]["abstract"] for i in members), key=len)
        r["keywords"] = "; ".join(sorted({ident[i]["keywords"] for i in members if ident[i]["keywords"]}))
        w.writerow(r)
