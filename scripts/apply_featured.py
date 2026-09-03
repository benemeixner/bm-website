#!/usr/bin/env python3
"""
Post-import fixups applied after `academic import`:
  1. Apply featured: true and summary: from data/featured-publications.yaml
  2. Fix publication dates: replace YYYY-01-01 placeholders with real
     month-level dates fetched from the CrossRef API via each paper's DOI.
"""

import re
import sys
import time
import urllib.request
import json
from pathlib import Path

try:
    import yaml
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
    import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
FEATURED_CONFIG = REPO_ROOT / "data" / "featured-publications.yaml"
PUBS_DIR = REPO_ROOT / "content" / "publications"
CROSSREF_API = "https://api.crossref.org/works/{doi}"
MAILTO = "benedikt.meixner@unibw.de"


# ── Frontmatter helpers ────────────────────────────────────────────────────────

def set_frontmatter_field(frontmatter, field, value):
    """Set or replace a field in a YAML frontmatter string."""
    pattern = re.compile(rf"^{field}:.*$", re.MULTILINE)
    replacement = f"{field}: '{value}'"
    if pattern.search(frontmatter):
        return pattern.sub(replacement, frontmatter)
    return frontmatter.rstrip("\n") + f"\n{field}: '{value}'\n"


def parse_md(content):
    """Split markdown into (frontmatter_str, body_str). Returns None if not parseable."""
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    return parts[1], parts[2]


def reassemble(frontmatter, body):
    return "---" + frontmatter + "---" + body


# ── CrossRef date lookup ───────────────────────────────────────────────────────

def crossref_date(doi):
    """Return 'YYYY-MM-01' for a DOI using CrossRef, or None on failure."""
    url = CROSSREF_API.format(doi=doi.strip()) + f"?mailto={MAILTO}"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": f"BenediktMeixnerSite/1.0 (mailto:{MAILTO})"}
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            msg = json.loads(r.read())["message"]
        for field in ("published-print", "published-online", "issued"):
            dp = msg.get(field, {}).get("date-parts", [[]])[0]
            if dp and len(dp) >= 2:
                return f"{dp[0]}-{dp[1]:02d}-01"
            if dp and len(dp) == 1:
                # Year only — keep as-is (no improvement over what we have)
                return None
    except Exception as e:
        print(f"    CrossRef lookup failed for {doi}: {e}")
    return None


def extract_doi(frontmatter):
    """Pull the DOI from frontmatter — checks both top-level doi: and hugoblox.ids.doi."""
    # Top-level doi: field
    m = re.search(r"^doi:\s*(.+)$", frontmatter, re.MULTILINE | re.IGNORECASE)
    if m:
        return m.group(1).strip().strip("'\"")
    # Structured hugoblox.ids.doi
    m = re.search(r"doi:\s*'?([^'\n]+)'?", frontmatter)
    if m:
        return m.group(1).strip()
    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def apply_featured(pub_dirs):
    """Step 1: apply featured flags and summaries."""
    if not FEATURED_CONFIG.exists():
        print("No data/featured-publications.yaml found — skipping featured step.")
        return

    config = yaml.safe_load(FEATURED_CONFIG.read_text(encoding="utf-8"))
    entries = config.get("featured", [])

    for entry in entries:
        key = entry.get("key")
        summary = entry.get("summary", "").strip()
        if not key:
            continue

        pub_file = PUBS_DIR / key / "index.md"
        if not pub_file.exists():
            print(f"  WARNING: {key}/index.md not found — skipping.")
            continue

        content = pub_file.read_text(encoding="utf-8")
        parsed = parse_md(content)
        if not parsed:
            print(f"  WARNING: could not parse frontmatter for {key}")
            continue
        frontmatter, body = parsed

        if "featured: false" in frontmatter:
            frontmatter = frontmatter.replace("featured: false", "featured: true")
        elif "featured: true" not in frontmatter:
            frontmatter = frontmatter.rstrip("\n") + "\nfeatured: true\n"

        if summary:
            escaped = summary.replace("'", "\\'")
            frontmatter = set_frontmatter_field(frontmatter, "summary", escaped)

        pub_file.write_text(reassemble(frontmatter, body), encoding="utf-8")
        print(f"  {key}: applied featured + summary")


def fix_dates(pub_dirs):
    """Step 2: replace YYYY-01-01 dates with real months from CrossRef."""
    print("\nFixing publication dates via CrossRef …")
    updated = 0
    for pub_dir in sorted(pub_dirs):
        pub_file = pub_dir / "index.md"
        if not pub_file.exists():
            continue

        content = pub_file.read_text(encoding="utf-8")
        parsed = parse_md(content)
        if not parsed:
            continue
        frontmatter, body = parsed

        # Only fix dates that look like YYYY-01-01 (i.e. month was never set)
        m = re.search(r"^date:\s*'?(\d{4})-01-01'?", frontmatter, re.MULTILINE)
        if not m:
            continue  # date already has a real month — skip

        doi = extract_doi(frontmatter)
        if not doi:
            print(f"  {pub_dir.name}: no DOI found — skipping date fix")
            continue

        real_date = crossref_date(doi)
        time.sleep(0.15)  # be polite to CrossRef

        if not real_date or real_date.endswith("-01-01"):
            print(f"  {pub_dir.name}: CrossRef returned January or no month — leaving as-is")
            continue

        frontmatter = re.sub(
            r"^(date:\s*)'?\d{4}-01-01'?",
            f"\\g<1>'{real_date}'",
            frontmatter,
            flags=re.MULTILINE,
        )
        pub_file.write_text(reassemble(frontmatter, body), encoding="utf-8")
        print(f"  {pub_dir.name}: {m.group(1)}-01-01 → {real_date}")
        updated += 1

    print(f"Dates fixed: {updated} paper(s) updated.")


def main():
    pub_dirs = [d for d in PUBS_DIR.iterdir() if d.is_dir()] if PUBS_DIR.exists() else []

    print("=== Step 1: Apply featured flags ===")
    apply_featured(pub_dirs)

    print("\n=== Step 2: Fix publication dates ===")
    fix_dates(pub_dirs)

    return 0


if __name__ == "__main__":
    sys.exit(main())
