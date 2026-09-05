# Handoff documents

- `STATUS.md` — the current state: status tuple, active artifacts and digests, CI state, test count, next ordered task. Overwritten each tranche. Start here after `CLAUDE.md`.
- `CR-EIB-0.N_Orchestrator_Handover.md` — one narrative per tranche: what was built, why, what was verified, what is next. Append-only; the highest number is the live continuation point named in `STATUS.md`. Earlier files carry a superseded banner and are history.

Durable rules (authority boundary, never-promote, environment, verification tiers, publishing) live in the repository root `CLAUDE.md`, not here.
