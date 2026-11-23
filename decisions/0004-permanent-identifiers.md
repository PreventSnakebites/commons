# 0004: Permanent identifiers

- Status: accepted
- Date: 2026-11-23

## Decision

Every entity in the commons gets one permanent identifier of the form `U-PSB-<TYPE>-<NUMBER>-<CHECK>`, for example `U-PSB-SP-000001-4`.

- `U` marks the identifier as universal: one commons, for all people and all places.
- `PSB` is the PreventSnakebites namespace.
- `TYPE` is the kind of entity: `SP` species, `AV` antivenom product, `MF` manufacturer. New types are added by decision record.
- `NUMBER` is six digits, issued in sequence, carrying no meaning.
- `CHECK` is a Luhn mod 36 check character over the letters and digits, so a mistyped identifier is caught.

## Rules

- An identifier is minted once, recorded in `data/registry/ids.csv`, and never changed, reused or deleted.
- Identifiers carry no names, ranks or families, so no change in taxonomy or ownership can break them.
- A retired entity keeps its identifier, marked retired, with a pointer to what replaced it.
