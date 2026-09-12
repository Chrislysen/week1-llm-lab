"""fetch_casino.py: download the CaSiNo corpus for the E30 feasibility work.

CaSiNo (Chawla, Ramirez, Clever, Lucas, May, Gratch; NAACL 2021), 1,030
human-human campsite negotiation dialogues, released by its authors under
**CC BY 4.0** (verified from the repository's LICENSE file, 2026-09-12).

The data is NOT committed to this repository: it is third-party, 4.3 MB, and
fetching it keeps attribution unambiguous. It lands in `data/casino/`, which
is gitignored.

    python fetch_casino.py           # download and report the shape
    python fetch_casino.py --stats   # also run the offer-then-decline census
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from collections import Counter

URL = "https://raw.githubusercontent.com/kushalchawla/CaSiNo/main/data/casino.json"
LICENSE_URL = "https://raw.githubusercontent.com/kushalchawla/CaSiNo/main/LICENSE"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "data", "casino")
OUT = os.path.join(OUT_DIR, "casino.json")

MARKERS = {"Submit-Deal", "Accept-Deal", "Reject-Deal", "Walk-Away"}
#: A quantified offer of one of the three issues.
ITEM = re.compile(r"\b(\d+|one|two|three|a)\s+(food|water|firewood|package)", re.I)
#: An explicit decline. Deliberately narrow: a counter-offer is a different
#: speech act and is excluded, so this is a lower bound on usable dialogues.
DECLINE = re.compile(
    r"\b(no,|nope|i can't|can not|cannot|won't work|that (won't|doesn't) work|"
    r"unfortunately|i'm afraid|too much|can'?t (do|accept|agree)|not (going to )?work|"
    r"i (would |'d )?(have to )?(decline|disagree|refuse)|sorry,? (but|i)|that is too|thats too)",
    re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "casino-fetch"})
    return urllib.request.urlopen(req, timeout=120).read()


def load(download=True):
    if not os.path.exists(OUT) and download:
        os.makedirs(OUT_DIR, exist_ok=True)
        raw = fetch(URL)
        with open(OUT, "wb") as f:
            f.write(raw)
        lic = fetch(LICENSE_URL)
        with open(os.path.join(OUT_DIR, "LICENSE"), "wb") as f:
            f.write(lic)
        print(f"downloaded {len(raw)} bytes to {OUT} (+ LICENSE)")
    with open(OUT, encoding="utf-8") as f:
        return json.load(f)


def utterances(dlg):
    return [t for t in dlg["chat_logs"] if t["text"] not in MARKERS]


def offer_decline_pairs(dlg, window=2):
    """[(offer_turn_index, decline_turn_index)] on the utterance list."""
    turns, out = utterances(dlg), []
    for i, t in enumerate(turns[:-1]):
        if not ITEM.search(t["text"]):
            continue
        for j in range(i + 1, min(i + 1 + window, len(turns))):
            if turns[j]["id"] != t["id"] and DECLINE.search(turns[j]["text"]):
                out.append((i, j))
                break
    return out


def census(d):
    c = Counter()
    pairs_per = Counter()
    for dlg in d:
        turns = utterances(dlg)
        c["utterances"] += len(turns)
        c["offers"] += sum(1 for t in turns if ITEM.search(t["text"]))
        c["declines"] += sum(1 for t in turns if DECLINE.search(t["text"]))
        p = offer_decline_pairs(dlg)
        c["pairs"] += len(p)
        pairs_per[min(len(p), 5)] += 1
        if dlg.get("annotations"):
            c["annotated_dialogues"] += 1
    c["dialogues"] = len(d)
    c["usable_dialogues"] = sum(v for k, v in pairs_per.items() if k >= 1)
    return c, pairs_per


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    d = load()
    print(f"CaSiNo: {len(d)} dialogues")
    if a.stats:
        c, pp = census(d)
        for k in ("dialogues", "annotated_dialogues", "utterances", "offers", "declines",
                  "pairs", "usable_dialogues"):
            print(f"  {k:22} {c[k]}")
        print("  dialogues by pair count:", dict(sorted(pp.items())))
