#!/usr/bin/env python3
"""Validate updates/feed.json. Run before opening a pull request:  python3 updates/validate.py"""
import json, re, sys
from datetime import date
from pathlib import Path

TYPES = {"research", "guideline", "trial", "event", "knowledge", "clinical", "digest", "other"}
EVIDENCE = {"guideline", "meta-analysis", "rct", "observational", "preclinical",
            "preprint", "company", "regulatory", "review"}
EVIDENCE_REQUIRED = {"research", "trial", "guideline", "clinical"}
BILINGUAL = ("title", "plain", "summary")
MAX_LEN = {"title": 160, "plain": 400, "summary": 900}
DIGEST_SUMMARY_MAX = 2000
ALLOWED = {"id", "date", "type", "evidence", "title", "plain", "summary", "link", "source", "tags"}
ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
URL_RE = re.compile(r"^(https://|\.\./)[^\s<>\"']+$")
GREEK_RE = re.compile("[Ͱ-Ͽἀ-῿]")


def fail(errors):
    for e in errors:
        print("ERROR:", e)
    sys.exit(1)


def bilingual_ok(v):
    return isinstance(v, dict) and set(v) == {"el", "en"} and all(isinstance(x, str) and x.strip() for x in v.values())


def main():
    path = Path(__file__).with_name("feed.json")
    try:
        feed = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        fail([f"feed.json is not valid JSON: {e}"])
    if feed.get("version") != 1 or not isinstance(feed.get("items"), list):
        fail(['feed.json must be {"version": 1, "items": [...]}'])
    errors = []
    seen = set()
    prev = None
    for n, it in enumerate(feed["items"]):
        if not isinstance(it, dict):
            errors.append(f"items[{n}]: must be an object")
            continue
        where = f"items[{n}] ({it.get('id', '?')})"
        extra = set(it) - ALLOWED
        if extra:
            errors.append(f"{where}: unknown fields {sorted(extra)}")

        iid = it.get("id", "")
        if not isinstance(iid, str) or not ID_RE.match(iid):
            errors.append(f"{where}: id must look like 2026-10-01-short-slug")
        if iid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(iid)

        try:
            d = date.fromisoformat(it.get("date", ""))
            if isinstance(iid, str) and not iid.startswith(it["date"]):
                errors.append(f"{where}: id must start with the date")
            if d > date.today():
                errors.append(f"{where}: date is in the future")
            if prev and d > prev:
                errors.append(f"{where}: items must be sorted newest first")
            prev = d
        except (ValueError, TypeError):
            errors.append(f"{where}: date must be YYYY-MM-DD")

        itype = it.get("type")
        if itype not in TYPES:
            errors.append(f"{where}: type must be one of {sorted(TYPES)}")
        if "evidence" in it:
            if it["evidence"] not in EVIDENCE:
                errors.append(f"{where}: evidence must be one of {sorted(EVIDENCE)}")
        elif itype in EVIDENCE_REQUIRED:
            errors.append(f"{where}: evidence is required for type '{itype}'")

        for key in BILINGUAL:
            v = it.get(key)
            limit = DIGEST_SUMMARY_MAX if (key == "summary" and itype == "digest") else MAX_LEN[key]
            if not bilingual_ok(v):
                errors.append(f"{where}: {key} must have non-empty 'el' and 'en' strings")
            elif any(len(x) > limit for x in v.values()):
                errors.append(f"{where}: {key} longer than {limit} characters")
            elif key != "title" and not GREEK_RE.search(v["el"]):
                errors.append(f"{where}: {key}.el contains no Greek text")

        if "link" in it and not (isinstance(it["link"], str) and URL_RE.match(it["link"])):
            errors.append(f"{where}: link must be an https:// URL or a ../ site path")
        src = it.get("source")
        label = src.get("label") if isinstance(src, dict) else None
        label_ok = (isinstance(label, str) and label.strip()) or bilingual_ok(label)
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
