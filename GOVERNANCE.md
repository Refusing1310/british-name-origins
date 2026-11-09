# Development governance and release policy

**Approved direction:** updated 9 November 2026. This is the standing Product Owner policy for this repository.

## Product Owner involvement

- The Product Owner's 9 November 2026 standing policy delegates private design, engineering, and protected-branch code merges (including `main`) without per-change approval, **provided the merge does not itself cause a public release**. See [cross-repository policy](https://github.com/Refusing1310/engineering-control/issues/128).
- Record material UX, architecture, security, data-flow and other product/design changes with rationale, tests, risks and rollback in the issue or PR; preserve independent technical reviews and exact-head checks where required.
- **Before each public release**, provide a concise summary of security and design/architecture changes since the previous release, exact release commit/artifact, independent security review, tests, unresolved risks and rollback; request an explicit Product Owner go/no-go.
- Code-merge delegation does not authorise spending, contracts, new secrets, live production/infrastructure changes, handling protected information, clinical/human activity, or weakening security gates. Project-specific legal, safety, privacy and consent requirements still apply.

## Security review: public-release gate, not a private-development gate

- **Mandatory independent security review applies to public releases only.** Obtain a genuine independent assessment against the exact proposed release commit/artifact, resolve material findings, retest and secure the Product Owner's explicit go/no-go before a public release.
- For internal feature branches, draft or ready PRs, offline testing, and private isolated QA previews, **do not require a separate formal or external security review merely because work is advancing**.
- Private work still requires proportionate security engineering: available CI, automated dependency/secret/static checks, least privilege, review of significant trust-boundary changes, accurate test evidence and no bypass of configured required checks. A passed scanner is not an independent public-release review.
- Public release includes making a service/site available to the public, publishing a distributable software release or shipping a change that users directly consume as a public release. On already-public repositories, source/PR contents are visible immediately: never publish secrets or private data. Public source visibility alone does not waive the security gate for actual releases.
- Maintain any **additional specialist** requirements for sensitive work (for example clinical, human-subject, legal, privacy, financial, or regulated activity); this policy does not authorise that work or waive its necessary safeguards.

## Branches, checks and deployment

- Work on topic branches and reviewable PRs. Protected-branch merges can proceed without per-merge Product Owner approval once enforced reviews, current exact-head CI/security checks and branch protections are satisfied and the merge does not cause a public release. Public deployment/publication and changes to credentials, production infrastructure or branch/security protections remain separately gated.
- Do not silently disable required CI/security checks, weaken workflow permissions, or claim a review occurred when it did not. If older reviewer-specific automation conflicts with this policy or is unavailable, propose a safe adjustment separately rather than bypassing the check.
- Verify checks against the current exact PR head; distinguish tested, skipped, pending, failed and untested evidence. Fix ordinary defects autonomously within approved scope.
- A private preview does not itself require the public-release independent assessment, but it must remain private/isolated and respect existing credential, environment, external-access and deployment restrictions.

## Project-specific limits

- Repository content is public: never put secrets or unapproved sensitive data into a branch/PR. A public software release still requires the pre-release gate below.

This document governs general decision thresholds. More protective project-specific safety or legal constraints continue to apply.
