#!/usr/bin/env python3
"""
Sync publications from ORCID (+ Crossref) into a BibTeX file.

What this does:
  1. Fetches the list of "works" from the public ORCID API for ORCID_ID.
  2. For each work that has a DOI, fetches richer metadata from Crossref
     (full author list, journal/volume/pages, etc.).
  3. For works without a DOI, falls back to the (sparser) ORCID metadata.
  4. Writes all of this to bib/publications-orcid.bib (auto-generated,
     do not hand-edit — it gets overwritten every run).
  5. Concatenates bib/publications-manual.bib (hand-maintained) +
     bib/publications-orcid.bib into publications.bib at the repo root.

publications.bib is what Hugo Blox's "Import Publications From Bibtex"
step converts into pages under content/publications/.

Run manually with: python3 scripts/sync_orcid_publications.py
"""

import re
import sys
import time
import unicodedata
from pathlib import Path

import requests

ORCID_ID = "0000-0001-7044-9426"
SCHOLAR_ID = "T3OFN84AAAAJ"  # Google Scholar ID (used for reference; wordcloud built from Crossref data)
ORCID_API = f"https://pub.orcid.org/v3.0/{ORCID_ID}/works"
CROSSREF_API = "https://api.crossref.org/works/"

REPO_ROOT = Path(__file__).resolve().parent.parent
BIB_DIR = REPO_ROOT / "bib"
ORCID_BIB = BIB_DIR / "publications-orcid.bib"
MANUAL_BIB = BIB_DIR / "publications-manual.bib"
OUTPUT_BIB = REPO_ROOT / "publications.bib"
WORDCLOUD_OUT = REPO_ROOT / "static" / "media" / "wordcloud.png"

# Stop-words for the word cloud: generic academic filler + common English stops
STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "to", "for", "on", "with",
    "from", "by", "is", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "at", "as", "this", "that", "these",
    "those", "it", "its", "we", "our", "their", "between", "using", "based",
    "during", "study", "studies", "effect", "effects", "result", "results",
    "between", "within", "across", "toward", "via", "among",
    "however", "therefore", "also", "both", "may", "can", "no", "not",
    "high", "low", "new", "different", "related", "associated", "significant",
    "use", "used", "increased", "decreased", "compared", "including",
}

HEADERS_JSON = {"Accept": "application/json"}

# Map Crossref "type" -> BibTeX entry type
CROSSREF_TYPE_MAP = {
    "journal-article": "article",
    "proceedings-article": "inproceedings",
    "book-chapter": "incollection",
    "book": "book",
    "monograph": "book",
    "report": "techreport",
    "posted-content": "article",  # preprints
    "dataset": "misc",
}


def slugify(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "", text)
    return text.lower()


def get_orcid_works():
    """Return a list of (put_code, doi_or_None, fallback_summary_dict)."""
    resp = requests.get(ORCID_API, headers=HEADERS_JSON, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    works = []
    for group in data.get("group", []):
        summaries = group.get("work-summary", [])
        if not summaries:
            continue
        summary = summaries[0]

        doi = None
        for ext_id in group.get("external-ids", {}).get("external-id", []):
            if ext_id.get("external-id-type") == "doi":
                doi = ext_id.get("external-id-value", "").strip()
                break

        title = (summary.get("title") or {}).get("title", {}).get("value", "")
        pub_date = summary.get("publication-date") or {}
        year = (pub_date.get("year") or {}).get("value")
        journal = (summary.get("journal-title") or {}).get("value", "")
        work_type = summary.get("type", "")

        works.append(
            {
                "doi": doi,
                "title": title,
                "year": year,
                "journal": journal,
                "type": work_type,
            }
        )
    return works


def get_crossref_metadata(doi):
    """Fetch metadata for a DOI from Crossref. Returns dict or None."""
    try:
        resp = requests.get(CROSSREF_API + doi, headers=HEADERS_JSON, timeout=30)
        if resp.status_code != 200:
            return None
        return resp.json().get("message")
    except requests.RequestException:
        return None


def format_authors_crossref(authors):
    parts = []
    for a in authors or []:
        family = a.get("family", "").strip()
        given = a.get("given", "").strip()
        if not family and not given:
            continue
        if family and given:
            parts.append(f"{family}, {given}")
        else:
            parts.append(family or given)
    return " and ".join(parts)


def make_cite_key(first_author_family, year, title):
    first_word = ""
    for word in re.split(r"\s+", title):
        word_clean = re.sub(r"[^a-zA-Z0-9]", "", word)
        if len(word_clean) >= 4:
            first_word = word_clean
            break
    key = f"{slugify(first_author_family)}-{year or ''}-{slugify(first_word)}"
    return key or slugify(title)[:30]


def bibtex_escape(value):
    return str(value).replace("{", "").replace("}", "")


def crossref_to_bibtex(doi, crossref, fallback):
    entry_type = CROSSREF_TYPE_MAP.get(crossref.get("type"), "article")

    title_parts = crossref.get("title") or [fallback.get("title", "")]
    title = title_parts[0] if title_parts else fallback.get("title", "")

    authors = crossref.get("author")
    author_str = format_authors_crossref(authors) if authors else ""

    container = crossref.get("container-title") or [fallback.get("journal", "")]
    journal = container[0] if container else fallback.get("journal", "")

    # Year: prefer published-print, then published-online, then issued
    year = None
    for date_field in ("published-print", "published-online", "issued"):
        date_parts = (crossref.get(date_field) or {}).get("date-parts")
        if date_parts and date_parts[0]:
            year = date_parts[0][0]
            break
    if not year:
        year = fallback.get("year")

    volume = crossref.get("volume", "")
    issue = crossref.get("issue", "")
    pages = crossref.get("page", "")

    first_author_family = ""
    if authors:
        first_author_family = authors[0].get("family", "")
    cite_key = make_cite_key(first_author_family, year, title)

    fields = {
        "title": bibtex_escape(title),
        "author": author_str,
        "year": str(year) if year else "",
        "doi": doi,
    }
    if entry_type in ("article",):
        fields["journal"] = bibtex_escape(journal)
    elif entry_type == "inproceedings":
        fields["booktitle"] = bibtex_escape(journal)
    elif entry_type == "incollection":
        fields["booktitle"] = bibtex_escape(journal)

    if volume:
        fields["volume"] = str(volume)
    if issue:
        fields["number"] = str(issue)
    if pages:
        fields["pages"] = str(pages)

    return entry_type, cite_key, fields


def fallback_to_bibtex(work):
    title = work.get("title", "Untitled")
    year = work.get("year")
    cite_key = make_cite_key("orcid", year, title)
    fields = {
        "title": bibtex_escape(title),
        "year": str(year) if year else "",
        "journal": bibtex_escape(work.get("journal", "")),
        "note": "Imported from ORCID without DOI metadata; please check/edit.",
    }
    return "misc", cite_key, fields


def write_bibtex_entry(f, entry_type, cite_key, fields):
    f.write(f"@{entry_type}{{{cite_key},\n")
    for k, v in fields.items():
        if v:
            f.write(f"  {k} = {{{v}}},\n")
    f.write("}\n\n")


def generate_wordcloud(crossref_records):
    """
    Generate a word cloud PNG with transparent background from Crossref title +
    abstract text and save it to static/media/wordcloud.png.
    Requires: pip install wordcloud pillow
    """
    try:
        from wordcloud import WordCloud
    except ImportError:
        print("wordcloud not installed — skipping word cloud generation.")
        print("  Install with: pip install wordcloud")
        return

    texts = []
    for cr in crossref_records:
        title_parts = cr.get("title") or []
        if title_parts:
            texts.append(title_parts[0])
        abstract = cr.get("abstract", "") or ""
        # Strip JATS/HTML tags Crossref sometimes embeds
        abstract = re.sub(r"<[^>]+>", " ", abstract)
        if abstract.strip():
            texts.append(abstract)

    if not texts:
        print("No text available for word cloud — skipping.")
        return

    combined = " ".join(texts)

    wc = WordCloud(
        width=1000,
        height=1000,
        background_color=None,
        mode="RGBA",
        stopwords=STOPWORDS,
        max_words=120,
        min_font_size=11,
        prefer_horizontal=0.75,
        colormap="tab10",
        collocations=False,
    ).generate(combined)

    WORDCLOUD_OUT.parent.mkdir(parents=True, exist_ok=True)
    wc.to_file(str(WORDCLOUD_OUT))
    print(f"Word cloud saved to {WORDCLOUD_OUT}")


def main():
    print(f"Fetching works for ORCID {ORCID_ID} ...")
    works = get_orcid_works()
    print(f"Found {len(works)} works.")

    entries = []
    crossref_records = []  # kept for wordcloud text extraction
    for work in works:
        doi = work.get("doi")
        if doi:
            print(f"  Looking up DOI {doi} on Crossref ...")
            crossref = get_crossref_metadata(doi)
            time.sleep(1)  # be polite to the Crossref API
            if crossref:
                crossref_records.append(crossref)
                entries.append(crossref_to_bibtex(doi, crossref, work))
                continue
            print(f"    Crossref lookup failed for {doi}, using ORCID data only.")
        entries.append(fallback_to_bibtex(work))

    # Sort newest first
    def sort_key(entry):
        _, _, fields = entry
        try:
            return -int(fields.get("year", 0))
        except (TypeError, ValueError):
            return 0

    entries.sort(key=sort_key)

    BIB_DIR.mkdir(exist_ok=True)
    with open(ORCID_BIB, "w", encoding="utf-8") as f:
        f.write("% AUTO-GENERATED by scripts/sync_orcid_publications.py\n")
        f.write(f"% Source: ORCID {ORCID_ID} + Crossref. Do not hand-edit.\n\n")
        for entry_type, cite_key, fields in entries:
            write_bibtex_entry(f, entry_type, cite_key, fields)

    print(f"Wrote {len(entries)} entries to {ORCID_BIB}")

    # Combine manual + ORCID-synced entries into publications.bib
    manual_text = MANUAL_BIB.read_text(encoding="utf-8") if MANUAL_BIB.exists() else ""
    orcid_text = ORCID_BIB.read_text(encoding="utf-8")

    with open(OUTPUT_BIB, "w", encoding="utf-8") as f:
        f.write("% This file is generated by scripts/sync_orcid_publications.py\n")
        f.write("% Do not hand-edit directly:\n")
        f.write(f"%   - manual entries go in {MANUAL_BIB.relative_to(REPO_ROOT)}\n")
        f.write("%   - ORCID-synced entries are regenerated automatically\n\n")
        f.write(manual_text)
        f.write("\n")
        f.write(orcid_text)

    print(f"Wrote {OUTPUT_BIB}")

    # Generate word cloud from collected Crossref titles + abstracts
    print("Generating word cloud ...")
    generate_wordcloud(crossref_records)


if __name__ == "__main__":
    sys.exit(main())
