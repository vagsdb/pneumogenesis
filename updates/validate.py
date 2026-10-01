#!/usr/bin/env python3
"""Validate updates/feed.json. Run before opening a pull request:  python3 updates/validate.py"""
import json, re, sys
from datetime import date
from pathlib import Path

TYPES = {"research", "guideline", "trial", "event", "knowledge", "clinical", "other"}
ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
URL_RE = re.compile(r"^(https://|\.\./)[^\s<>\"']+$")
BILINGUAL = ("title", "summary")


def fail(errors):
    for e in errors:
        print("ERROR:", e)
    sys.exit(1)


def main():
    path = Path(__file__).with_name("feed.json")
    try:
        feed = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        fail([f"feed.json is not valid JSON: {e}"])
    errors = []
    if feed.get("version") != 1 or not isinstance(feed.get("items"), list):
        fail(["feed.json must be {\"version\": 1, \"items\": [...]}"])
    seen = set()
    prev = None
    for n, it in enumerate(feed["items"]):
        where = f"items[{n}] ({it.get('id', '?')})"
        allowed = {"id", "date", "type", "title", "summary", "link", "source", "tags"}
        extra = set(it) - allowed
        if extra:
            errors.append(f"{where}: unknown fields {sorted(extra)}")
        iid = it.get("id", "")
        if not ID_RE.match(iid):
            errors.append(f"{where}: id must look like 2026-10-01-short-slug")
        if iid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(iid)
        try:
            d = date.fromisoformat(it.get("date", ""))
            if not iid.startswith(it["date"]):
                errors.append(f"{where}: id must start with the date")
            if d > date.today():
                errors.append(f"{where}: date is in the future")
            if prev and d > prev:
                errors.append(f"{where}: items must be sorted newest first")
            prev = d
        except (ValueError, TypeError):
            errors.append(f"{where}: date must be YYYY-MM-DD")
        if it.get("type") not in TYPES:
            errors.append(f"{where}: type must be one of {sorted(TYPES)}")
        for key in BILINGUAL:
            v = it.get(key)
            if not isinstance(v, dict) or set(v) != {"el", "en"} or not all(isinstance(x, str) and x.strip() for x in v.values()):
                errors.append(f"{where}: {key} must have non-empty 'el' and 'en' strings")
            elif key == "title" and any(len(x) > 160 for x in v.values()):
                errors.append(f"{where}: title longer than 160 characters")
            elif key == "summary" and any(len(x) > 900 for x in v.values()):
                errors.append(f"{where}: summary longer than 900 characters")
            elif key == "summary" and not re.search(r"[Ͱ-Ͽ]", v.get("el", "")):
                errors.append(f"{where}: {key}.el contains no Greek text")
        if "link" in it and not (isinstance(it["link"], str) and URL_RE.match(it["link"])):
            errors.append(f"{where}: link must be an https:// URL or a ../ site path")
        src = it.get("source")
        label = src.get("label") if isinstance(src, dict) else None
        label_ok = (isinstance(label, str) and label.strip()) or (
            isinstance(label, dict) and set(label) == {"el", "en"}
            and all(isinstance(x, str) and x.strip() for x in label.values()))
        if not isinstance(src, dict) or not label_ok \
                or not isinstance(src.get("url"), str) or not URL_RE.match(src["url"]):
            errors.append(f"{where}: source must be {{label, url}}: label a string or {{el, en}}, url https:// or ../ site path")
        tags = it.get("tags", [])
        if not isinstance(tags, list) or len(tags) > 8 or not all(isinstance(t, str) and 0 < len(t) <= 40 for t in tags):
            errors.append(f"{where}: tags must be a list of up to 8 short strings")
    if errors:
        fail(errors)
    print(f"OK: {len(feed['items'])} items")


if __name__ == "__main__":
    main()
