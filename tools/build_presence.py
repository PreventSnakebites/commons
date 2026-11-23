"""Build the presence table: which snakes live in which region, from GARD ranges.

Run from the project root:  python3 tools/build_presence.py ADM0   (then ADM1)
Resumable: it works in time-boxed passes and continues where it stopped.
Each country's own boundaries are used as published (decision 0005).
Run tools/prepare_gard_snakes.py first. Needs shapely 2.
"""
import csv, glob, json, os, sys, time
import shapely
from shapely.geometry import shape
from shapely.strtree import STRtree
from shapely.validation import make_valid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_canonical import Registry, REG

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVEL = sys.argv[1] if len(sys.argv) > 1 else "ADM0"
BUDGET = float(sys.argv[2]) if len(sys.argv) > 2 else 150
GB = os.path.join(ROOT, "sources", "raw", "geoboundaries")
RANGES = os.path.join(ROOT, "data", "work", "gard_snakes.csv")
csv.field_size_limit(1 << 30)
CAN = os.path.join(ROOT, "data", "canonical")
WORK = os.path.join(ROOT, "data", "work")
OUT = os.path.join(CAN, "presence_%s.csv" % LEVEL.lower())
REGIONS = os.path.join(CAN, "regions_%s.csv" % LEVEL.lower())
STATE = os.path.join(WORK, "presence_%s.state" % LEVEL.lower())
FIELDS = ["species_psb_id", "region_psb_id", "source", "gard_record", "gard_name", "name_match",
          "share_of_range", "share_of_region", "strength"]
start = time.time()
os.makedirs(WORK, exist_ok=True)

# Regions: every country's own boundaries at this level, each with a permanent ID
reg = Registry(REG)
NE = os.path.join(ROOT, "sources", "raw", "naturalearth")
NE_LICENCE = "Public Domain (Natural Earth)"
replace = {}
with open(os.path.join(ROOT, "sources", "curated", "boundary_replacements.csv"), newline="") as f:
    for r in csv.DictReader(f):
        replace[(r["country"], r["level"])] = r["natural_earth_code"]
ne_file = "ne_10m_admin_0_countries.geojson" if LEVEL == "ADM0" else "ne_10m_admin_1_states_provinces.geojson"
ne_feats = json.load(open(os.path.join(NE, ne_file)))["features"] if replace else []
geoms, region_ids, region_rows = [], [], []


def add_region(iso, g, key, name, iso_code, shape_id, source, licence, year):
    rid = reg.get("RG", key, "%s %s" % (iso, name))
    geoms.append(g)
    region_ids.append(rid)
    region_rows.append({"psb_id": rid, "level": LEVEL, "country": iso, "name": name, "iso_code": iso_code,
                        "boundary_id": shape_id, "boundary_source": source, "boundary_licence": licence,
                        "boundary_year": year})


for path in sorted(glob.glob(os.path.join(GB, "*", LEVEL, "*_simplified.geojson"))):
    iso = path.split(os.sep)[-3]
    if (iso, LEVEL) in replace:
        continue
    meta_path = path.replace("_simplified.geojson", "-metaData.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    for feat in json.load(open(path))["features"]:
        p = feat["properties"]
        try:
            g = make_valid(shape(feat["geometry"]))
        except Exception:
            continue
        add_region(iso, g, "gb:%s:%s:%s" % (iso, LEVEL, p.get("shapeID")), p.get("shapeName", ""),
                   p.get("shapeISO", ""), p.get("shapeID", ""), "geoBoundaries gbOpen: " + meta.get("boundarySource", ""),
                   meta.get("boundaryLicense", ""), meta.get("boundaryYearRepresented", ""))

# Countries whose gbOpen boundary cannot sit in an ODbL commons: Natural Earth instead (decision 0006)
for (iso, lvl), code in sorted(replace.items()):
    if lvl != LEVEL:
        continue
    for feat in ne_feats:
        p = feat["properties"]
        if LEVEL == "ADM0":
            if code not in (p.get("ADM0_A3"), p.get("ISO_A3"), p.get("GU_A3")):
                continue
            name, iso_code, fid = p.get("NAME", ""), p.get("ISO_A2", ""), str(p.get("NE_ID", ""))
        else:
            if p.get("adm0_a3") != code:
                continue
            name, iso_code, fid = p.get("name", ""), p.get("iso_3166_2", ""), str(p.get("ne_id", ""))
        g = make_valid(shape(feat["geometry"]))
        add_region(iso, g, "ne:%s:%s:%s" % (iso, LEVEL, fid), name, iso_code, fid,
                   "Natural Earth 10m, version 5.2.0-pre", NE_LICENCE, "")
reg.save()
with open(REGIONS, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(region_rows[0]))
    w.writeheader()
    w.writerows(region_rows)
tree = STRtree(geoms)
areas = [g.area for g in geoms]

match = {}
with open(os.path.join(CAN, "gard_species_match.csv"), newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["species_psb_id"]:
            match[int(r["gard_record"])] = r

done = int(open(STATE).read()) if os.path.exists(STATE) else -1
new_file = done < 0
out = open(OUT, "w" if new_file else "a", newline="", encoding="utf-8")
w = csv.DictWriter(out, fieldnames=FIELDS)
if new_file:
    w.writeheader()
last = done
with open(RANGES, newline="") as f:
    for row in csv.DictReader(f):
        i = int(row["gard_record"])
        if i <= done:
            continue
        if time.time() - start > BUDGET:
            break
        m = match.get(i)
        if m:
            rng = shapely.from_wkb(row["wkb_hex"])
            ra = rng.area or 1e-12
            for j in tree.query(rng):
                reg_g = geoms[j]
                if not rng.intersects(reg_g):
                    continue
                inter = rng.intersection(reg_g).area
                if inter <= 0:
                    continue
                sr, sg = inter / ra, inter / (areas[j] or 1e-12)
                strength = "core" if (sr >= 0.05 or sg >= 0.10) else ("present" if (sr >= 0.005 or sg >= 0.01) else "edge")
                w.writerow({"species_psb_id": m["species_psb_id"], "region_psb_id": region_ids[j], "source": "GARD 1.7",
                            "gard_record": i, "gard_name": m["gard_name"], "name_match": m["match"],
                            "share_of_range": round(sr, 5), "share_of_region": round(sg, 5), "strength": strength})
        last = i
out.close()
open(STATE, "w").write(str(last))
print("%s: processed up to GARD record %d" % (LEVEL, last))
