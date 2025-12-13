# AGENTS.md — Workspace Operating Rules (Design Repo)

This repo is your design + prototyping environment for building an autonomous multi-agent dev pipeline.
These rules govern how assistants should work in this workspace (Cursor / VS Code), not the eventual pipeline runtime.

## Mission
- Produce a safe, auditable, incremental implementation of the design described in `docs/DESIGN.md`.
- Prefer small, reviewable changes with tests.
- Keep everything reproducible via scripts and documented commands.

## Non-negotiables (Safety)
- Never run destructive commands: `rm`, `mv`, `chmod`, `chown`, `sudo`, disk tools, or global package installs.
- Never use risky git operations: `git reset --hard`, `git clean`, `git rebase`, `git push --force`.
- No command chaining in terminals: no `&&`, `;`, `|`, redirects, or subshells (`$(`, backticks).
- No secrets: don’t paste API keys or tokens into files, logs, or commits. Use env vars.
- No external side effects unless explicitly requested (no creating GitHub repos/issues/PRs, billing changes, etc.).

## Git Workflow (Required)

For every task:

1. **Create issue** — If a GitHub issue doesn't exist for the task, create one
2. **Create branch** — Branch from `main` using naming convention:
   - Features: `feature/<issue-number>-<short-description>`
   - Defects: `defect/<issue-number>-<short-description>`
3. **Checkout branch** — Switch to the new branch locally
4. **Implement** — Complete the task with tests
5. **Commit & push** — Commit changes and push to the branch
6. **Open PR** — Create a pull request to merge into `main`

Example:
```
feature/2-safe-shell-tool
defect/15-fix-path-validation
```

## Development Expectations

- Work in small steps. After each step:
  - explain what changed
  - how to run it
  - what remains
- If you need to add dependencies, update `pyproject.toml` (preferred) and explain why.
- Keep scripts deterministic: explicit inputs/outputs, no hidden behavior.

## Quality Bar
- Python >= 3.10
- Type hints where practical
- Clear error messages
- Minimal magic: configuration is explicit and serialized where appropriate
- Tests:
  - Add unit tests for critical safety logic (parsers/allowlisting)
  - Add one smoke test script to validate end-to-end locally

## Standard Commands (local dev)
- Create venv:
  - `python -m venv .venv`
  - activate: `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate` (Windows)
- Install:
  - `pip install -U pip`
  - `pip install -e ".[dev]"`
- Run tests:
  - `python -m pytest -q`

## Directory Conventions
- `docs/` — design notes, decisions, references
- `src/` — library code
- `tests/` — tests
- `scripts/` — runnable helpers

## “Ask Before Doing”
If you are about to:
- enable/configure MCP servers,
- introduce network calls,
- add a new framework,
- change branching strategy,
…then pause and surface the plan first.