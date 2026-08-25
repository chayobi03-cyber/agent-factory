# CER CI / Generic Evidence Lessons — 2026-08-20

## Session finding
The previously missing `CER_CI_PR_EXECUTION_LESSONS_2026-08-20.md` was not present on the active branch. The canonical Git state therefore takes precedence, and the requested artifact reference was treated as a governance-context gap rather than assumed to exist.

## Evidence execution lesson
PR #11 now has primary Actions evidence bound to the exact PR head SHA. Historical success must not be reused after a new commit; every new target SHA requires a new observed run whose `head_sha` matches the target SHA.

## Generic Evidence Contract lesson
Existing contracts already separated document revision, source evidence, claims, CER runtime, and trace. The remaining architectural gap was the absence of one domain-independent evidence envelope binding:

`execution identity → provenance → result → validation → artifact/digest → manifest → HOTL decision`

The new Generic Engineering Evidence Contract closes that composition gap without moving domain-specific semantics into the Kernel.

## Method rule
Use the execution loop:

`plan → state check → execute → evidence → RCA if needed → minimal correction → rerun → verification`

Do not infer GREEN from static artifacts, prior runs, or documentation state.

## Automation opportunities
- Validate generic evidence envelope shape in unit tests.
- Enforce target/runtime SHA equality before GREEN.
- Require artifact digest verification and evidence-manifest binding.
- Check that Domain Packs add payload mappings rather than Kernel schema branches.

## Keep under HITL
- audited baseline changes
- OPRO promotion
- GEPA implementation before its governed gate
- history rewrite / force push
- production changes
- changes that alter the meaning of core governance contracts
