"""Shared parsing helpers: DOI and title normalization, a minimal BibTeX reader."""
import csv, html, re, unicodedata

def norm_doi(d):
    if not d:
        return ""
    d = d.strip().lower()
    d = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", d)
    d = d.replace("doi:", "").strip().rstrip(".")
    return d if d.startswith("10.") else ""

def norm_title(t):
    t = html.unescape(t or "")
    t = re.sub(r"<[^>]+>", " ", t)
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower().replace("&amp;", " and ").replace("&", " and ")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

# minimal BibTeX reader (brace-balanced field values)
def parse_bib(text):
    entries = []
    i = 0
    while True:
        m = re.compile(r"@(\w+)\s*\{", re.S).search(text, i)
        if not m:
            break
        etype = m.group(1).lower()
        j = m.end()
        depth = 1
        k = j
        while k < len(text) and depth:
            if text[k] == "{":
                depth += 1
            elif text[k] == "}":
                depth -= 1
            k += 1
        body = text[j:k - 1]
        i = k
        key, _, rest = body.partition(",")
        fields = {}
        p = 0
        fre = re.compile(r"\s*([A-Za-z_\-]+)\s*=\s*", re.S)
        while p < len(rest):
            fm = fre.match(rest, p)
            if not fm:
                p += 1
                continue
            name = fm.group(1).lower()
            q = fm.end()
            if q < len(rest) and rest[q] == "{":
                d = 1; r = q + 1
                while r < len(rest) and d:
                    if rest[r] == "{": d += 1
                    elif rest[r] == "}": d -= 1
                    r += 1
                val = rest[q + 1:r - 1]
            elif q < len(rest) and rest[q] == '"':
                r = rest.find('"', q + 1) + 1
                val = rest[q + 1:r - 1]
            else:
                r = q
                while r < len(rest) and rest[r] not in ",\n":
                    r += 1
                val = rest[q:r]
            fields.setdefault(name, val.strip())
            p = r
            while p < len(rest) and rest[p] in ", \t\r\n":
                p += 1
        entries.append((etype, key.strip(), fields))
    return entries

def clean_bib(s):
    s = s or ""
    s = re.sub(r"[{}]", "", s)
    s = s.replace("\\&", "&")
    return re.sub(r"\s+", " ", s).strip()

