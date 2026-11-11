# Curated personal-name links: private research contract (#4)

The bundled KEPN data often gives an element like `Personal name (Old English)` with a generic meaning. **Do not replace that generic element or assign a place-name gloss to the etymology of an individual person's given name.** One generic element ID may occur in hundreds of distinct source rows, each with different, disputed or unnamed people.

`data_processing/personal_name_links.py` now accepts an **independently curated local registry** and an occurrence-level link table. It uses the existing `element_sources.csv` exact source-row/element/occurrence identifiers and preserves `KEPNSourceFile` / `KEPNRecordNumber`. A curated entry has a local `NameId`, spelling (`Form`), stated language, optionally a specific independently sourced `Meaning`, attribution references and an explicit `PermissionStatus`. It rejects a nonempty meaning without its own source reference and an affirmative human rights-review marker.

Every output link is **`unverified_candidate`**. A stable local `NameId` is not the PASE ID of a documented person, a proof that a name belongs in a historical place name, a scholar-endorsed meaning, or a licence to distribute someone else's database. Multiple alternatives remain distinct. This module does not modify the elements, create a finished personal-name lexicon, scrape online dictionaries, or change mapped origins.

## What remains before real-name imports

1. Identify a legally reusable external source for each specific name form and any semantic meaning, establish its licence/permissions for the intended publication model, and record scholarly provenance plus uncertainty. An accessible website does **not** necessarily grant redistribution rights.
2. Curate and review each exact KEPN source occurrence and any alternative names; distinguish a place-name gloss (e.g. *Abba's island*) from the *meaning of the personal name Abba*. Do not infer a personal-name root from a string merely because it resembles a documented name.
3. Produce the two optional curated CSV inputs from **licensed and independently reviewed** sources, validate them with `validate_curated_personal_name_links`, and inspect the unverified candidates before any approved downstream display or map semantics.
4. Test against multiple historical name forms, homonyms, source ambiguity, false positives and reconstructed or uncertain names before raising any evidence classification.

**No third-party lexicon contents are included or downloaded.** The standard elements output and KEPN source lineage remain unchanged. All tests use fictional records.

Research permissions checkpoint (11 November 2026): [PASE copyright](https://pase.ac.uk/about/copyright/) permits individual noncommercial access but states other use requires project-director consent; do not bulk-import PASE. DMNES rights for reuse/redistribution have not been established in this review. Prosopographical *person identities* and linguistic *name meanings* are different evidence categories.

This is a **schema/validation prerequisite**, not completion of issue #4's request for historically supported meanings. It authorises no external scraping, contact, rights transfer, public release or change to KEPN's historic meanings.
