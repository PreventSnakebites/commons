# PreventSnakebites canonical data

Built from `sources/raw/` by `tools/build_canonical.py`. Do not edit these files by hand: change the sources or the curated inputs and rebuild.
All files are UTF-8 CSV. Identifiers follow decision 0004 and are permanent.

| File | One row per | Key fields |
|---|---|---|
| `species.csv` | Snake species (order Serpentes) | `psb_id`, `scientific_name`, `authority`, `family`, `rdb_species_no` |
| `species_names.csv` | Name ever used for a species: accepted, subspecies, spelling variant, former combination | `psb_id`, `name`, `status` |
| `manufacturers.csv` | Antivenom manufacturer | `psb_id`, `name`, `country` |
| `antivenom_products.csv` | Antivenom product | `psb_id`, `product_name`, `manufacturer_psb_id`, `who_assessment_status` |
| `antivenom_species.csv` | Product recorded against a species | `antivenom_psb_id`, `species_psb_id`, `specificity`, `source_records` |
| `antivenom_gaps.csv` | Species recorded with no specific antivenom | `species_psb_id`, `who_species_code` |

`source_records` lists the original row numbers (OBJECTID) in the WHO file, so every link can be traced back to its source.
`name_match` shows how a recorded name was matched to a species: exact, through a spelling variant, a former combination, a subspecies, or unresolved (left unlinked until expert review).

## Ranges and regions (Phase 1)

| File | One row per | Key fields |
|---|---|---|
| `gard_species_match.csv` | GARD 1.7 snake range, matched to a species | `gard_record`, `gard_name`, `species_psb_id`, `match` |
| `regions_adm0.csv` | Country, from its own published boundary | `psb_id`, `country`, `name`, `boundary_licence` |
| `regions_adm1.csv` | State or province, from its country's own published boundaries | `psb_id`, `country`, `name`, `iso_code`, `boundary_licence` |
| `presence_adm0.csv` | Species range overlapping a country | `species_psb_id`, `region_psb_id`, `share_of_range`, `share_of_region`, `strength` |
| `presence_adm1.csv` | Species range overlapping a state or province | same as above |

`match` in `gard_species_match.csv`: `exact`, `spelling_variant`, `now_subspecies` and `former_combination` are confident; `genus_change_probable` needs expert confirmation; `unmatched` is not linked.

`strength` in the presence files: `core` (at least 5% of the range or 10% of the region), `present` (at least 0.5% of the range or 1% of the region), `edge` (a smaller overlap, often a mapping artefact along a border). Disputed land appears under every country that claims it (decision 0005).

Built by `tools/match_gard.py`, `tools/prepare_gard_snakes.py` and `tools/build_presence.py`. GARD ranges are simplified to about 1 km before overlap is measured.
