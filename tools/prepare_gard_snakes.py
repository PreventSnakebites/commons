"""Extract the GARD 1.7 snake ranges into a compact working file.

Run from the project root:  python3 tools/prepare_gard_snakes.py
Reads the shapefile record by record with numpy (low memory), simplifies each
ring to about 1 km (0.01 degree, well within the precision of expert range
maps), and writes data/work/gard_snakes.csv: GARD record number and WKB hex.
Resumable in time-boxed passes. Needs numpy and shapely 2.
"""
import csv, os, struct, sys, time
import numpy as np
import shapely
from shapely.geometry import Polygon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHP = os.path.join(ROOT, "sources", "raw", "GARD", "Gard_1_7_ranges")
CAN = os.path.join(ROOT, "data", "canonical")
OUT = os.path.join(ROOT, "data", "work", "gard_snakes.csv")
TOL = 0.01
BUDGET = float(sys.argv[1]) if len(sys.argv) > 1 else 150
start = time.time()
csv.field_size_limit(1 << 30)

with open(SHP + ".shx", "rb") as f:
    f.seek(100)
    raw = f.read()
offsets = [struct.unpack(">ii", raw[k:k + 8]) for k in range(0, len(raw), 8)]
snakes = sorted(int(r["gard_record"]) for r in csv.DictReader(open(os.path.join(CAN, "gard_species_match.csv"))))

done = set()
if os.path.exists(OUT):
    with open(OUT, newline="") as f:
        done = {int(r["gard_record"]) for r in csv.DictReader(f)}
mode = "a" if done else "w"
out = open(OUT, mode, newline="")
w = csv.writer(out)
if not done:
    w.writerow(["gard_record", "wkb_hex"])


def read_geom(fh, i):
    off, length = offsets[i]
    fh.seek(off * 2 + 8)
    buf = fh.read(length * 2)
    stype, = struct.unpack("<i", buf[:4])
    if stype not in (5, 15, 25):
        return None
    nparts, npts = struct.unpack("<ii", buf[36:44])
    parts = np.frombuffer(buf, "<i4", nparts, 44)
    pts = np.frombuffer(buf, "<f8", npts * 2, 44 + 4 * nparts).reshape(-1, 2)
    bounds = list(parts) + [npts]
    outers, holes = [], []
    for a, b in zip(bounds[:-1], bounds[1:]):
        ring = pts[a:b]
        if len(ring) < 4:
            continue
        x, y = ring[:, 0], ring[:, 1]
        signed = np.sum(x[:-1] * y[1:] - x[1:] * y[:-1])  # shapefile outer rings are clockwise (negative)
        poly = Polygon(ring).simplify(TOL, preserve_topology=True)
        if poly.is_empty or poly.area == 0:
            continue
        (outers if signed < 0 else holes).append(shapely.make_valid(poly))
    if not outers:
        return None
    g = shapely.union_all(outers)
    if holes:
        g = g.difference(shapely.union_all(holes))
    return shapely.make_valid(g)


n = 0
with open(SHP + ".shp", "rb") as fh:
    for i in snakes:
        if i in done:
            continue
        if time.time() - start > BUDGET:
            break
        g = read_geom(fh, i)
        if g is not None and not g.is_empty:
            w.writerow([i, shapely.to_wkb(g, hex=True)])
        n += 1
out.close()
print("prepared %d this pass; %d of %d snake ranges done" % (n, len(done) + n, len(snakes)))
