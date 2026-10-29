Records of the database searches, de-duplication and screening
"Comprehensive Review of Clustering Protocols in Wireless Sensor Networks and Performance Trends".

Searches (Sect. 3.2 and Table 3 of the manuscript): IEEE Xplore, ACM Digital Library, ScienceDirect, SpringerLink,
Taylor & Francis Online, Wiley Online Library and Google Scholar; publication years 2002-2025. Every record
counted was available by 31 December 2025.

search_records.csv : one row per identified record (5873 rows), in the order of the database exports.
  record_no            running number
  database             database that returned the record
  export               the export that holds the record: database and export number (in file-name order);
                       Taylor & Francis Online by search (always search 1: the identified records are those
                       of search 1 that search 2 also returned), Google Scholar by the publication year of its query
  title, doi           as exported (DOI normalized to lower case without the resolver prefix)
  year                 publication year used for the 2002-2025 window (basis in year_basis)
  year_basis           "record year"; "online date" (Taylor & Francis Online, whose date filter uses the online
                       publication date); "single-year query" (Google Scholar record without a year, returned by a
                       query limited to one publication year; the 2024 query had no upper year limit, and its records
                       without a year are not counted)
  duplicate_group      records sharing a number are duplicates of one record: same DOI, or same normalized title
                       (titles of at least 20 characters after normalization; titles and author names in
                       non-Latin scripts are compared in their original characters) when the two records share an author name,
                       are dated at most three years apart and the group does not come to hold two different DOIs
  screened             "yes" for the first record of each group (5411 records); "no (duplicate)" for the other 462
  screening_result     "eligible" or "excluded:" with the rule (title, abstract and keywords):
                         S1 not a paper (front or back matter, keynote abstract, proceedings volume, thesis)
                         S2 title not in English
                         S3 no sensor or IoT network named: none of the terms sensor, WSN, IoT, Internet of
                            Things, M2M, machine-to-machine, ad hoc, MANET, VANET, FANET, UAV, body area,
                            WBAN, UWSN in the title, abstract or keywords
                         S4 no clustering or cluster-based structure named: none of the terms cluster (any
                            form), LEACH, HEED, PEGASIS, TEEN, APTEEN, DEEC, SEP, hierarch- (any form),
                            cluster head, CH, coalition in the title, abstract or keywords
                       S3 and S4 were applied only to records whose export carries an abstract of more than
                       200 characters from IEEE Xplore, ACM Digital Library, ScienceDirect or Wiley Online
                       Library; the other records were screened by S1 and S2 only.
  in_evidence_base     reference key of the included work that this record represents (26 records)
  tf_in_search3_export Taylor & Francis Online only: whether the record is also in the export of the third
                       search (objective block), which holds 2000 of its 13,403 records

reference_list_vs_searches.csv : the 86 included works. Columns: reference_key (key in refs.bib), role
  (primary study or background), title, year, doi, returned_by_searches (yes/no), databases (those that
  returned the work), duplicate_group (in search_records.csv) and match (DOI, or title (exact): the
  exact normalized title with a publication year at most two years apart).

Counts (Fig. 4): identified 5873; duplicates removed 462; screened 5411; excluded by the rules 54
(S1 11, S2 11, S3 0, S4 32); eligible 5357, of which 26 are included works and 5331 were not examined further.
A further 60 included works are not among the records of the searches. They were identified on the official web
resources of their publishers. Included: 86 (31 primary studies, 55 background sources).
Abstracts are not included in this file.
