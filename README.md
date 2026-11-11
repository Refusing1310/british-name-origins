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
## Personal-name meaning provenance (development)

The [curated name-link contract](docs/PERSONAL_NAME_LINKS.md) permits a separately
licensed, human-reviewed personal-name registry to be linked by local name ID
to an **exact KEPN source occurrence**. It preserves the generic personal-name
element and does not automatically invent linguistic meanings or import PASE/DMNES
material. There are no real linked names or rights-cleared semantic glosses yet.

## Place-name candidate matching (development)

The matching pipeline reads source-preserving aliases from
`data/processed/aliases.csv` and searches the OS `NAME` column.
It appends the following columns to the GeoDataFrame and its processed CSV:

- `ElementCandidates`: JSON array of matching candidate elements. Each candidate
  includes `element`, NFC-casefolded `matched_alias`, start/end offsets in the
  **normalised name** (end-exclusive), a purely textual `position`, KEPN
  `source_ids`, distinct `language_options`, and paired `source_records`
  (`id`, exact source `language` label, and `reconstructed` flag). The separate
  language summary is not a source-to-language mapping. Overlapping or
  contradictory candidates are retained rather than arbitrarily ranked.
- `ElementCandidateCount`: number of candidates, **not** number of
  confirmed etymological components.
- `ElementMatchStatus`: `missing_name`, `no_candidates`, or
  `unverified_candidates`.
- `KEPNNameMatches`: count of exact normalised KEPN place-name strings.
  This is **not** a geographically verified link between an OS feature and
  a particular KEPN record; homonymous locations may share a name.

All candidates are **unverified lexical hypotheses**; `position` describes
where an alias appears in the text, not a linguistically established prefix
or suffix. Short (1-2 character) aliases only match complete tokens to
reduce obvious false positives. The system does not assign a single language,
confidence score, final segmentation, or map colour based on these candidates.
The current matcher rejects alias spellings not supported by identity or
NFC/casefold normalisation of their source element. Curated historical
spellings require a separately reviewed and provenance-labelled rule.

Source language options preserve the distinction between the KEPN code `C`
(unresolved) and the literal `Celtic` family-level label; neither is
silently expanded, collapsed, or inferred from a substring match. Provenance
linkage required for verified origin maps is tracked in
[issue #29](https://github.com/Refusing1310/british-name-origins/issues/29).
Further parser quality and ranking are tracked in [issue #2](https://github.com/Refusing1310/british-name-origins/issues/2).

To run focused candidate tests:

```sh
python -m pytest -q tests/test_place_name_parser.py
```
