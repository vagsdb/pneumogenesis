# Updates feed — agent instructions

The page `/updates/` shows the items in `updates/feed.json`. An agent adds new items
and opens a pull request; the site owner reviews and merges it. **Nothing is ever
pushed straight to `main`, and the agent never merges its own pull request.**

## 1. Audience

The feed is read by a **wide range of people at once**: patients and families,
clinicians and researchers. Every post therefore has two layers:

- **`plain`** — "Σε απλά λόγια / In plain words": 1–2 sentences a patient can
  understand without medical training. What was found and what it means (or does
  not yet mean) for people living with pulmonary fibrosis. No abbreviations
  without explanation, no statistics beyond a simple number.
- **`summary`** — the technical layer for clinicians and researchers: design, n,
  population, endpoint, effect size with CI or p, and the main limitation.

## 2. Scope

**Diseases**

- Idiopathic pulmonary fibrosis (IPF) — the core.
- Progressive pulmonary fibrosis (PPF) and fibrotic ILD in general.
- Connective-tissue-disease ILD (rheumatoid arthritis, systemic sclerosis),
  fibrotic hypersensitivity pneumonitis, fibrotic (stage IV) sarcoidosis and
  post-COVID fibrosis.

For non-IPF diseases, say in the summary which disease the study was in and
whether it applies to IPF.

**Evidence** — all of the following may be posted, always with the right
`evidence` badge (section 5):

- guidelines, consensus statements, RCTs (phase 2/3), systematic reviews and
  meta-analyses;
- observational and real-world studies (registries, cohorts, real-world drug data);
- basic science: mechanisms, omics, animal and cell models;
- preprints (medRxiv, bioRxiv), congress abstracts and company announcements —
  always labelled as such in the badge and in the text.

**Events** — Greek events (Ελληνική Πνευμονολογική Εταιρεία, Greek patient
associations, university ILD centres, hospital meetings) and major European and
international congresses (ERS, ATS, ERS/ELF patient sessions, EU-IPFF). Skip small
non-Greek webinars.

## 3. Sources — check every run

| Area | Sources |
|---|---|
| Research | PubMed (use the PubMed tools if available, otherwise web search); medRxiv / bioRxiv for preprints |
| Trials | ClinicalTrials.gov, EU Clinical Trials Information System (CTIS): new trials, readouts, early stops |
| Regulators | FDA, EMA, ΕΟΦ (Εθνικός Οργανισμός Φαρμάκων): approvals, label changes, safety notices |
| Guidelines | ATS / ERS / JRS / ALAT, BTS, NICE, ISHLT, Ελληνική Πνευμονολογική Εταιρεία |
| Greece | Ελληνική Πνευμονολογική Εταιρεία, Greek IPF / pulmonary fibrosis patient associations, university ILD centres |
| Patient organisations | EU-IPFF, Pulmonary Fibrosis Foundation, Action for Pulmonary Fibrosis, European Lung Foundation (ELF) |
| Industry | Company press releases for topline results and approvals only (see section 6) |

Record every source and query you ran, and any you could not reach, for the
search log in the pull request (section 8).

## 4. Schedule and selection

| Run | When (Athens time) | Scope | Max items |
|---|---|---|---|
| Monday | 08:52 | everything new since the newest item in the feed | 8 |
| Wednesday | 08:52 | everything new since the newest item in the feed | 8 |
| Friday | 17:47 — weekly roundup | the whole week (Monday–Friday), all sources, deeper search | 12 + 1 digest |

**Selection — balanced mix.** Each run should cover a spread of types rather than
filling every slot with one kind. As a guide, when enough material exists, aim
for a mix like: clinical / treatment (guidelines, approvals, trials, safety
notices), research (RCTs, observational, basic science), and Greek or European
events / patient-relevant news. Within each group prefer the more important and
better-evidenced item. Quality over quantity: it is fine to post fewer items, or
nothing.

**Friday weekly digest** — besides the new items, add one `digest` item dated
that Friday (`id`: `YYYY-MM-DD-weekly-digest`, `evidence` omitted):

- a **longer briefing**, up to ~10 sentences per language, grouped by theme —
  e.g. "Treatment", "Research", "Events & community" — with the theme names in
  the text;
- name this week's posts it refers to (including those still in open pull
  requests);
- `plain`: 1–2 sentences on the week's single most important takeaway for patients;
- `source.url` is `../updates/`, `link` omitted.

Post the digest unless the week had no posts at all.

## 5. Item format

```json
{
  "id": "2026-10-08-short-english-slug",
  "date": "2026-10-08",
  "type": "research",
  "evidence": "rct",
  "title": { "el": "Ελληνικός τίτλος", "en": "English title" },
  "plain": { "el": "1–2 απλές προτάσεις.", "en": "1–2 plain sentences." },
  "summary": { "el": "2–5 τεχνικές προτάσεις.", "en": "2–5 technical sentences." },
  "link": "https://doi.org/...",
  "source": { "label": "NEJM · 2026", "url": "https://doi.org/..." },
  "tags": ["nerandomilast", "fvc"]
}
```

- `id`: the date, then a short lowercase English slug. Unique.
- `date`: when the item became public (publication, announcement), `YYYY-MM-DD`,
  never in the future. For events use the announcement date and give the event
  date and place in the text.
- `type`: `research`, `guideline`, `trial`, `event`, `knowledge`, `clinical`,
  `digest` (Friday only) or `other`.
- `evidence` — required for `research`, `trial`, `guideline` and `clinical`;
  optional otherwise:

  | value | badge (ΕΛ / EN) | use for |
  |---|---|---|
  | `guideline` | Κατευθυντήρια οδηγία / Guideline | guidelines, consensus statements |
  | `meta-analysis` | Μετα-ανάλυση / Meta-analysis | systematic reviews, meta-analyses |
  | `rct` | Τυχαιοποιημένη μελέτη / RCT | randomised trials, phase 2/3 results |
  | `observational` | Μελέτη παρατήρησης / Observational | cohorts, registries, real-world data |
  | `preclinical` | Προκλινική (εργαστήριο/ζώα) / Preclinical (lab/animal) | cell, animal, omics, mechanism studies |
  | `preprint` | Προδημοσίευση / Preprint or abstract | preprints, congress abstracts |
  | `company` | Ανακοίνωση εταιρείας / Company announcement | press releases, topline results |
  | `regulatory` | Ρυθμιστική απόφαση / Regulatory | FDA / EMA / ΕΟΦ approvals and safety notices |
  | `review` | Ανασκόπηση / Review | narrative reviews, explainers, Pneumogenesis reviews |

- `title`, `plain`, `summary`: **Greek and English both required.**
- `link` (optional) and `source.url`: `https://` links only; prefer the DOI or
  the official page. `source.label` is short, e.g. `NEJM · 2026`; when it contains
  words give it as `{ "el": "...", "en": "..." }`.
- `tags`: up to 8 short lowercase keywords.

## 6. Writing rules

**Greek style — warm and clear.** Approachable modern Greek, not word-for-word
translation. Give the Greek medical term with the English term or abbreviation in
parentheses the first time in each post, e.g. «βίαιη ζωτική χωρητικότητα (FVC)»,
«διάμεση πνευμονοπάθεια (ILD)». Drug and trial names stay in Latin script. Decimal
commas in Greek (`+37,3`).

**Accuracy**

- Summarise only what the source says. Give numbers with their context.
  Say what the result does **not** show.
- Never invent a citation, number, date or event. If you cannot open and verify
  the source, leave the item out.
- No hype ("breakthrough", "cure", "επανάσταση", «θαύμα»).
- Preclinical results: say plainly in `plain` that this is lab/animal research and
  is years away from treatment, if ever.
- Preprints and abstracts: say they are not yet peer-reviewed.
- **Industry news:** allowed for major topline results and approvals, with
  `evidence: "company"` and the words "company announcement — not yet
  peer-reviewed" / «ανακοίνωση εταιρείας — δεν έχει ακόμη αξιολογηθεί από
  ομοτίμους» in the summary. No promotional wording, no product claims beyond
  what the release states.

**Patient safety — every post**

1. **No individual advice.** Never tell readers to start, stop or change a
   treatment.
2. **"Ask your doctor".** Every post about a treatment, drug, device or
   intervention ends its `plain` text with a short line, e.g. «Συζητήστε το με
   τον πνευμονολόγο σας.» / "Discuss this with your pulmonologist."
3. **Flag unproven therapies.** When a post touches stem cells, supplements or
   other unregulated offers, warn explicitly that unregulated clinics and products
   marketed for pulmonary fibrosis are unproven and can be harmful.
4. **Availability.** Say clearly when a drug or device is not approved, or not
   available in Greece (state what is known: EMA status, ΕΟΦ availability).

## 7. Each run

1. Start from the latest `main`:
   `git fetch origin main && git checkout -B updates/YYYY-MM-DD origin/main`
2. Read `updates/feed.json` (by `id`, title and source URL) and the
   `updates/feed.json` changes in any **open** pull request titled
   `Updates feed: …`. Both count as already posted. Never post the same study,
   guideline or event twice.
3. Search the sources in section 3 for what is new since the newest item's date
   (at most the last 14 days on the first run). Verify each candidate by opening
   the source.
4. Select per section 4 and write items per sections 5 and 6.
5. Add them to the **top** of `items` (newest first), run
   `python3 updates/validate.py`, and fix every error.
6. Commit as `Updates feed: N new items (YYYY-MM-DD)` (Friday:
   `Updates feed: weekly roundup (YYYY-MM-DD)`) and push the branch.
7. Open a pull request into `main` titled `Updates feed: YYYY-MM-DD` (Friday:
   `Updates feed: weekly roundup YYYY-MM-DD`) with the body described in section 8.
8. If nothing new and important was found, do not open a pull request; end with a
   short note that includes the search log.

## 8. Pull request body

Use these sections, in this order:

1. **Items** — one block per item:
   - title (EN), `type` and `evidence`, source link;
   - **Confidence: high / medium / low** with the reason (e.g. "full text read",
     "abstract only", "press release only", "event page in Greek only");
   - one line on why it was chosen.
2. **Greek preview** — for every item, the Greek title and the Greek `plain`
   text, so the reviewer can check the Greek without opening the JSON.
3. **Considered but skipped** — candidates found but left out, one line each with
   the reason (duplicate, weak evidence, out of scope, could not verify, slot limit).
4. **Search log** — every source and query run, and any source that could not be
   reached (with the error).
5. **Please double-check** — anything uncertain: numbers, translations of
   technical terms, availability in Greece.
