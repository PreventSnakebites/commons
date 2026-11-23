# 0006: Commons data is released under ODbL

- Status: accepted
- Date: 2026-11-23

## Decision

Data built on ODbL sources is released under the Open Database License (ODbL 1.0), so it stays open for everyone, forever: anyone may use, share and build on it, and whatever they build on it must stay open in the same way.

## Why

Most of the country and state boundaries the commons uses are published under ODbL, which requires derived databases to be shared under ODbL too. That share-alike promise matches the commons: no one can take what is built for the whole family and close it off.

## Compatibility of the other sources

- Public domain and CC0 (GARD, many boundaries): can be included freely.
- CC BY and similar attribution licences (Reptile Database, many boundaries, national open licences of Canada, France, Germany, Sweden, Belarus, Switzerland): can be included, with attribution kept per record.
- CC BY-SA (25 boundary files: AGO, AUT, BWA, GAB, GEO, GHA, GIN, GRD, GRL, JAM, KNA, MMR, MRT, NER, SLV, SYC, TUR, WSM, XKX): their own share-alike conflicts with ODbL. Needs a decision: permission from the publisher, a replacement from another open source, or keeping their derived rows in a separate CC BY-SA file.
- Unclear terms (POL country outline, "Other - Humanitarian"; TWN outline, Pixabay licence): to be replaced or confirmed before release.
- WHO data (antivenom records, range maps): terms still to be confirmed.

## Resolution (2026-11-23)

The 25 CC BY-SA boundary files and the 2 with unclear terms were replaced by public-domain Natural Earth boundaries for those countries (listed in `sources/curated/boundary_replacements.csv`). Their earlier region IDs are kept in the registry and listed in `data/registry/retired.csv`, never reused. No boundary in the commons now carries a licence incompatible with ODbL.
