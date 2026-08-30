# GEMINI.md

@docs/AGENT_CONTEXT.md

This file deliberately holds no content of its own. The agent context is
maintained once, in `docs/AGENT_CONTEXT.md`, and imported here and in
`CLAUDE.md` so both agents read the same text rather than two copies that
drift. `tests/test_agent_context.py` fails if a body appears here.

If your client does not resolve the `@` import above, read
`docs/AGENT_CONTEXT.md` before doing anything else.
