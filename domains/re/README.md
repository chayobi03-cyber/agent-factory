# RE Domain Pack v0.1

This Domain Pack contains Radiated Emission (RE) semantics and policies without modifying the shared Agent Factory kernel.

## Capability boundary

The RE pack provides domain configuration for:

- ontology and terminology;
- source authority and revision policy;
- retrieval defaults;
- engineering reasoning policy;
- evidence/claim verification rules;
- report structure;
- benchmark query classes;
- risk thresholds.

It does not implement the shared CER runtime, WorkflowRun, Evidence object model, HOTL controller, or regression engine.

## Initial ontology

Entities and relations are derived from `docs/RE_POC.md` and are intentionally small enough to support the first ingestion/retrieval benchmark.

## Evidence requirements

RE claims must remain traceable to an authoritative revision and a stable document locator. Frequency/value/limit statements require compatible units and preserved test context when available.

## Initial workflow use cases

1. evidence-grounded factual QA;
2. document and revision lookup;
3. revision comparison;
4. condition/cause analysis;
5. RE failure diagnosis;
6. supporting/contradicting evidence search;
7. recommended additional-test generation;
8. engineering report generation;
9. evidence sufficiency / abstention.

## Non-goals

- direct equipment control;
- autonomous compliance certification;
- kernel forks for RE;
- provider-specific logic;
- replacing human approval for high/critical-risk actions.
