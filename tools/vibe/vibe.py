#!/usr/bin/env python3
"""vibe — give it links, get back things with the same vibe.

Accepts YouTube / SoundCloud / Vimeo / Bandcamp / ... (anything yt-dlp knows),
playlists, and plain web pages (Spotify, articles, ...) via their OpenGraph tags.

Pipeline
  1. extract   metadata for every seed (title, tags, description, channel, duration)
  2. profile   a weighted "vibe" keyword profile; terms shared by several seeds win
  3. search    several diverse queries in parallel (YouTube, SoundCloud)
  4. rank      semantic similarity to the seeds (sentence-transformers if installed,
               TF-IDF otherwise) + duration affinity + cross-query agreement
  5. diversify MMR re-ranking and a per-channel cap so you don't get 10 clips
               from one uploader

Usage
  python vibe.py URL [URL ...] [-n 15] [--source youtube,soundcloud] [--deep 20] [--json]
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import statistics
import sys
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from typing import Callable, Iterable, Sequence
from urllib.parse import parse_qs, urlparse

# --------------------------------------------------------------------------- model


@dataclass
class Item:
    url: str
    title: str = ""
    channel: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    duration: float | None = None
    views: int | None = None
    platform: str = ""
    # filled during ranking
    score: float = 0.0
    hits: int = 0

    @property
    def key(self) -> str:
        return canonical_key(self.url)

    def text(self) -> str:
        return " . ".join(
            p for p in (self.title, ", ".join(self.tags), self.channel,
                        clean_description(self.description)[:400]) if p
        )


def canonical_key(url: str) -> str:
    u = urlparse(url)
    host = u.netloc.lower().removeprefix("www.").removeprefix("m.").removeprefix("music.")
    if host == "youtu.be":
        return "yt:" + u.path.strip("/")
    if host.endswith("youtube.com"):
        if v := parse_qs(u.query).get("v"):
            return "yt:" + v[0]
        if m := re.match(r"/(?:shorts|embed|live)/([\w-]+)", u.path):
            return "yt:" + m.group(1)
    return host + u.path.rstrip("/")


# --------------------------------------------------------------------------- text

STOPWORDS = set("""
a an the and or but if then of to in on at by for with from into over under about as is
are was were be been being it its this that these those i me my we our you your he she they
them his her their what which who whom how why when where all any both each few more most
other some such no nor not only own same so than too very can will just do does did done
have has had having s t don should now ft feat featuring vs x
official video audio music lyric lyrics visualizer hd hq 4k 1080p full version remastered
new live clip mv m/v teaser trailer episode ep part pt prod produced
subscribe channel follow instagram twitter facebook tiktok spotify apple soundcloud patreon
merch link links listen stream download free http https www com watch like comment share
youtube please enjoy thanks thank check out out now available
και ο η το οι τα του της των τον την σε στο στη στην στον στα με για από ένα μια είναι
που θα να δεν μη ως ή αλλά επίσης
""".split())

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_WORD_RE = re.compile(r"[^\W\d_][\w'’&+-]*")
_BRACKETS_RE = re.compile(r"[\(\[\{][^\)\]\}]*[\)\]\}]")


def clean_description(desc: str) -> str:
    # Descriptions are mostly link spam after the first paragraph or two.
    lines = [ln for ln in (desc or "").splitlines() if not _URL_RE.search(ln) and "@" not in ln]
    return " ".join(lines)


def tokens(text: str) -> list[str]:
    out = []
    for w in _WORD_RE.findall(_URL_RE.sub(" ", text.lower())):
        w = w.strip("'’-&+")
        if len(w) > 1 and w not in STOPWORDS:
            out.append(w)
    return out


def ngrams(toks: list[str]) -> list[str]:
    return toks + [f"{a} {b}" for a, b in zip(toks, toks[1:])]


def item_terms(item: Item) -> Counter:
    """Field-weighted bag of words (+ bigrams) for one item."""
    c: Counter = Counter()
    for tag in item.tags[:40]:
        for t in ngrams(tokens(tag)):
            c[t] += 3.0
    for t in ngrams(tokens(_BRACKETS_RE.sub(" ", item.title))):
        c[t] += 2.5
    for t in tokens(" ".join(item.categories)):
        c[t] += 1.0
    for t in ngrams(tokens(clean_description(item.description)[:600])):
        c[t] += 0.6
    return c


# --------------------------------------------------------------------------- extraction


class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta: dict[str, str] = {}
        self._in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            k = (a.get("property") or a.get("name") or "").lower()
            if k and a.get("content") and k not in self.meta:
                self.meta[k] = a["content"]
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def extract_html(url: str, timeout: float = 15) -> Item:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (vibe)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(600_000).decode(r.headers.get_content_charset() or "utf-8", "replace")
    p = _MetaParser()
    p.feed(raw)
    m = p.meta
    keywords = [k.strip() for k in m.get("keywords", "").split(",") if k.strip()]
    return Item(
        url=url,
        title=html.unescape(m.get("og:title") or m.get("twitter:title") or p.title).strip(),
        description=html.unescape(m.get("og:description") or m.get("description") or ""),
        channel=m.get("og:site_name", "") or m.get("music:musician_description", ""),
        tags=keywords,
        platform=urlparse(url).netloc,
    )


def _from_info(info: dict) -> Item:
    url = info.get("webpage_url") or info.get("original_url") or info.get("url") or ""
    if info.get("ie_key") == "Youtube" and info.get("id") and "watch" not in url:
        url = f"https://www.youtube.com/watch?v={info['id']}"
    return Item(
        url=url,
        title=info.get("title") or "",
        channel=info.get("channel") or info.get("uploader") or info.get("artist") or "",
        description=info.get("description") or "",
        tags=list(info.get("tags") or []),
        categories=list(info.get("categories") or []) + list(info.get("genres") or []),
        duration=info.get("duration"),
        views=info.get("view_count"),
        platform=(info.get("extractor_key") or info.get("ie_key") or "").lower(),
    )


def _ydl(**extra):
    import yt_dlp  # imported lazily so the module is importable without it

    opts = {"quiet": True, "no_warnings": True, "skip_download": True,
            "noplaylist": True, "socket_timeout": 20, **extra}
    return yt_dlp.YoutubeDL(opts)


def extract(url: str, playlist_limit: int = 25) -> list[Item]:
    """Seed URL -> one Item, or several for a playlist / channel."""
    try:
        with _ydl(extract_flat="in_playlist", playlistend=playlist_limit) as y:
            info = y.extract_info(url, download=False)
        if info.get("entries"):
            return [_from_info(e) for e in info["entries"] if e and e.get("title")]
        if info.get("extractor_key") != "Generic" or info.get("title"):
            return [_from_info(info)]
    except Exception as e:  # unsupported site, geo block, ...
        log(f"  yt-dlp could not read {url} ({type(e).__name__}); trying page metadata")
    return [extract_html(url)]


def enrich(item: Item) -> Item:
    """Full metadata (tags, full description) for a flat search result."""
    try:
        with _ydl() as y:
            full = _from_info(y.extract_info(item.url, download=False))
        full.hits, full.url = item.hits, item.url
        return full
    except Exception:
        return item


SEARCH_PREFIX = {"youtube": "ytsearch", "soundcloud": "scsearch"}


def search(query: str, source: str, n: int) -> list[Item]:
    try:
        with _ydl(extract_flat=True) as y:
            info = y.extract_info(f"{SEARCH_PREFIX[source]}{n}:{query}", download=False)
        return [_from_info(e) for e in info.get("entries") or [] if e and e.get("title")]
    except Exception as e:
        log(f"  search failed [{source}] {query!r}: {type(e).__name__}")
        return []


# --------------------------------------------------------------------------- profile


def vibe_profile(seeds: Sequence[Item], top: int = 25) -> list[tuple[str, float]]:
    """Terms that describe the seeds; terms shared across seeds are boosted."""
    per_seed = []
    for s in seeds:
        c = item_terms(s)
        total = sum(c.values()) or 1
        per_seed.append({t: w / total for t, w in c.items()})
    score: dict[str, float] = defaultdict(float)
    coverage: Counter = Counter()
    for d in per_seed:
        for t, w in d.items():
            score[t] += w
            coverage[t] += 1
    n = len(per_seed)
    # Channel names are identity, not vibe — don't let them dominate queries.
    channel_toks = {t for s in seeds for t in tokens(s.channel)}
    ranked = []
    for t, w in score.items():
        boost = 1 + 2 * (coverage[t] - 1) / max(n - 1, 1) if n > 1 else 1
        if " " in t:
            boost *= 1.3
        if t in channel_toks:
            boost *= 0.35
        ranked.append((t, w * boost))
    # A word mostly seen inside a strong phrase ("hop" in "hip hop") is absorbed by it.
    best_phrase: dict[str, float] = defaultdict(float)
    for t, w in ranked:
        if " " in t:
            for word in t.split():
                best_phrase[word] = max(best_phrase[word], w)
    ranked = [(t, w) for t, w in ranked if " " in t or best_phrase[t] < 0.5 * w]
    ranked.sort(key=lambda x: -x[1])
    return ranked[:top]


def build_queries(seeds: Sequence[Item], profile: list[tuple[str, float]], k: int) -> list[str]:
    terms = [t for t, _ in profile]
    qs: list[str] = []

    def add(q: str):
        q = " ".join(dict.fromkeys(q.split()))  # drop repeated words, keep order
        if q and q.lower() not in {x.lower() for x in qs}:
            qs.append(q)

    # Multi-word tags that recur are usually genre/mood names ("dark ambient").
    tag_counts = Counter(t.lower() for s in seeds for t in s.tags if 1 < len(t.split()) <= 4)
    for tag, _ in tag_counts.most_common(2):
        add(tag)
    if terms:
        add(" ".join(terms[:3]))
    for i in range(1, min(len(terms), 6)):
        add(f"{terms[0]} {terms[i]}")
    for a, b in zip(terms[1::2], terms[2::2]):
        add(f"{a} {b}")
    # A cleaned seed title catches covers / remixes / "if you like X" mixes.
    for s in seeds[:2]:
        t = _BRACKETS_RE.sub(" ", s.title)
        t = re.split(r"\s[|•·]\s", t)[0]
        add(" ".join(t.split()[:6]))
    return qs[:k]


# --------------------------------------------------------------------------- similarity


class TfidfEmbedder:
    name = "tfidf"

    def fit(self, items: Sequence[Item]):
        bags = [item_terms(i) for i in items]
        df: Counter = Counter()
        for b in bags:
            df.update(b.keys())
        n = len(bags)
        self.idf = {t: math.log((1 + n) / (1 + d)) + 1 for t, d in df.items()}
        return [self._vec(b) for b in bags]

    def _vec(self, bag: Counter) -> dict[str, float]:
        v = {t: (1 + math.log(w)) * self.idf.get(t, 1.0) for t, w in bag.items() if w > 0}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norm for t, x in v.items()}

    @staticmethod
    def sim(a, b) -> float:
        if len(a) > len(b):
            a, b = b, a
        return sum(x * b.get(t, 0.0) for t, x in a.items())

    @staticmethod
    def mean(vs):
        acc: dict[str, float] = defaultdict(float)
        for v in vs:
            for t, x in v.items():
                acc[t] += x
        norm = math.sqrt(sum(x * x for x in acc.values())) or 1.0
        return {t: x / norm for t, x in acc.items()}


class SentenceEmbedder:
    """Multilingual semantic embeddings; picks up mood words a bag of words misses."""
    name = "sentence-transformers"
    MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(self.MODEL)

    def fit(self, items: Sequence[Item]):
        return list(self.model.encode([i.text() for i in items], normalize_embeddings=True))

    @staticmethod
    def sim(a, b) -> float:
        return float(a @ b)

    @staticmethod
    def mean(vs):
        import numpy as np
        m = np.mean(vs, axis=0)
        return m / (np.linalg.norm(m) or 1.0)


def make_embedder(kind: str):
    if kind in ("auto", "sbert"):
        try:
            return SentenceEmbedder()
        except Exception as e:
            if kind == "sbert":
                raise
            log(f"  sentence-transformers unavailable ({type(e).__name__}); using TF-IDF")
    return TfidfEmbedder()


def duration_affinity(d: float | None, ref: float | None) -> float:
    if not d or not ref:
        return 0.5
    return math.exp(-abs(math.log(d / ref)))


def rank(seeds: Sequence[Item], cands: Sequence[Item], embedder, n: int,
         per_channel: int = 2, mmr_lambda: float = 0.75,
         exclude_channels: Iterable[str] = ()) -> list[Item]:
    if not cands:
        return []
    vecs = embedder.fit(list(seeds) + list(cands))
    svecs, cvecs = vecs[:len(seeds)], vecs[len(seeds):]
    centroid = embedder.mean(svecs)
    durs = [s.duration for s in seeds if s.duration]
    ref_dur = statistics.median(durs) if durs else None
    max_hits = max(c.hits for c in cands) or 1

    for c, v in zip(cands, cvecs):
        sem = 0.6 * embedder.sim(v, centroid) + 0.4 * max(embedder.sim(v, s) for s in svecs)
        c.score = (0.78 * sem
                   + 0.14 * duration_affinity(c.duration, ref_dur)
                   + 0.08 * math.log1p(c.hits) / math.log1p(max_hits))

    # MMR: relevance vs. redundancy with what is already picked.
    excluded = {x.lower() for x in exclude_channels}
    pool = sorted(range(len(cands)), key=lambda i: -cands[i].score)[: max(n * 6, 60)]
    picked: list[int] = []
    per_ch: Counter = Counter()
    while pool and len(picked) < n:
        best, best_val = None, -1e9
        for i in pool:
            ch = cands[i].channel.lower()
            if ch in excluded or (ch and per_ch[ch] >= per_channel):
                continue
            red = max((embedder.sim(cvecs[i], cvecs[j]) for j in picked), default=0.0)
            val = mmr_lambda * cands[i].score - (1 - mmr_lambda) * red
            if val > best_val:
                best, best_val = i, val
        if best is None:
            break
        picked.append(best)
        pool.remove(best)
        per_ch[cands[best].channel.lower()] += 1
    return [cands[i] for i in picked]


# --------------------------------------------------------------------------- orchestration


def log(msg: str):
    print(msg, file=sys.stderr)


def find_similar(urls: Sequence[str], n: int = 15, sources: Sequence[str] = ("youtube",),
                 queries: int = 8, per_query: int = 15, deep: int = 0,
                 embedder: str = "auto", per_channel: int = 2, same_channel: bool = True,
                 min_duration: float = 0, extractor: Callable = extract,
                 searcher: Callable = search, enricher: Callable = enrich,
                 verbose: bool = False) -> dict:
    with ThreadPoolExecutor(8) as ex:
        seeds = [i for group in ex.map(extractor, urls) for i in group]
    seeds = [s for s in seeds if s.title]
    if not seeds:
        raise SystemExit("Could not read any of the given URLs.")

    profile = vibe_profile(seeds)
    qs = build_queries(seeds, profile, queries)
    if verbose:
        log("seeds:    " + " | ".join(s.title for s in seeds[:8]))
        log("vibe:     " + ", ".join(t for t, _ in profile[:15]))
        log("queries:  " + " | ".join(qs))

    jobs = [(q, src) for q in qs for src in sources]
    with ThreadPoolExecutor(8) as ex:
        results = list(ex.map(lambda j: searcher(j[0], j[1], per_query), jobs))

    seed_keys = {s.key for s in seeds}
    seed_titles = {s.title.lower() for s in seeds}
    merged: dict[str, Item] = {}
    for batch in results:
        for c in batch:
            if (c.key in seed_keys or c.title.lower() in seed_titles
                    or (min_duration and c.duration and c.duration < min_duration)):
                continue
            if c.key in merged:
                merged[c.key].hits += 1
            else:
                c.hits = 1
                merged[c.key] = c
    cands = list(merged.values())

    emb = make_embedder(embedder)
    excl = () if same_channel else {s.channel for s in seeds if s.channel}
    if deep and cands:
        # Cheap first pass, then fetch full tags/descriptions for the front-runners.
        prelim = rank(seeds, cands, emb, deep, per_channel=deep, mmr_lambda=1.0,
                      exclude_channels=excl)
        with ThreadPoolExecutor(8) as ex:
            rich = {i.key: i for i in ex.map(enricher, prelim)}
        cands = [rich.get(c.key, c) for c in cands]
    picks = rank(seeds, cands, emb, n, per_channel=per_channel, exclude_channels=excl)
    return {
        "seeds": [{"title": s.title, "url": s.url, "channel": s.channel} for s in seeds],
        "vibe": [t for t, _ in profile[:15]],
        "queries": qs,
        "embedder": emb.name,
        "candidates": len(cands),
        "results": [
            {k: v for k, v in asdict(c).items() if k in
             ("title", "url", "channel", "duration", "views", "platform", "score", "hits")}
            for c in picks
        ],
    }


def fmt_dur(d) -> str:
    if not d:
        return "  -  "
    d = int(d)
    h, m, s = d // 3600, d % 3600 // 60, d % 60
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Find links with a similar vibe.")
    ap.add_argument("urls", nargs="+", help="YouTube / SoundCloud / Spotify / any page; playlists too")
    ap.add_argument("-n", type=int, default=15, help="number of results (15)")
    ap.add_argument("--source", default="youtube",
                    help="comma list of: youtube, soundcloud (youtube)")
    ap.add_argument("--queries", type=int, default=8, help="search queries to run (8)")
    ap.add_argument("--per-query", type=int, default=15, help="results per query (15)")
    ap.add_argument("--deep", type=int, default=0, metavar="K",
                    help="fetch full metadata for the top K before final ranking (slower, better)")
    ap.add_argument("--embedder", choices=["auto", "sbert", "tfidf"], default="auto")
    ap.add_argument("--per-channel", type=int, default=2, help="max results per channel (2)")
    ap.add_argument("--other-channels", action="store_true",
                    help="exclude the seeds' own channels/artists")
    ap.add_argument("--min-duration", type=float, default=0, metavar="SEC",
                    help="drop results shorter than this (e.g. 61 to skip Shorts)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)

    sources = [s.strip() for s in a.source.split(",") if s.strip()]
    if bad := [s for s in sources if s not in SEARCH_PREFIX]:
        ap.error(f"unknown source(s): {', '.join(bad)}")
    out = find_similar(a.urls, n=a.n, sources=sources, queries=a.queries,
                       per_query=a.per_query, deep=a.deep, embedder=a.embedder,
                       per_channel=a.per_channel, same_channel=not a.other_channels,
                       min_duration=a.min_duration, verbose=a.verbose)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    print(f"\nvibe: {', '.join(out['vibe'][:10])}")
    print(f"{out['candidates']} candidates, ranked with {out['embedder']}\n")
    for i, r in enumerate(out["results"], 1):
        print(f"{i:>2}. {r['title'][:70]}")
        print(f"    {r['channel'][:30]:<30} {fmt_dur(r['duration']):>8}  "
              f"score {r['score']:.2f}  {r['url']}")


if __name__ == "__main__":
    main()
