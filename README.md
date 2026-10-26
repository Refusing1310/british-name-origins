# british-suffixes
The idea for this project is to take data for the names of towns and cities. This data is then mapped, with bigger towns having larger dots. The dots will be coloured by the origin of the suffixes and prefixes in the names (e.g Celtic) to produce a map of town name origins. 

## Note on language use
Throughout the project I'm using the word element to refer to roots, suffixes and prefixes.


## KEPN source lineage (development)

Fresh KEPN processing now writes three related CSVs:

- `ground_truth.csv`: original place-name derivations plus
  `KEPNSourceFile` (relative raw CSV filename) and `KEPNRecordNumber`
  (1-based data-record ordinal within that file, not physical text line).
- `elements.csv`: existing aggregate element records and their
  `Id`/`Frequency`, unchanged in shape.
- `element_sources.csv`: one row per parsed element occurrence, containing
  `GroundTruthRow` (0-based row in `ground_truth.csv`),
  `KEPNSourceFile`, `KEPNRecordNumber`, `ElementId` (foreign key to
  `elements.csv` `Id`), and `OccurrenceInRow` (1-based ordinal).
  The number of references to each `ElementId` equals its `Frequency`.

A place-name string is not a unique geographic identifier, and the presence
of a source-row reference does **not** itself prove that an OS mapped feature
has that derivation. Origin validation and location disambiguation remain
tracked under [issue #29](https://github.com/Refusing1310/british-name-origins/issues/29).
The original KEPN `C` code remains unresolved and distinct from the
`Celtic` language-family label. Do not use either as an automatic fallback
for the other.

Existing processed caches without source lineage must be regenerated from
the bundled raw KEPN CSVs; this PR does not silently overwrite them.
