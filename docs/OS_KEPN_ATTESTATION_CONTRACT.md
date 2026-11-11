# OS location ↔ KEPN derivation: manual evidence-link contract (#29)

**Private, preliminary, source-preserving software. No place-name origin is automatically verified.**

KEPN derivations are indexed by the exact **\`KEPNSourceFile\` and \`KEPNRecordNumber\`** pair written by \`process_kepn_data\`; these are source-local row ordinals rather than physical line numbers. OS Open Names geographic locations are indexed by the **OS \`ID\`** column, not by \`NAME\`, and must be unique in the reviewed input. An identical name string may refer to distinct geographic features or to competing historical derivations. A matching prefix or suffix is merely a lexical lead.

\`data_processing/place_attestations.py\` accepts three separate in-memory dataframes:

- OS features: \`ID\`, \`NAME\` (other columns, including coordinates, remain untouched).
- Source KEPN rows: \`KEPNSourceFile\`, \`KEPNRecordNumber\`, \`PlaceName\` (original derivation and uncertainty text can remain alongside).
- **Human-entered proposals**: \`OSFeatureId\`, \`KEPNSourceFile\`, \`KEPNRecordNumber\`, \`Decision\` (\`supported_candidate\`, \`rejected_candidate\`, \`unresolved_candidate\`), \`EvidenceRef\`, \`ReviewerRef\`, \`NameMismatchReviewed\` (explicit Boolean).

Each proposed link requires a real, nonblank source reference and reviewer reference supplied externally. A positive proposal linking **different** place-name spellings additionally requires an explicit recorded name-discrepancy review. A plain text match **never generates a proposal** and cannot be used as a confirmation. This program cannot establish that the entered reviewer was qualified, rights have been cleared, documents actually support the claim, or the proposal is correct. The output therefore has **\`EvidenceStatus = review_record_claim_only_not_independently_verified\`** even for a positive entry.

Links to different source rows for the same OS feature remain separate. Two or more \`supported_candidate\` decisions get \`multiple_supported_candidates\`, rather than a fabricated unique answer. Unsupported and rejected candidates remain explicit; contradictory duplicates or unknown identifiers fail closed. A valid empty link table returns no claims.

## Future human review before mapping actual origin colours

1. Identify the precise geographic feature and county/locality, using original OS identifiers, location and primary historical references; distinguish same-named localities.
2. Check exact KEPN source file and ordinal against the raw source, original derivation, reconstructed forms, competing languages and any citation restrictions. Do **not** automatically equate the KEPN label \`C\` with \`Celtic\`.
3. Independently review the evidence, contradictions, spelling variants, and redistribution rights; record a genuine reviewer and rationale. \`EvidenceRef\` is a pointer supplied by a reviewer, **not** a cryptographically or academically verified fact.
4. Require separate product-scientific acceptance for any map display as an *attested origin*, with unresolved/conflicting candidates visibly unassigned. This module does not implement the origin-colouring policy or OS/KEPN join side effects.

## Reproduce

\`\`\`sh
python -m pytest -q tests/test_place_attestations.py tests/test_source_lineage.py
\`\`\`

All new tests use fictional localities and references, no external name datasets, geocoding, network calls, database writes, public release, or data scraping. See [#2](https://github.com/Refusing1310/british-name-origins/issues/2) for lexical matching and [#39](https://github.com/Refusing1310/british-name-origins/issues/39) for a future accessible map. This is a **partial implementation of #29**, not historic or geospatial verification.
