"""Match GARD 1.7 snake ranges to PreventSnakebites species IDs.

Run from the project root:  python3 tools/match_gard.py
Writes data/canonical/gard_species_match.csv. Needs pyshp.
"""
import csv, os, re, collections
import shapefile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GARD = os.path.join(ROOT, "sources", "raw", "GARD", "Gard_1_7_ranges")
CAN = os.path.join(ROOT, "data", "canonical")

accepted, other = {}, collections.defaultdict(set)
with open(os.path.join(CAN, "species_names.csv"), newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if not r["psb_id"]:
            continue
        if r["status"] == "accepted":
            accepted[r["name"]] = r["psb_id"]
        elif r["status"] == "subspecies":
            parts = r["name"].split()
            if len(parts) >= 3:  # "Genus species subsp AUTHOR": take the trinomial's epithet as a binomial
                other[parts[0] + " " + parts[2]].add((r["psb_id"], "now_subspecies"))
        else:
            other[r["name"]].add((r["psb_id"], r["status"]))
family = {}
with open(os.path.join(CAN, "species.csv"), newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        family[r["psb_id"]] = r["family"]


def stem(epithet):
    """Strip Latin gender endings so malaccanus, malaccana and malaccanum compare equal."""
    return re.sub(r"(us|um|a|is|e|er|ra|rum|ae|i)$", "", epithet)


by_stem = collections.defaultdict(set)
for name, pid in accepted.items():
    g, e = name.split()[:2]
    by_stem[stem(e)].add((g, name, pid))

rows, seen = [], set()
rd = shapefile.Reader(GARD)
for i, rec in enumerate(rd.iterRecords()):
    d = rec.as_dict()
    if d["group"] != "snake":
        continue
    name = d["binomial"].strip()
    pid, how, note = "", "unmatched", ""
    if name in accepted:
        pid, how = accepted[name], "exact"
    elif name in other and len(other[name]) == 1:
        pid, how = next(iter(other[name]))
    elif len(name.split()) > 1:
        g, e = name.split()[:2]
        cands = by_stem.get(stem(e), set())
        same_genus = [c for c in cands if c[0] == g]
        same_family = [c for c in cands if family.get(c[2]) == d["family"]]
        if len(same_genus) == 1:
            pid, how, note = same_genus[0][2], "spelling_variant", "Epithet ending differs: " + same_genus[0][1]
        elif len(same_family) == 1:
            pid, how, note = same_family[0][2], "genus_change_probable", "Same epithet and family as " + same_family[0][1] + "; confirm"
        elif cands:
            note = "Epithet found in other families only: " + ", ".join(sorted(c[1] for c in cands)[:3])
    if how in ("exact", "spelling_variant", "now_subspecies", "former_combination"):
        seen.add(pid)
    rows.append({"gard_record": i, "gard_taxon_id": d["TaxonID"], "gard_name": name, "gard_family": d["family"],
                 "species_psb_id": pid, "match": how, "note": note})

with open(os.path.join(CAN, "gard_species_match.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
c = collections.Counter(r["match"] for r in rows)
print("GARD snake ranges:", len(rows), dict(c))
print("registry species with a confident GARD range:", len(seen - {""}), "of", len(accepted))
