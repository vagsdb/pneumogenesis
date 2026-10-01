# Updates feed — agent instructions

The page `/updates/` shows the items in `updates/feed.json`. An agent adds new items
and opens a pull request; the site owner reviews and merges it. **Nothing is ever
pushed straight to `main`.**

## Schedule

| Run | When (Athens time) | Scope | Max items |
|---|---|---|---|
| Monday | morning | everything new since the newest item in the feed | 5 |
| Wednesday | morning | everything new since the newest item in the feed | 5 |
| Friday | weekly roundup | the whole week (Monday–Friday), all source types, deeper search | 8 + 1 digest |

**Friday roundup:** besides new items, add one `digest` item dated that Friday
(`id`: `YYYY-MM-DD-weekly-digest`) that summarises the week in 3–6 sentences per
language: the most important findings, why they matter, and links back to this
week's posts by naming them. Its `source.url` is `../updates/` and its `link` is
omitted. Post the digest even if the only items this week came from Monday and
Wednesday; skip it only if the week had no posts at all.

## Each run

1. Start from the latest `main`:
   `git fetch origin main && git checkout -B updates/YYYY-MM-DD origin/main`
2. Read `updates/feed.json` to see what is already posted (by `id`, title and
   source URL). Also read the `updates/feed.json` changes in any **open** pull
   request titled `Updates feed: …` — those items are waiting for review and count
   as already posted (the Friday digest may mention them). Never post the same
   study, guideline or event twice.
3. Look for what is new since the newest item's date (at most the last 14 days on
   the first run):
   - **Research**: PubMed for idiopathic pulmonary fibrosis, progressive pulmonary
     fibrosis and fibrotic ILD — prioritise RCTs, phase 2/3 results, meta-analyses
     and major-journal papers (NEJM, Lancet, Lancet Respir Med, AJRCCM, ERJ, Thorax,
     Chest, Nature/Cell family).
   - **Guidelines**: new or updated ATS / ERS / JRS / ALAT, BTS, NICE, ISHLT,
     Hellenic Thoracic Society statements.
   - **Trials**: new readouts, starts or stops of notable trials; drug approvals
     (FDA, EMA).
   - **Events**: upcoming congresses, webinars and patient days relevant to IPF,
     especially in Greece and Europe.
   - **Knowledge / clinical**: practice-relevant explainers or safety notices.
4. Pick at most **5** items (Friday: **8** plus the digest) that genuinely matter. Quality over quantity; it is
   fine to post nothing.
5. Add them to the **top** of `items` (newest first), run
   `python3 updates/validate.py`, and fix every error it reports.
6. Commit as `Updates feed: N new items (YYYY-MM-DD)` (Friday: `Updates feed: weekly roundup (YYYY-MM-DD)`) and push the branch.
7. Open a pull request into `main` titled `Updates feed: YYYY-MM-DD` (Friday: `Updates feed: weekly roundup YYYY-MM-DD`). In the body,
   list each item with its source link and one line on why it was chosen, plus
   anything the reviewer should double-check.
8. If nothing new and important was found, do not open a pull request.

## Item format

```json
{
  "id": "2026-10-08-short-english-slug",
  "date": "2026-10-08",
  "type": "research",
  "title": { "el": "Ελληνικός τίτλος", "en": "English title" },
  "summary": { "el": "2–4 προτάσεις στα ελληνικά.", "en": "2–4 sentences in English." },
  "link": "https://doi.org/...",
  "source": { "label": "Journal · Year", "url": "https://doi.org/..." },
  "tags": ["nerandomilast", "FVC"]
}
```

- `id`: the date, then a short lowercase English slug. Unique.
- `date`: the date the item became public (publication, announcement), `YYYY-MM-DD`,
  not in the future (except for events, use the announcement date and give the
  event date in the summary).
- `type`: one of `research`, `guideline`, `trial`, `event`, `knowledge`,
  `clinical`, `digest` (Friday weekly roundup only), `other`.
- `title`, `summary`: **both Greek and English are required.** Write natural Greek
  (not word-for-word); keep standard abbreviations (FVC, DLCO, 6MWD, RCT) and drug
  and trial names in Latin script; use decimal commas in Greek (`+37,3`).
- `link` (optional) and `source.url`: `https://` links only — prefer the DOI or
  the official page. `source.label` is short, e.g. `NEJM · 2026`; when it contains words, give it as `{ "el": "...", "en": "..." }`.
- `tags`: up to 8 short lowercase keywords.

## Writing rules

- Summarise only what the source says. Give numbers with their context (n, design,
  endpoint, effect size, CI or p). Say what the result does **not** show.
- Never invent a citation, number or date. If you cannot open and verify the
  source, leave the item out.
- No treatment advice to individual patients. No hype ("breakthrough", "cure").
- Preprints, conference abstracts and press releases must say so in the summary.
