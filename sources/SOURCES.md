# Sources

Every raw source, exactly as received. Never edited. Canonical data is rebuilt from these by the scripts in `tools/`.

## 1. The Reptile Database, checklist release June 2026

- File: `raw/reptile_checklist_2026_06.xlsx`
- SHA-256: `c9ec613aac4ad8f95aa5ee049c2f5c4e6016ed1c0ddaadf453319645a7ade268`
- Publisher: The Reptile Database (Uetz P., Freed P., Reyes F., Kudera J. & Hošek J., eds.), http://www.reptile-database.org
- Release date: 17 June 2026. Received: 23 November 2026.
- Contents: 12,650 reptile species; sheets "Checklist", "species-level changes", "Release notes".
- Scope taken: order Serpentes only (4,249 species, 33 families). See decision 0003.
- Licence: published to the Catalogue of Life and GBIF under CC BY (attribution). To confirm directly with the Reptile Database before the commons is released.
- Required citation: Uetz P., Freed P., Reyes F., Kudera J. & Hošek J. (eds.) The Reptile Database, http://www.reptile-database.org, accessed 23 November 2026.

## 2. WHO antivenom records

- File: `raw/who_antivenom_records.csv`
- SHA-256: `a24eb5539d176a8c33b3b61e2bdbc583b10f90c36ea8f55aae3f761590d525c5`
- Publisher: World Health Organization, snakebite antivenom data (public utility data store)
- Received: 23 November 2026.
- Contents: 815 records linking 274 snake species to 120 antivenom products from 52 manufacturers in 38 countries, with specificity and WHO assessment status.
- Licence: to be confirmed. WHO data usually carries its own terms of use; redistribution rights must be checked before release.

## Known issues found on import

- 33 rows are exact duplicates apart from their OBJECTID.
- 64 species are recorded with no specific antivenom available.
- 9 species names differ from the current Reptile Database taxonomy (spelling changes, genus moves, a species reduced to a subspecies, and one name not recognised). They are reconciled through the synonym layer, never by editing the source.

## 3. GARD 1.7, global distributions of terrestrial reptiles

- Folder: `raw/GARD/` (shapefile, 10,914 reptile ranges, of which 3,691 are snakes)
- Publisher: Global Assessment of Reptile Distributions; Dryad doi:10.5061/dryad.9cnp5hqmb, mirrored on Zenodo record 6499637. Published 27 April 2022.
- Received: 23 November 2026, each file downloaded individually from Zenodo.
- Checked: MD5 of .cpg, .dbf, .prj, .sbn, .sbx and .shp match the checksums published on Zenodo.
- Licence: CC0 (all Dryad data). Citation requested: Roll et al. 2017, Nature Ecology & Evolution 1:1677-1682; Caetano et al. 2022, PLoS Biology.

## 4. geoBoundaries gbOpen, each country's own boundaries

- Folder: `raw/geoboundaries/<ISO>/<ADM0|ADM1>/` (simplified GeoJSON and metadata per country)
- Publisher: geoBoundaries, William & Mary geoLab, via github.com/wmgeolab/geoBoundaries
- Received: 23 November 2026.
- Licence: open licences recorded per boundary in each metadata file (CC BY 4.0, ODbL, public domain and others). See decision 0005.

## 5. Natural Earth 10m admin boundaries

- Folder: `raw/naturalearth/` (admin 0 countries and admin 1 states and provinces, GeoJSON)
- Publisher: Natural Earth, via github.com/nvkelso/natural-earth-vector, version 5.2.0-pre
- SHA-256: countries `239eec57ac17f100a11e2536cffc56752c318b50ae765b0918ff7aab4ce8f255`; states `22d0e3ad85eb3e27f17cabf8ba2d50e554fbc27a87796ff891d958185da62fb5`
- Received: 23 November 2026.
- Licence: public domain.
- Used only for the 27 country-level boundaries whose geoBoundaries licence cannot sit inside an ODbL commons (see `curated/boundary_replacements.csv` and decision 0006).
