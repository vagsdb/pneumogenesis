"""Offline tests: network calls are replaced with fakes.  Run: python -m pytest tools/vibe"""
import vibe
from vibe import Item

SEEDS = {
    "https://www.youtube.com/watch?v=seed1": Item(
        url="https://www.youtube.com/watch?v=seed1", title="Rainy Night Lofi Beats [chill study mix]",
        channel="Dreamy Tapes", tags=["lofi hip hop", "chill beats", "study music", "rain"],
        duration=3600, description="Relax and study.\nhttps://spotify.com/x\nFollow @dreamy"),
    "https://youtu.be/seed2": Item(
        url="https://youtu.be/seed2", title="Late night jazzy lofi to relax",
        channel="Moon Cafe", tags=["lofi hip hop", "jazz hop", "chill beats"], duration=3000),
}

POOL = [
    Item(url="https://www.youtube.com/watch?v=a1", title="Chill lofi hip hop beats for studying",
         channel="Beat Lab", duration=3400),
    Item(url="https://www.youtube.com/watch?v=a2", title="Jazzy lofi rain beats - 1 hour",
         channel="Beat Lab", duration=3600),
    Item(url="https://www.youtube.com/watch?v=a3", title="Lofi beats chill night mix",
         channel="Beat Lab", duration=3500),
    Item(url="https://www.youtube.com/watch?v=b1", title="Coffee shop jazz hop chill beats",
         channel="Cafe Sounds", duration=2900),
    Item(url="https://www.youtube.com/watch?v=c1", title="Heavy metal guitar solo compilation",
         channel="Shred", duration=600),
    Item(url="https://www.youtube.com/watch?v=d1", title="lofi hip hop #shorts",
         channel="Clips", duration=30),
    Item(url="https://youtu.be/seed1", title="Rainy Night Lofi Beats [chill study mix]",
         channel="Dreamy Tapes", duration=3600),
]


def fake_extract(url):
    return [SEEDS[url]]


def fake_search(query, source, n):
    toks = set(vibe.tokens(query))
    return [Item(**{k: getattr(i, k) for k in ("url", "title", "channel", "duration")})
            for i in POOL if toks & set(vibe.tokens(i.title))][:n]


def run(**kw):
    return vibe.find_similar(list(SEEDS), extractor=fake_extract, searcher=fake_search,
                             enricher=lambda i: i, embedder="tfidf", **kw)


def test_profile_prefers_shared_terms():
    prof = [t for t, _ in vibe.vibe_profile(list(SEEDS.values()))]
    assert prof[0] in {"lofi hip", "lofi hip hop", "chill beats", "hip hop"}
    assert "spotify" not in prof and "dreamy" not in prof[:5]


def test_ranking_excludes_seeds_and_caps_channels():
    out = run(n=5)
    urls = [r["url"] for r in out["results"]]
    assert all("seed" not in u for u in urls)
    assert sum(r["channel"] == "Beat Lab" for r in out["results"]) <= 2
    assert out["results"][0]["channel"] in {"Beat Lab", "Cafe Sounds"}


def test_irrelevant_and_short_rank_low():
    titles = [r["title"] for r in run(n=10)["results"]]
    assert "Heavy metal guitar solo compilation" not in titles
    assert titles[-1] == "lofi hip hop #shorts"  # duration mismatch with 1h seeds
    out = run(n=10, min_duration=61)
    assert all(r["duration"] > 61 for r in out["results"])


def test_canonical_key():
    k = vibe.canonical_key
    assert k("https://youtu.be/abc") == k("https://www.youtube.com/watch?v=abc&t=3") == "yt:abc"
    assert k("https://m.youtube.com/shorts/abc") == "yt:abc"


def test_html_meta_parser():
    p = vibe._MetaParser()
    p.feed('<html><head><title>T</title><meta property="og:title" content="Song · Artist">'
           '<meta name="description" content="A dreamy track"></head></html>')
    assert p.meta["og:title"] == "Song · Artist" and p.title == "T"
