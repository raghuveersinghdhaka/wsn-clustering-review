# Clustering protocols in wireless sensor networks: review data and scripts

Data and scripts for the article *Comprehensive Review of Clustering Protocols in Wireless Sensor Networks
and Performance Trends* (R. S. Dhaka, M. Khurana and S. Lamba). They reproduce the search and selection
counts of the review, its ordinal-synthesis figure and its analytical trade-off between fixed and periodic
cluster-head election.

## Contents

```
data/
  search/        search_strings.csv            database-specific search strings, fields, filters and record counts (Table 3)
                 search_records.csv            one row per identified record: duplicate group and screening decision
                 reference_list_vs_searches.csv  the included works and the searches that returned them
                 README_search.txt             description of every column
  extraction/    data_extraction.csv           structured data-extraction sheet, one row per primary study
                 security_schemes.csv          one row per security-enhanced scheme
                 README_extraction.txt         description of the columns
  references/    refs.bib                      reference list of the article
scripts/
  verify_counts.py                             recomputes every search and selection count from data/search
  make_fig_ordinal.py                          draws the ordinal-synthesis figure (Fig. 7) from data/extraction
  tradeoff_model.py                            computes Table 17 from Eqs. (4)-(6)
  search_pipeline/                             rebuilds data/search from the database exports
requirements.txt
```

| Item of the article | File or script |
|---|---|
| Search strings and records per database (Sect. 3.2, Table 3) | `data/search/search_strings.csv`; `scripts/verify_counts.py` |
| Selection flow (Sect. 3.4, Fig. 4) | `data/search/search_records.csv`, `data/search/reference_list_vs_searches.csv`; `scripts/verify_counts.py` |
| Extraction fields (Table 6); conditions, reported results and scores (Tables 7-15) | `data/extraction/data_extraction.csv` |
| Security-enhanced schemes (Table 21) | `data/extraction/security_schemes.csv` |
| Ordinal synthesis (Fig. 7) | `scripts/make_fig_ordinal.py` |
| Fixed versus periodic election (Sect. 5.7, Table 17) | `scripts/tradeoff_model.py` |

## Quick start

Python 3.8 or later. `verify_counts.py` and `tradeoff_model.py` need only the standard library;
`make_fig_ordinal.py` needs matplotlib.

```
python scripts/verify_counts.py          # prints each count with the value printed in the article
python scripts/tradeoff_model.py         # prints the rows of Table 17
pip install -r requirements.txt
python scripts/make_fig_ordinal.py       # writes output/fig_ordinal.pdf
```

`verify_counts.py` ends with `all counts agree` and exit code 0 when every count matches the article.

## Rebuilding the search records from the database exports

`data/search/search_records.csv` records, for each of the 5873 identified records, its duplicate group and
the screening rule that applied (S1 not a paper, S2 title not in English, S3 no sensor or IoT network named,
S4 no clustering or cluster-based structure named). The rules are applied to titles, abstracts and keywords. The
database exports carry the publishers' abstracts, so they are not included here. They can be obtained by
running the strings of `data/search/search_strings.csv` in each database with the stated fields and filters
and exporting all results (IEEE Xplore and SpringerLink as CSV; ACM Digital Library, ScienceDirect and Wiley
Online Library as BibTeX; Taylor & Francis Online as CSV, one file per search; Google Scholar as CSV, one file
per publication year). Every record counted was available by 31 December 2025; a search run after that date
may also return records added since.

With the exports in one folder per database (layout in the header of
`scripts/search_pipeline/run_pipeline.py`):

```
python scripts/search_pipeline/run_pipeline.py <exports folder>
```

The script runs the identification, de-duplication, screening and matching steps, writes the two record files to
`output/search_pipeline/records/` and reports whether each is identical to the file in `data/search`.

## Notes

- NR in the extraction sheet means not reported in the source, or not retrievable where only the abstract or
  the title and index record of a study was available. Text in quotation marks is in the words of the source.
- The ordinal scores S_E and S_T compare each study with its own strongest baseline under its own conditions
  (rubric of Sect. 7.1 of the article), and they do not rank protocols across studies.
