#!/usr/bin/env python3
"""Check that an incoming cross-session plan names a baseline this repository has.

LSN-0001 recorded a session that produced a plan to build FactoryRuntime, a
workflow state machine, CER gate enforcement, idempotency, and a run manifest
from scratch -- all of which already existed, tested, on another branch.
Following it would have meant rebuilding ~6,000 LOC. Its root cause:

    Each session/agent instance re-derives its plan from whatever branch it
    happens to be pointed at, with no branch-identity check as a mandatory
    first step.

Its `candidate_change.mandatory_first_step` prescribed exactly the check this
script performs. Its `validation_plan.regression_guard` said
`N/A (process lesson, not a code regression)` -- so nothing enforced it, and on
2026-08-30 the same failure arrived again as the APF Living Specification vNext
package: 368 lines specifying contracts that already run under CI, written
against no stated baseline at all. See LSN-0003.

"Process lesson" is why that lesson was unenforced, not why it was unenforceable.
This is the enforcement.

## What it checks

    1. Does the document declare a baseline (a commit SHA, or a branch)?
       No  -> REVIEW_REQUIRED. A plan whose assumed baseline is unknown cannot
              be diffed against the target, which is the whole check.
    2. Does this repository have that baseline?
       No  -> BLOCKED. The plan was written against something else.
    3. How far has the target moved since?
       Materially -> REVIEW_REQUIRED, with the divergence quantified.

It does not judge the plan's content. It answers only "what was this written
against, and is that still true", which is the question LSN-0001 says gets
skipped.

## Usage

    python3 scripts/verify_plan_baseline.py <plan.md> [--target main]
    python3 scripts/verify_plan_baseline.py --baseline <sha-or-branch> [--target main]

Exit: 0 PASS, 2 REVIEW_REQUIRED or BLOCKED (matching validate_project_context.py).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: A plan states its baseline in one of these shapes. Deliberately generous --
#: the failure this guards is a plan naming *nothing*, not one naming it oddly.
BASELINE_PATTERNS = (
    r"\b(?:baseline|audited_baseline_sha|baseline_sha|HEAD|commit|against)\b[^\n]{0,40}?\b([0-9a-f]{7,40})\b",
    r"\b([0-9a-f]{40})\b",
    r"\bbranch[:=]\s*[`'\"]?([\w./-]+)",
)
#: Divergence past which a plan's assumptions are worth re-reading, not the
#: point at which it is wrong. LSN-0001's case was 236 commits and ~6,000 LOC.
COMMITS_MATERIAL = 50
FILES_MATERIAL = 25


class BaselineError(RuntimeError):
    """The repository cannot answer the question -- distinct from a bad answer."""


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise BaselineError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def find_declared_baseline(text: str) -> str | None:
    """The first thing in the document that looks like a baseline, or None."""
    for pattern in BASELINE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def is_shallow() -> bool:
    """A shallow clone cannot tell 'this commit does not exist' from 'not fetched'.

    Claude Code web sessions and most CI checkouts are shallow. Reporting BLOCKED
    for a baseline that is merely beyond the fetch depth would make this guard
    fail for a legitimate context -- which is LSN-0002's failure exactly: a
    fail-closed guard tested under only one of the situations it runs in.
    """
    return git("rev-parse", "--is-shallow-repository") == "true"


def resolve(ref: str) -> str | None:
    try:
        return git("rev-parse", "--verify", f"{ref}^{{commit}}")
    except BaselineError:
        return None


def divergence(baseline: str, target: str) -> dict[str, object]:
    behind = int(git("rev-list", "--count", f"{baseline}..{target}"))
    ahead = int(git("rev-list", "--count", f"{target}..{baseline}"))
    changed = [line for line in git("diff", "--name-only", baseline, target).splitlines() if line]
    return {
        "merge_base": git("merge-base", baseline, target),
        "is_ancestor": subprocess.run(
            ["git", "merge-base", "--is-ancestor", baseline, target],
            cwd=ROOT, capture_output=True, check=False,
        ).returncode == 0,
        "target_ahead_by": behind,
        "baseline_ahead_by": ahead,
        "files_changed": len(changed),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", nargs="?", help="path to the incoming plan/handoff document")
    parser.add_argument("--baseline", help="baseline ref, instead of extracting one from a document")
    parser.add_argument("--target", default="HEAD", help="branch the work would actually land on (default: HEAD)")
    args = parser.parse_args(argv)

    if not args.plan and not args.baseline:
        parser.error("give a plan document or --baseline")

    declared = args.baseline
    if declared is None:
        path = Path(args.plan)
        if not path.exists():
            print(f"PLAN_BASELINE=BLOCKED: no such file: {path}")
            return 2
        declared = find_declared_baseline(path.read_text(encoding="utf-8", errors="replace"))

    if declared is None:
        print(f"PLAN_BASELINE_FAILURE=no baseline declared in {args.plan}")
        print("PLAN_BASELINE=REVIEW_REQUIRED")
        print("  A plan that does not say what it was written against cannot be")
        print("  diffed against the target. Per LSN-0001, establish the baseline")
        print("  before adopting any 'build X' instruction -- X may already exist.")
        return 2

    try:
        target_sha = resolve(args.target)
        if target_sha is None:
            print(f"PLAN_BASELINE=BLOCKED: target {args.target!r} does not resolve")
            return 2
        baseline_sha = resolve(declared)
        if baseline_sha is None:
            if is_shallow():
                print(f"PLAN_BASELINE_FAILURE=declared baseline {declared!r} is beyond this clone's depth")
                print("PLAN_BASELINE=REVIEW_REQUIRED")
                print(f"  This is a shallow clone ({git('rev-list', '--count', 'HEAD')} commits), so the")
                print("  baseline being unresolvable is not evidence that it is absent.")
                print("  Run `git fetch --unshallow` and re-check before concluding anything.")
                return 2
            print(f"PLAN_BASELINE_FAILURE=declared baseline {declared!r} is not in this repository")
            print("PLAN_BASELINE=BLOCKED")
            print("  The plan was written against a history this repository does not have.")
            return 2
        stats = divergence(baseline_sha, target_sha)
    except BaselineError as exc:
        print(f"PLAN_BASELINE=BLOCKED: {exc}")
        return 2

    print(f"DECLARED_BASELINE={declared} ({baseline_sha[:12]})")
    print(f"TARGET={args.target} ({target_sha[:12]})")
    print(f"MERGE_BASE={str(stats['merge_base'])[:12]}")
    print(f"BASELINE_IS_ANCESTOR_OF_TARGET={stats['is_ancestor']}")
    print(f"TARGET_AHEAD_BY={stats['target_ahead_by']} commits")
    print(f"BASELINE_AHEAD_BY={stats['baseline_ahead_by']} commits")
    print(f"FILES_CHANGED_SINCE_BASELINE={stats['files_changed']}")

    reasons = []
    if not stats["is_ancestor"]:
        reasons.append("baseline is not an ancestor of target: the two lines diverged")
    if int(stats["target_ahead_by"]) > COMMITS_MATERIAL:
        reasons.append(f"target moved {stats['target_ahead_by']} commits (> {COMMITS_MATERIAL})")
    if int(stats["files_changed"]) > FILES_MATERIAL:
        reasons.append(f"{stats['files_changed']} files differ (> {FILES_MATERIAL})")

    if reasons:
        for reason in reasons:
            print(f"PLAN_BASELINE_FAILURE={reason}")
        print("PLAN_BASELINE=REVIEW_REQUIRED")
        print("  Re-read the plan against the target before adopting it: what it")
        print("  proposes to build may already exist. This is LSN-0001's case.")
        return 2

    print("PLAN_BASELINE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
