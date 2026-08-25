from scripts.validate_session_resume import _contains_any


def test_rc07_accepts_semantically_equivalent_canonical_constraints():
    handoff = (
        "audited OPRO baseline SHA immutable; "
        "state/documentation never substitutes for primary evidence; "
        "OPRO promotion forbidden; GEPA implementation forbidden; "
        "RE Domain implementation forbidden"
    )
    assert _contains_any(
        handoff,
        (
            "audited opro baseline sha must not change",
            "audited opro baseline sha immutable",
            "audited opro baseline sha - do not change",
        ),
    )
    assert _contains_any(
        handoff,
        (
            "pass without primary execution evidence forbidden",
            "state/documentation never substitutes for primary evidence",
        ),
    )
