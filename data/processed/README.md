# Created datasets

## Aliases.csv
The aliases.csv file contains a dataset of aliases for elements, normalised to be searched by the parser. It also contains a type value. Each element has an alias that is identical to itself, with the highest possible weight. The type and weight are defined like so:
| Alias type                | Weight |
| ------------------------- | -----: |
| original                  |   1.00 |
| normalized                |   1.00 |
| transliteration           |   0.98 |
| historical descendant     |   0.95 |
| attested spelling variant |   0.90 |
| inferred/generated        |   0.75 |
| fuzzy match               |   0.50 |
<!-- TODO adjust these types and weights with more accurate values -->

## non_definition_starters.csv
This file contains words from the key english place names derivations field that come after a semi-colon, but aren't the start of a new derivation. This is needed as for some reason a semi-colon is both the separator for different derivations, but also used inside of the definitions themselves.