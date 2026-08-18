# External / Cold Auditor Verification — Audit Evidence Chain

**Review target:** AgentFactory OPRO baseline  
**Audited baseline SHA:** `20a54b92aad0857f75c6200d984b13098c6f4927`  
**Current disposition:** NOT ACCEPTED until every mandatory item resolves

## Evidence-chain questions

| ID | Auditor question | Required evidence | Decision |
|---|---|---|---|
| EX-01 | Does the workflow run resolve to the audited baseline SHA? | GitHub run metadata + head SHA | HOLD |
| EX-02 | Can every protected command be identified exactly? | execution evidence records | HOLD |
| EX-03 | Are exit codes explicit rather than inferred from job success? | per-command `exit_code` | HOLD |
| EX-04 | Are stdout and stderr both retained and hash-bound? | per-command hashes | HOLD |
| EX-05 | Is the machine-evidence artifact independently digest-verified? | artifact ZIP + expected digest + independent verification | HOLD |
| EX-06 | Are expected, observed, verified, and decision values separate? | Evidence Manifest | HOLD |
| EX-07 | Are application-reported commit labels distinguished from execution provenance? | `commit_sha` from workflow context + observed application output | HOLD |
| EX-08 | Does the Evidence Gate fail closed on missing or inconsistent evidence? | gate implementation + negative test evidence | HOLD |
| EX-09 | Can a reviewer reproduce the verification without trusting the prior auditor's conclusion? | external verification procedure | HOLD |
| EX-10 | Is auditor identity, timestamp, exceptions, and attestation recorded? | signed audit disposition | HOLD |

## Acceptance rule

External / Cold Audit = **ACCEPTED** only when EX-01 through EX-10 are all resolved PASS or explicitly classified N/A with documented rationale.

Any unresolved mandatory item is `INCONCLUSIVE` or `HOLD` and therefore blocks OPRO freeze/promotion.
