"""Build the PreventSnakebites canonical data from the raw sources.

Run from the project root:  python3 tools/build_canonical.py

Rules (see charter): raw sources are never edited; permanent IDs are minted
once, recorded in data/registry/ids.csv, and never changed or reused.
Needs Python 3 and openpyxl.
"""
import csv, os, re, datetime
from collections import OrderedDict
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "sources", "raw")
CUR = os.path.join(ROOT, "sources", "curated")
OUT = os.path.join(ROOT, "data", "canonical")
REG = os.path.join(ROOT, "data", "registry", "ids.csv")
CHECKLIST = os.path.join(RAW, "reptile_checklist_2026_06.xlsx")
WHO = os.path.join(RAW, "who_antivenom_records.csv")
RDB_SOURCE = "Reptile Database, release 2026-06"
WHO_SOURCE = "WHO antivenom records"
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
TODAY = datetime.date.today().isoformat()


def check_char(body):
    """Luhn mod 36 check character over the ID's letters and digits."""
    chars = [c for c in body if c != "-"]
    factor, total, n = 2, 0, len(ALPHABET)
    for c in reversed(chars):
        addend = factor * ALPHABET.index(c)
        factor = 1 if factor == 2 else 2
        total += addend // n + addend % n
    return ALPHABET[(n - total % n) % n]


def make_id(kind, number):
    body = "U-PSB-%s-%06d" % (kind, number)
    return body + "-" + check_char(body)


def clean(text):
    if text is None:
        return ""
    text = re.sub(r"\s+", " ", str(text)).strip()
    return "" if text == "<Null>" else text


class Registry:
    def __init__(self, path):
        self.path, self.rows, self.by_key, self.next = path, [], {}, {}
        if os.path.exists(path):
            with open(path, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.rows.append(r)
                    self.by_key[(r["entity"], r["key"])] = r["psb_id"]
                    num = int(r["psb_id"].split("-")[3])
                    self.next[r["entity"]] = max(self.next.get(r["entity"], 1), num + 1)

    def get(self, entity, key, label):
        if (entity, key) not in self.by_key:
            num = self.next.get(entity, 1)
            self.next[entity] = num + 1
            pid = make_id(entity, num)
            self.by_key[(entity, key)] = pid
            self.rows.append({"psb_id": pid, "entity": entity, "key": key, "label": label, "minted": TODAY})
        return self.by_key[(entity, key)]

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["psb_id", "entity", "key", "label", "minted"])
            w.writeheader()
            w.writerows(self.rows)


def write(name, fields, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("%-28s %6d rows" % (name, len(rows)))


def main():
    os.makedirs(OUT, exist_ok=True)
    reg = Registry(REG)

    # 1. Species: order Serpentes from the Reptile Database checklist
    ws = openpyxl.load_workbook(CHECKLIST, read_only=True)["Checklist"]
    rows = ws.iter_rows(values_only=True)
    head = [clean(h) for h in next(rows)]
    snakes = [dict(zip(head, r)) for r in rows]
    snakes = [s for s in snakes if clean(s["order"]) == "Serpentes"]
    snakes.sort(key=lambda s: clean(s["Species"]))
    species, names, by_name = [], [], {}
    for s in snakes:
        name = clean(s["Species"])
        pid = reg.get("SP", "rdb:%s" % int(s["sp#"]), name)
        by_name[name] = pid
        subsp = [clean(x) for x in str(s["Subspecies"] or "").split("\n") if clean(x)]
        species.append({"psb_id": pid, "scientific_name": name, "authority": clean(s["Author"]),
                        "family": clean(s["Family"]), "order": "Serpentes",
                        "rdb_species_no": int(s["sp#"]), "rdb_type_species": "yes" if clean(s["type_species"]) else "no",
                        "subspecies": " | ".join(subsp), "rdb_change_this_release": clean(s["changes"]),
                        "source": RDB_SOURCE})
        names.append({"psb_id": pid, "name": name, "status": "accepted", "source": RDB_SOURCE, "note": ""})
        for sub in subsp:
            names.append({"psb_id": pid, "name": sub, "status": "subspecies", "source": RDB_SOURCE, "note": ""})

    # 2. Name reconciliation for names recorded under older taxonomy
    recon = {}
    with open(os.path.join(CUR, "name_reconciliation.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            recon[r["name_as_recorded"]] = r
            target = by_name.get(r["accepted_name"], "")
            names.append({"psb_id": target, "name": r["name_as_recorded"], "status": r["relation"],
                          "source": WHO_SOURCE, "note": r["note"]})

    def resolve(name):
        if name in by_name:
            return by_name[name], "exact"
        r = recon.get(name)
        if r and r["accepted_name"] in by_name:
            return by_name[r["accepted_name"]], r["relation"]
        return "", "unresolved"

    # 3. Antivenom: manufacturers, products, product-species links, gaps
    with open(WHO, newline="", encoding="utf-8-sig") as f:
        who = [{k: clean(v) for k, v in r.items()} for r in csv.DictReader(f)]
    makers, products, links, gaps = OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict()
    for r in sorted(who, key=lambda r: (r["Manufacturer Name"], r["Antivenom Name"])):
        sp_id, match = resolve(r["Scientific Name"])
        if not r["Manufacturer Name"]:
            key = r["code_ssn"]
            g = gaps.setdefault(key, {"species_psb_id": sp_id, "name_as_recorded": r["Scientific Name"],
                                      "name_match": match, "who_species_code": r["code_ssn"],
                                      "note": "No specific antivenom available", "source_records": []})
            g["source_records"].append(r["OBJECTID"])
            continue
        mkey = r["Manufacturer Name"].lower()
        mid = reg.get("MF", mkey, r["Manufacturer Name"])
        makers.setdefault(mid, {"psb_id": mid, "name": r["Manufacturer Name"],
                                "country": r["Manufacturer Country"], "source": WHO_SOURCE})
        pkey = "%s|%s" % (mkey, r["Antivenom Name"].lower())
        pid = reg.get("AV", pkey, r["Antivenom Name"])
        p = products.setdefault(pid, {"psb_id": pid, "product_name": r["Antivenom Name"], "manufacturer_psb_id": mid,
                                      "who_assessment_status": r["Status"], "registration_notes": set(),
                                      "source": WHO_SOURCE})
        p["registration_notes"].add(r["Antivenom Comments"])
        lkey = (pid, r["code_ssn"])
        l = links.setdefault(lkey, {"antivenom_psb_id": pid, "species_psb_id": sp_id,
                                    "name_as_recorded": r["Scientific Name"], "name_match": match,
                                    "who_species_code": r["code_ssn"], "specificity": r["Specificity"],
                                    "source_records": [], "source": WHO_SOURCE})
        l["source_records"].append(r["OBJECTID"])

    for p in products.values():
        p["registration_notes"] = " | ".join(sorted(n for n in p["registration_notes"] if n))
    for x in list(links.values()) + list(gaps.values()):
        x["source_records"] = " ".join(sorted(x["source_records"], key=int))

    write("species.csv", list(species[0]), species)
    write("species_names.csv", ["psb_id", "name", "status", "source", "note"], names)
    write("manufacturers.csv", ["psb_id", "name", "country", "source"], list(makers.values()))
    write("antivenom_products.csv", ["psb_id", "product_name", "manufacturer_psb_id", "who_assessment_status",
                                     "registration_notes", "source"], list(products.values()))
    write("antivenom_species.csv", ["antivenom_psb_id", "species_psb_id", "name_as_recorded", "name_match",
                                    "who_species_code", "specificity", "source_records", "source"], list(links.values()))
    write("antivenom_gaps.csv", ["species_psb_id", "name_as_recorded", "name_match", "who_species_code",
                                 "note", "source_records"], list(gaps.values()))
    reg.save()
    print("registry: %d permanent IDs" % len(reg.rows))


if __name__ == "__main__":
    main()
