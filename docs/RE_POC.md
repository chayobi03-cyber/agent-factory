# RE PoC Scope

## Objective
Validate that the Agent Factory kernel, contracts, retrieval, evidence verification, reporting, HOTL and benchmark system work on a real engineering domain without domain-specific kernel forks.

## Inputs
- legacy PDF
- test reports
- specifications
- measurement logs/exports
- internal wiki/Markdown

## Functions
- ingestion and revision detection
- hybrid retrieval
- evidence extraction
- claim generation
- claim-evidence verification
- natural-language QA
- comparative QA
- diagnosis workflow
- report generation
- HOTL review
- trace
- benchmark

## Initial RE ontology
Entities: equipment, DUT, chamber, antenna, cable, connector, enclosure, frequency, limit, test_setup, measurement, peak, mitigation, failure_mode.

Relations: tested_with, connected_to, measured_at, exceeds, mitigated_by, correlates_with, reproduced_by.

## Query taxonomy
1. definition / factual
2. document location
3. revision comparison
4. condition/cause analysis
5. RE failure diagnosis
6. evidence supporting or contradicting a hypothesis
7. recommended additional test
8. engineering report
9. evidence sufficiency / abstention

## PoC target
- 20+ representative legacy documents
- 150 benchmark cases
- 3 retrieval methods minimum
- 2 model providers minimum
- citation and evidence verification
- report output
- human correction capture

## Initial acceptance targets
These are calibration targets and must be revised after source characterization.
- Evidence Recall@10 >= 0.90
- Citation Accuracy >= 0.95
- Critical Claim Unsupported Rate <= 0.02
- Negative-case Abstention >= 0.90
- Revision correctness >= 0.95
- Trace completeness = 100%
- Domain Pack load without kernel modification = PASS
