# Pneumogenesis

Evidence-led pulmonary fibrosis intelligence for patients, clinicians, and researchers.

## Current feature

- `/ipf-insights/` — curated visual reading of the 2026 IPF deep scientific journal briefing
- `/reports/IPF_Deep_Scientific_Journal_Insights_2026.pdf` — complete six-page report with 21 linked sources
- `/ipf-interventions/` — bilingual (ΕΛ / EN, switch in the header, `?lang=en` or `?lang=el`) evidence review (2026) of non-pharmacological interventions in IPF: rehabilitation, oxygen, transplantation, palliative care, comorbidities, remote monitoring, investigational approaches
- `/medicines/` — bilingual (ΕΛ / EN) list of antifibrotic medicines: each original (Esbriet, Ofev, Jascayd) next to every generic registered in Greece, plus EU-only generics, with sources
- `/explore/` — bilingual (ΕΛ / EN) interactive tools: myth-or-fact quiz, FVC time machine (with vs without antifibrotic, INPULSIS averages), synthesized "velcro" crackles, pursed-lip breathing pacer
- `/updates/` — bilingual (ΕΛ / EN) news feed of research, guidelines, trials, events and knowledge; content lives in `updates/feed.json` and is posted by an agent via reviewed pull requests (see `updates/AGENT.md`)
- `updates/local-agent/` — run the updates agent on your own computer (Debian/macOS) on a schedule; see its README
- `/vags-console/` — personal habits, goals, tasks, and scratchpad dashboard with browser-local storage

The site is static and dependency-free. It is designed to be served directly with GitHub Pages from the repository root.
