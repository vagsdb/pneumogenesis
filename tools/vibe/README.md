# vibe

Give it links, get back links with the same vibe.

```bash
pip install -r requirements.txt            # just yt-dlp
pip install sentence-transformers          # optional, better matching

python vibe.py "https://www.youtube.com/watch?v=jfKfPfyJRdk"
python vibe.py URL1 URL2 URL3 -n 20 --deep 25 -v
python vibe.py "https://open.spotify.com/track/..." --source youtube,soundcloud
python vibe.py "https://www.youtube.com/playlist?list=..." --other-channels --min-duration 61
python vibe.py URL --json > similar.json
```

**Inputs:** anything [yt-dlp](https://github.com/yt-dlp/yt-dlp) can read (YouTube, SoundCloud,
Vimeo, Bandcamp, ...), including playlists and channels, which use their first 25 items.
For any other page, such as Spotify or an article, it reads the page's title, description
and keyword tags. Several links together give a stronger signal, because words the seeds
have in common count for more.

## How it works

1. **Extract**: reads the title, tags, categories, description (link spam removed), channel
   and duration of each seed.
2. **Vibe profile**: builds a weighted list of words and two-word phrases. Tags count most,
   then the title, then the description. Words shared by several seeds get a boost, and
   channel names get less weight because they say who made it, not how it feels.
3. **Search**: runs up to 8 different queries (recurring genre tags, key-term combinations,
   cleaned seed titles) in parallel on YouTube and/or SoundCloud. No API key needed.
4. **Rank**: each result is scored on
   - meaning similarity to the seeds: 60% closeness to the seeds' average, 40% to the
     closest single seed (multilingual sentence embeddings, or TF-IDF if those aren't
     installed),
   - duration affinity, so 3-minute songs match songs and 2-hour mixes match mixes,
   - how many separate queries found the same result.
5. **Diversify**: a diversity pass (MMR) skips near-duplicates, and each channel is
   capped at 2 results (`--per-channel`).

`--deep K` fetches full tags and descriptions for the top K before the final ranking.
It is slower and gives better results.

| Option | Default | |
|---|---|---|
| `-n` | 15 | results |
| `--source` | youtube | `youtube`, `soundcloud`, or both comma-separated |
| `--queries` / `--per-query` | 8 / 15 | search breadth |
| `--deep K` | 0 | enrich the top K before final ranking |
| `--embedder` | auto | `sbert`, `tfidf` |
| `--other-channels` | off | exclude the seeds' own channels/artists |
| `--min-duration SEC` | 0 | e.g. `61` to skip Shorts |

Tests run offline: `python -m pytest tools/vibe`.
