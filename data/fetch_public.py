#!/usr/bin/env python3
"""Download Swiss federal law from Fedlex and split it into one record per article.

Output: data/public/fedlex.jsonl (already committed, so you only need to run this
to refresh the texts). Standard library only.

Source: https://www.fedlex.admin.ch (Publication Platform for Federal Law).
Swiss federal acts and ordinances are not protected by copyright
(Copyright Act, SR 231.1, Art. 5 para. 1 let. a). Every record keeps its source URL.

Usage: python3 data/fetch_public.py
"""
import html
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "public", "fedlex.jsonl")
BASE = "https://www.fedlex.admin.ch"

# eli path, consolidated version (date in force), SR number, abbreviation per language.
LAWS = [
    {"eli": "cc/2022/491", "version": "20250401", "sr": "235.1",
     "abbr": {"de": "DSG", "fr": "LPD", "it": "LPD", "en": "FADP"}},
    {"eli": "cc/2022/568", "version": "20251201", "sr": "235.11",
     "abbr": {"de": "DSV", "fr": "OPDo", "it": "OPDa", "en": "DPO"}},
    {"eli": "cc/1998/892_892_892", "version": "20261001", "sr": "955.0",
     "abbr": {"de": "GwG", "fr": "LBA", "it": "LRD", "en": "AMLA"}},
    {"eli": "cc/51/117_121_129", "version": "20261001", "sr": "952.0",
     "abbr": {"de": "BankG", "fr": "LB", "it": "LBCR"}},
    {"eli": "cc/2015/390", "version": "20230101", "sr": "955.033.0",
     "abbr": {"de": "GwV-FINMA", "fr": "OBA-FINMA", "it": "ORD-FINMA"}},
]


def file_url(eli, version, lang):
    slug = eli.replace("/", "-")
    return ("%s/filestore/fedlex.data.admin.ch/eli/%s/%s/%s/html/"
            "fedlex-data-admin-ch-eli-%s-%s-%s-html.html" % (BASE, eli, version, lang, slug, version, lang))


def text_of(fragment):
    """HTML fragment to plain text."""
    fragment = re.sub(r"(?is)<div class=\"footnotes\".*?</div>", " ", fragment)
    fragment = re.sub(r"(?is)<sup>\s*<a[^>]*>.*?</a>\s*</sup>", "", fragment)   # footnote marks
    fragment = re.sub(r"(?is)<sup>(.*?)</sup>", r"\1 ", fragment)               # paragraph numbers
    fragment = re.sub(r"(?i)</(p|dd|dt|dl|h\d|div|tr|li)>|<br\s*/?>", "\n", fragment)
    fragment = html.unescape(re.sub(r"<[^>]+>", "", fragment)).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in fragment.split("\n")]
    out, pending = [], ""
    for line in lines:                       # join "a." list letters with their text
        if not line:
            continue
        if re.fullmatch(r"(\d+|[a-z]{1,2}|[ivx]+)\.?(bis|ter|quater)?\.?", line) and not pending:
            pending = line
            continue
        out.append((pending + " " + line).strip() if pending else line)
        pending = ""
    return "\n".join(out)


def parse(page, law, lang):
    m = re.search(r'(?is)<h1 class="erlasstitel[^"]*">(.*?)</h1>', page)
    law_title = re.sub(r"\s+", " ", text_of(m.group(1))).strip() if m else law["abbr"][lang]
    abbr = law["abbr"][lang]
    for m in re.finditer(r'(?is)<article id="(art_[^"]+)">(.*?)</article>', page):
        anchor, inner = m.group(1), m.group(2)
        h = re.search(r"(?is)<h6[^>]*>(.*?)</h6>", inner)
        if not h:
            continue
        heading = re.sub(r"\s+", " ", text_of(h.group(1))).strip()
        num = re.match(r"(Art\.\s*\d+[a-z]*(?:bis|ter|quater|quinquies|sexies)?)", heading)
        section = re.sub(r"\s+", " ", num.group(1)) if num else heading[:20]
        body = text_of(inner[h.end():])
        if len(body) < 40 or body.lower().startswith(("aufgehoben", "abrog", "repealed")):
            continue
        yield {
            "id": "fedlex-%s-%s-%s" % (law["sr"], lang, anchor),
            "title": "%s %s" % (abbr, heading),
            "section": "%s %s" % (section, abbr),
            "law": abbr,
            "law_title": law_title,
            "sr_number": law["sr"],
            "language": lang,
            "doc_type": "law",
            "source": "fedlex",
            "source_url": "%s/eli/%s/%s#%s" % (BASE, law["eli"], lang, anchor),
            "valid_from": "%s-%s-%s" % (law["version"][:4], law["version"][4:6], law["version"][6:]),
            "is_current": True,
            "allowed_groups": ["all_staff"],
            "body": body,
        }


def main():
    records = []
    for law in LAWS:
        for lang in law["abbr"]:
            url = file_url(law["eli"], law["version"], lang)
            with urllib.request.urlopen(url, timeout=60) as resp:
                page = resp.read().decode("utf-8", errors="replace")
            if "<article" not in page or len(page) < 20000:
                sys.exit("No law text at %s (version may have changed)" % url)
            found = list(parse(page, law, lang))
            print("%-10s %s  %4d articles" % (law["abbr"][lang], lang, len(found)))
            records.extend(found)
            time.sleep(1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("Wrote %d records to %s" % (len(records), OUT))


if __name__ == "__main__":
    main()
