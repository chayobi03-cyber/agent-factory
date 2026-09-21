# Goal Alignment v0.1 — deterministic preservation gate

## Purpose

Goal Alignment v0.1 distinguishes plausible summarisation from preservation
of the user's actual objective, priorities, hard constraints, forbidden scope,
and success criteria.

The evaluator is deterministic and does not call an LLM. A free-tier GPT may
produce the candidate Goal Card; the candidate is then checked by
goal_alignment/evaluator.py.

## Test contract

| Case | Expected | Primary failure represented |
| --- | --- | --- |
| T01 | PASS | Contract-preserving Goal Card |
| T02 | BLOCK | Objective drift + hard constraint loss |
| T03 | BLOCK | Priority order drift |
| T04 | BLOCK | Missing hard constraint |
| T05 | BLOCK | Forbidden-scope contradiction |

## Files

- goal_alignment/gold/T01.json … T05.json: canonical contracts.
- goal_alignment/cases/goal_alignment_v0_1.jsonl: five runnable cases with natural-language input and a candidate Goal Card.
- goal_alignment/evaluator.py: deterministic evaluator and CLI.
- tests/test_goal_alignment.py: pytest regression suite.

Replace only candidate_goal_card in a case with the raw Goal Card returned by
a free-tier GPT. The evaluator then produces PASS/BLOCK and stable error codes
without another model call.

## Run

    python -m pytest tests/test_goal_alignment.py -q
    python -m goal_alignment.evaluator --cases goal_alignment/cases/goal_alignment_v0_1.jsonl

For an arbitrary GPT-generated Goal Card:

    python -m goal_alignment.evaluator --gold goal_alignment/gold/T01.json --candidate /path/to/gpt_goal_card.json

For a single candidate, exit code 0 means PASS and 1 means BLOCK. Batch mode
prints all verdicts and remains observational so a mixed regression fixture can
be inspected in CI.

## Error codes

- GA001 OBJECTIVE_DRIFT — objective identity changed.
- GA002 PRIORITY_DRIFT — required priority set/order changed.
- GA003 CONSTRAINT_MISSING — a required hard constraint was lost or weakened.
- GA004 SUCCESS_CRITERION_MISSING — a required success criterion was lost.
- GA005 FORBIDDEN_SCOPE_CONTRADICTION — protected scope was lost or a prohibited operating mode was introduced.
- GA006 SCHEMA_INVALID — the candidate cannot be evaluated safely.

## Fixture provenance

The repository did not contain the original five natural-language prompts or
raw free-tier GPT Goal Cards referenced by the session status (T01 PASS,
T02–T05 BLOCK). The five fixtures committed in this first executable gate are
therefore representative reconstructions of that stated pattern, not claims
that they are verbatim historical prompts.

Once the original five prompt/Goal Card pairs are available, replace the five
JSONL records and their gold contracts without changing the evaluator or pytest
harness. This preserves the project rule that missing historical evidence is
never silently invented.
