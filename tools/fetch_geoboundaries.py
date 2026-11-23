"""Fetch each country's own published boundaries (geoBoundaries gbOpen), ADM0 and ADM1.

Run from the project root:  python3 tools/fetch_geoboundaries.py
Each country's boundaries are kept as that country publishes them; disputed
areas therefore appear under every country that claims them (decision 0005).
"""
import json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "sources", "raw", "geoboundaries")
API = "https://api.github.com/repos/wmgeolab/geoBoundaries/contents/releaseData/gbOpen"
MEDIA = "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/gbOpen/{iso}/{lvl}/{name}"
LEVELS = ["ADM0", "ADM1"]


def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return True
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=120) as r, open(path + ".part", "wb") as f:
                f.write(r.read())
            os.replace(path + ".part", path)
            return True
        except Exception as e:
            err = e
            time.sleep(2)
    print("FAILED", url, err, flush=True)
    return False


os.makedirs(OUT, exist_ok=True)
with urllib.request.urlopen(API, timeout=60) as r:
    isos = sorted(x["name"] for x in json.load(r) if x["type"] == "dir")
json.dump(isos, open(os.path.join(OUT, "countries.json"), "w"))
print(len(isos), "countries", flush=True)
def fetch_country(iso):
    for lvl in LEVELS:
        d = os.path.join(OUT, iso, lvl)
        os.makedirs(d, exist_ok=True)
        for name in ["geoBoundaries-%s-%s_simplified.geojson" % (iso, lvl), "geoBoundaries-%s-%s-metaData.json" % (iso, lvl)]:
            get(MEDIA.format(iso=iso, lvl=lvl, name=name), os.path.join(d, name))
    print("done", iso, flush=True)


with ThreadPoolExecutor(max_workers=8) as pool:
    list(pool.map(fetch_country, isos))
print("ALL DONE", flush=True)
