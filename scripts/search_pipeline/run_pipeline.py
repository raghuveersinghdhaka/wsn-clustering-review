"""Rebuild the search records (data/search) from the database exports and compare them with the files in data/search.

Usage:  python scripts/search_pipeline/run_pipeline.py <exports dir> [work dir]

<exports dir> holds one sub-folder per database, with the export files of the searches of Table 3:
  IEEE Xplore/*.csv             ACM Digital Library/*.bib      Science Direct/*.bib
  Springer Link/*.csv           Wiley Online Library/*.bib
  Taylor & Francis/*-1.csv, *-2.csv, *-3.csv   (the three concept searches, in this order)
  Google Scholar/*(YYYY).csv    (one file per publication year, YYYY = 2002 ... 2025)
Steps: load_records -> identify_dedup -> match_refs -> screen -> counts -> write_search_records.
Needs only the Python standard library.
"""
import filecmp
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
if len(sys.argv) < 2:
    sys.exit(__doc__)
exports = Path(sys.argv[1])
work = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "output" / "search_pipeline"
out = work / "records"
for sub in ("IEEE Xplore", "ACM Digital Library", "Science Direct", "Springer Link", "Taylor & Francis",
            "Wiley Online Library", "Google Scholar"):
    if not (exports / sub).is_dir():
        sys.exit(f"missing export folder: {exports / sub}")
work.mkdir(parents=True, exist_ok=True)
bib = ROOT / "data" / "references" / "refs.bib"
extraction = ROOT / "data" / "extraction"


def step(script, *args):
    print(f"running {script}", flush=True)
    subprocess.run([sys.executable, str(HERE / script), *map(str, args)], check=True,
                   stdout=subprocess.DEVNULL if script in ("load_records.py", "match_refs.py") else None)


step("load_records.py", exports, work)
step("identify_dedup.py", work)
step("match_refs.py", bib, work)
step("screen.py", work)
step("counts.py", work, extraction)
step("write_search_records.py", work, extraction, out)
same = True
for f in ("search_records.csv", "reference_list_vs_searches.csv"):
    eq = filecmp.cmp(out / f, ROOT / "data" / "search" / f, shallow=False)
    same &= eq
    print(f"{'identical' if eq else 'DIFFERENT'}: {f}")
sys.exit(0 if same else 1)
