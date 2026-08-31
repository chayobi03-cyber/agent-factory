# Lesson Index

**Purpose:** the lesson register in one view — what each lesson says, whether
anything enforces it, and what it is waiting on. `docs/governance/INDEX.md`
does this for governance documents and `schemas/INDEX.md` for schemas; lessons
were the third register without one, which is how LSN-0001 sat unenforced long
enough to recur.

Lifecycle is defined by `docs/governance/HOTL_FAILURE_ANALYSIS_LOOP_V1.md` §5:

```text
lesson → proposed rule → regression witness → execution evidence → human review → governance update
```

**All three lessons are `status: candidate`.** An agent may carry a lesson to
"execution evidence" and no further — §4 reserves promotion for a human, and
forbids inferring approval from a passing test. The last two columns are
therefore the live question: a lesson with a regression witness is enforced
whether or not it is promoted; a lesson without one is a document.

| ID | Lesson | Enforced by | Status |
|---|---|---|---|
| **LSN-0001** | Verify the baseline a cross-session plan was written against before adopting any "build X" instruction — X may already exist on another branch. | `scripts/verify_plan_baseline.py`, `tests/test_plan_baseline.py` (added 2026-08-31) | candidate · **recurred once** (LSN-0003) |
| **LSN-0002** | A fail-closed guard must be tested under every situation it actually runs in. A guard self-tested only via `push` can make `pull_request` structurally unusable while looking correctly strict. | `tests/test_project_context_guard.py::test_resolve_branch_uses_base_ref_for_pull_request_events` | candidate · **held** (caught a defect 2026-08-31) |
| **LSN-0003** | `regression_guard: N/A` is a finding to be justified, not a field to be filled. A lesson recorded without one will recur. | `tests/test_plan_baseline.py` (6 cases) | candidate |

## What the register has cost and returned

**LSN-0001 recurred because nothing enforced it.** It carried
`regression_guard: N/A (process lesson, not a code regression)` and prescribed,
in its own `candidate_change.mandatory_first_step`, precisely the check that
would have caught the recurrence. On 2026-08-30 the APF Living Specification
package arrived: 368 lines specifying contracts that already run under CI,
written against no stated baseline. "Process lesson" described why it was
unenforced, not why it was unenforceable — the check is mechanical and now runs.

**LSN-0002 paid for itself the same week.** It caught a defect in the guard
written to enforce LSN-0001, before that guard shipped. The first version of
`verify_plan_baseline.py` reported `BLOCKED` for any baseline it could not
resolve — which in a shallow clone, what web sessions and CI checkouts get,
would have failed every handoff in this repository, since its own
`audited_baseline_sha` (`20a54b92`) lies outside the default fetch depth. An
enforced lesson found the bug; the register worked as designed.

## Using this register

- **Before adopting an incoming plan**, run
  `python3 scripts/verify_plan_baseline.py <document>`. That is LSN-0001's
  mandatory first step, and it is now one command.
- **When writing a new lesson**, `regression_guard` is the field that decides
  whether it is learned or merely recorded. If it is genuinely `N/A`, say why
  in the field rather than naming the category — "process lesson" is a
  classification, not a reason.
- **When a lesson recurs**, record the recurrence on the original rather than
  only opening a new one. LSN-0001 now carries a `recurrence:` block, so its
  cost is visible where a reader meets it.
- Promotion out of `candidate` is a human decision. This index does not make it.

Update this file whenever a lesson is added, enforced, or promoted — otherwise
it drifts the way the registers it describes did.
