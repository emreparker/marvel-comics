#!/usr/bin/env python3
"""
build_reading_list.py

Builds a Markdown checklist (with Marvel issue URLs) for a named reading list in ./lists/*.json.

It uses marvel_year_scraper.py to fetch + decode year pages, then matches issues by exact `title`.

Usage:
  python build_reading_list.py --list lists/hickman_secret_wars_full.json --out out/hickman_full.md
  python build_reading_list.py --list lists/hickman_secret_wars_minimal.json --out out/hickman_minimal.md

Tip:
- If many URLs are missing, widen `year_pages` in the list json, or run:
    python marvel_year_scraper.py scrape --start 2009 --end 2016 --out data/issues_2009_2016.jsonl
  then pass `--from-jsonl data/issues_2009_2016.jsonl` to avoid re-fetching.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

import marvel_year_scraper as mys


def expand_items(items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Expand items like {"title": "Avengers (2012) #1", "range": "1-44"} into individual titles.
    Leaves plain {"title": "..."} as-is.
    """
    out: List[Dict[str, str]] = []
    for it in items:
        title = str(it["title"])
        r = it.get("range")
        if not r:
            out.append({"title": title, "note": str(it.get("note", "")).strip()})
            continue

        # Range assumed to apply to the issue number part after '#'
        # Example title: "Avengers (2012) #1" range "1-44"
        start_s, end_s = str(r).split("-", 1)
        start = int(start_s)
        end = int(end_s)
        prefix = title.split("#")[0].strip()
        for n in range(start, end + 1):
            out.append({"title": f"{prefix}#{n}".replace(" #", " #"), "note": ""})
    return out


def normalize_title_spacing(t: str) -> str:
    # Ensure consistent "Series (Year) #N" spacing
    t = t.replace("  ", " ").strip()
    # Fix if we accidentally ended with "... )#12"
    t = t.replace(")#", ") #")
    return t


def load_title_to_url_from_jsonl(path: Path) -> Dict[str, str]:
    m: Dict[str, str] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            title = obj.get("title")
            url = obj.get("detailUrl")
            if isinstance(title, str) and isinstance(url, str):
                m[normalize_title_spacing(title)] = mys.normalize_marvel_url(url)
    return m


def fetch_title_to_url_for_years(year_pages: List[int], delay: float) -> Dict[str, str]:
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "marvel-unlimited-open-api/0.1 (+https://github.com/yourname/yourrepo)",
        "Accept": "application/json, text/plain, */*",
    })

    title_to_url: Dict[str, str] = {}
    for y in year_pages:
        payload = mys.fetch_year(y, sess)
        if payload is None:
            continue
        issues = mys.decode_issues_from_payload(payload)
        for it in issues:
            title = it.get("title")
            url = it.get("detailUrl")
            if isinstance(title, str) and isinstance(url, str):
                title_to_url[normalize_title_spacing(title)] = mys.normalize_marvel_url(url)

        if delay > 0:
            import time
            time.sleep(delay)

    return title_to_url


def write_md(out_path: Path, list_name: str, description: str, items: List[Dict[str, str]], title_to_url: Dict[str, str]) -> Tuple[int, int]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    missing = 0
    total = 0

    lines = [f"# {list_name}", "", description.strip(), "", "## Checklist", ""]
    for it in items:
        total += 1
        title = normalize_title_spacing(it["title"])
        note = it.get("note", "")
        url = title_to_url.get(title)
        if url:
            lines.append(f"- [ ] [{title}]({url})" + (f" — {note}" if note else ""))
        else:
            missing += 1
            lines.append(f"- [ ] {title}  **(URL not found)**")

    lines += ["", "---", f"Total: {total}", f"Missing URLs: {missing}", ""]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return total, missing


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", type=Path, required=True, help="Path to list JSON (./lists/*.json)")
    ap.add_argument("--out", type=Path, required=True, help="Output markdown path")
    ap.add_argument("--delay", type=float, default=0.1, help="Delay between year requests when fetching")
    ap.add_argument("--from-jsonl", type=Path, default=None, help="Use already-scraped JSONL instead of fetching year pages")
    args = ap.parse_args()

    cfg = json.loads(args.list.read_text(encoding="utf-8"))
    list_name = cfg.get("name", args.list.stem)
    description = cfg.get("description", "")
    year_pages = cfg.get("year_pages", [])
    items_raw = cfg.get("items", [])
    items = [{"title": normalize_title_spacing(x["title"]), "note": x.get("note", "")} for x in expand_items(items_raw)]

    if args.from_jsonl:
        title_to_url = load_title_to_url_from_jsonl(args.from_jsonl)
    else:
        title_to_url = fetch_title_to_url_for_years(list(map(int, year_pages)), args.delay)

    total, missing = write_md(args.out, list_name, description, items, title_to_url)
    print(f"Wrote {args.out} (total={total}, missing={missing})")


if __name__ == "__main__":
    main()
