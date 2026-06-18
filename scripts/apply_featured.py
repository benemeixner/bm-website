#!/usr/bin/env python3
"""
Apply featured: true and summary: to publication files listed in
data/featured-publications.yaml.

Run after `academic import` to restore featured flags and blurbs
that the importer doesn't set.
"""

import re
import sys
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


def set_frontmatter_field(frontmatter, field, value):
    """Set or replace a field in a YAML frontmatter string."""
    pattern = re.compile(rf"^{field}:.*$", re.MULTILINE)
    replacement = f"{field}: '{value}'"
    if pattern.search(frontmatter):
        return pattern.sub(replacement, frontmatter)
    return frontmatter.rstrip("\n") + f"\n{field}: '{value}'\n"


def main():
    if not FEATURED_CONFIG.exists():
        print("No data/featured-publications.yaml found — skipping.")
        return 0

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
        parts = content.split("---", 2)
        if len(parts) < 3:
            print(f"  WARNING: could not parse frontmatter for {key}")
            continue

        frontmatter = parts[1]

        # Apply featured: true
        if "featured: false" in frontmatter:
            frontmatter = frontmatter.replace("featured: false", "featured: true")
        elif "featured: true" not in frontmatter:
            frontmatter = frontmatter.rstrip("\n") + "\nfeatured: true\n"

        # Apply summary (escape any single quotes in the text)
        if summary:
            escaped = summary.replace("'", "\\'")
            frontmatter = set_frontmatter_field(frontmatter, "summary", escaped)

        pub_file.write_text("---" + frontmatter + "---" + parts[2], encoding="utf-8")
        print(f"  {key}: applied featured + summary")

    return 0


if __name__ == "__main__":
    sys.exit(main())
