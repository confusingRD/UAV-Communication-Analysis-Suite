# UAV-CAS — Codex Project Rules

## 1. Development Principles

- Treat `plan.md` as the approved development roadmap.
- Preserve existing scientific functionality and backward compatibility.
- Prioritize physical correctness, numerical verification, reproducibility, and maintainability.
- Do not silently change physical assumptions, numerical methods, units, solver tolerances, or supported domains.
- Never claim verification or validation that has not actually been performed.

## 2. Mandatory Development History

Maintain these three files:

- `docs/CHANGELOG.md`
- `docs/DECISIONS.md`
- `docs/DEVLOG.md`

Create them if they do not exist.

Update the relevant files after every meaningful implementation task.

### CHANGELOG.md — What Changed?

Record meaningful changes to source code, scientific models, APIs, dependencies, and tests.

Each entry should include:

- Date (YYYY-MM-DD).
- Phase or milestone.
- Added, changed, fixed, or removed functionality.
- Main affected files.
- Backward compatibility implications, if applicable.

Do not record trivial formatting or temporary debugging edits unless they materially affect the implementation.

### DECISIONS.md — Why Was It Changed?

Record important architectural, scientific, and numerical decisions.

Each decision must contain:

- Unique decision ID (e.g., ADR-001).
- Date and status (Proposed, Accepted, Superseded).
- Problem or context.
- Decision and technical justification.
- Alternatives considered.
- Trade-offs and known limitations.
- Consequences for future development.

Especially document changes involving atmospheric models, refractivity, ray-tracing algorithms, numerical tolerances, boundary conditions, propagation assumptions, and link-budget methods.

Do not invent alternatives or rationales that were not actually considered. Mark unresolved decisions as Proposed.

Never delete or rewrite the history of an accepted decision. When a decision changes, create a new record and reference the superseded decision.

### DEVLOG.md — What Happened During Development?

For each meaningful work session or completed task, record:

- Date and phase.
- Objective.
- Implementation summary.
- Tests and commands actually executed.
- Test results (passed, failed, skipped, or not run).
- Bugs and numerical issues encountered.
- Solutions or workarounds.
- Remaining limitations and next steps.

Distinguish observed results from assumptions and planned work.

## 3. Scientific Traceability

For every significant scientific-model change, document:

- Governing equations or model references.
- Assumptions and validity domain.
- Relevant units and coordinate definitions.
- Verification tests and numerical evidence.
- Changes to previously established outputs.

Do not silently replace failed ray tracing with EER or another approximate method.

Preserve failed experiments and negative results in the development history when they influence engineering decisions.

## 4. Documentation Workflow

- Update the relevant history files within the same task as the implementation.
- Append new historical entries instead of overwriting earlier records.
- Use English for all technical history files.
- Reference relevant code paths, test files, and Git commit hashes when available.
- Do not fabricate timestamps, commit hashes, benchmark results, or test outcomes.
- Keep entries concise but sufficiently detailed to reconstruct why a change occurred.
- Avoid duplicating the complete technical report in the logs.
- Do not create commits unless explicitly authorized.

## 5. Completion Requirements

Before reporting an implementation task complete:

1. Run the relevant tests where feasible.
2. Update `CHANGELOG.md` for meaningful code changes.
3. Update `DECISIONS.md` if important decisions were made.
4. Append the task summary to `DEVLOG.md`.
5. Summarize any unresolved issues.
6. Report which history files were updated.

Documentation maintenance is part of the task's definition of done.