"""Load the seven database exports into one record table.

Usage: python load_records.py <exports dir> <work dir>
Writes <work dir>/records_all.csv (one row per exported record, source file kept)
and prints per-source counts. date_max_year is the latest year among the dates of the export record
(publication or volume year, online date, date added to the database).
"""
import csv, glob, os, re, sys
from collections import Counter, defaultdict

csv.field_size_limit(10**9)
SRC_DIR, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bibparse import norm_doi, norm_title, read_csv, parse_bib, clean_bib

rows = []
def add(source, sfile, title, year, doi, authors="", venue="", abstract="", rtype="", extra="", keywords="", dates=()):
    try:
        y = int(str(year).strip()[:4])
    except Exception:
        y = None
    ys = [y] + [int(m) for d in dates for m in re.findall(r"\b(?:19|20)\d\d\b", d or "")]
    ys = [v for v in ys if v]
    rows.append(dict(source=source, file=os.path.basename(sfile), title=clean_bib(title),
                     year=y, doi=norm_doi(doi), authors=clean_bib(authors), venue=clean_bib(venue),
                     abstract=clean_bib(abstract), keywords=clean_bib(keywords), type=rtype, extra=extra,
                     date_max_year=max(ys) if ys else ""))

# IEEE Xplore
for f in sorted(glob.glob(os.path.join(SRC_DIR, "IEEE Xplore", "*.csv"))):
    for r in read_csv(f):
        add("IEEE Xplore", f, r["Document Title"], r["Publication Year"], r["DOI"], r["Authors"],
            r["Publication Title"], r["Abstract"], r.get("Document Identifier", ""),
            keywords="; ".join(x for x in (r.get("Author Keywords", ""), r.get("IEEE Terms", "")) if x),
            dates=(r.get("Date Added To Xplore", ""), r.get("Online Date", "")))

# ACM Digital Library (BibTeX exports)
for f in sorted(glob.glob(os.path.join(SRC_DIR, "ACM Digital Library", "*.bib"))):
    for et, key, fl in parse_bib(open(f, encoding="utf-8-sig").read()):
        add("ACM Digital Library", f, fl.get("title"), fl.get("year"), fl.get("doi"), fl.get("author"),
            fl.get("booktitle") or fl.get("journal"), fl.get("abstract"), et, keywords=fl.get("keywords", ""))

# ScienceDirect
for f in sorted(glob.glob(os.path.join(SRC_DIR, "Science Direct", "*.bib"))):
    for et, key, fl in parse_bib(open(f, encoding="utf-8-sig").read()):
        add("ScienceDirect", f, fl.get("title"), fl.get("year"), fl.get("doi"), fl.get("author"),
            fl.get("journal") or fl.get("booktitle"), fl.get("abstract"), et, keywords=fl.get("keywords", ""))

# SpringerLink
for f in sorted(glob.glob(os.path.join(SRC_DIR, "Springer Link", "*.csv"))):
    for r in read_csv(f):
        add("SpringerLink", f, r["Item Title"], r["Publication Year"], r["Item DOI"], r["Authors"],
            r["Publication Title"], "", r["Content Type"])

# Taylor & Francis (three concept searches, combined later)
for f in sorted(glob.glob(os.path.join(SRC_DIR, "Taylor & Francis", "*.csv"))):
    for r in read_csv(f):
        add("Taylor & Francis Online", f, r["Article title"], r["Volume year"], r["DOI"], r["Authors"],
            r["Journal title"], "", "", r.get("Published online date", ""), dates=(r.get("Published online date", ""),))

# Wiley Online Library
for f in sorted(glob.glob(os.path.join(SRC_DIR, "Wiley Online Library", "*.bib"))):
    for et, key, fl in parse_bib(open(f, encoding="utf-8-sig").read()):
        add("Wiley Online Library", f, fl.get("title"), fl.get("year"), fl.get("doi"), fl.get("author"),
            fl.get("journal"), fl.get("abstract"), et, keywords=fl.get("keywords", ""))

# Google Scholar (Publish or Perish CSV, one file per publication year)
for f in sorted(glob.glob(os.path.join(SRC_DIR, "Google Scholar", "*.csv"))):
    for r in read_csv(f):
        add("Google Scholar", f, r["Title"], r["Year"], r.get("DOI", ""), r["Authors"], r["Source"],
            r.get("Abstract", ""), r.get("Type", ""), r.get("QueryDate", ""))

for i, r in enumerate(rows):
    r["rid"] = i + 1
    r["ntitle"] = norm_title(r["title"])
keys = ["rid", "source", "file", "title", "ntitle", "year", "doi", "authors", "venue", "type", "extra", "date_max_year",
        "keywords", "abstract"]
with open(os.path.join(OUT, "records_all.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    for r in rows:
        w.writerow({k: r[k] for k in keys})

print("rows per source:", Counter(r["source"] for r in rows))
byfile = Counter((r["source"], r["file"]) for r in rows)
for k, v in sorted(byfile.items()):
    print(f"  {k[0]:24s} {k[1]:60s} {v}")
yrs = defaultdict(Counter)
for r in rows:
    yrs[r["source"]][r["year"]] += 1
for s, c in yrs.items():
    print(s, "years:", min((y for y in c if y), default=None), max((y for y in c if y), default=None),
          "missing year:", c.get(None, 0), ">2025:", sum(v for y, v in c.items() if y and y > 2025),
          "<2002:", sum(v for y, v in c.items() if y and y < 2002))
