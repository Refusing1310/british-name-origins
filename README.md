# british-suffixes
The idea for this project is to take data for the names of towns and cities. This data is then mapped, with bigger towns having larger dots. The dots will be coloured by the origin of the suffixes and prefixes in the names (e.g Celtic) to produce a map of town name origins. 

## Note on language use
Throughout the project I'm using the word element to refer to roots, suffixes and prefixes.


## Place-name candidate matching (development)

The matching pipeline reads source-preserving aliases from
`data/processed/aliases.csv` and searches the OS `NAME` column.
It appends the following columns to the GeoDataFrame and its processed CSV:

- `ElementCandidates`: JSON array of matching candidate elements. Each candidate
  includes `element`, NFC-casefolded `matched_alias`, start/end offsets in the
  **normalised name** (end-exclusive), a purely textual `position`, KEPN
  `source_ids`, and distinct `language_options`. Overlapping or contradictory
  candidates are retained rather than arbitrarily ranked.
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
