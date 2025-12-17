# AGENTS.md — Workspace Operating Rules

This repo contains **Conductor**, an MCP workflow server that integrates with Cursor IDE.
These rules govern how AI assistants should work in this workspace.

## Mission

- Build an MCP server that guides developers through structured workflows
- Maintain full Cursor IDE integration (diffs, search, native tools)
- Keep it simple: ~200 lines of Python, not a complex framework
- Prefer small, reviewable changes with tests

## Non-negotiables (Safety)

- Never run destructive commands: `rm`, `mv`, `chmod`, `chown`, `sudo`, disk tools, or global package installs
- Never use risky git operations: `git reset --hard`, `git clean`, `git rebase`, `git push --force`
- No command chaining in terminals: no `&&`, `;`, `|`, redirects, or subshells (`$(`, backticks)
- No secrets: don't paste API keys or tokens into files, logs, or commits. Use env vars
- No external side effects unless explicitly requested (no creating GitHub repos/issues/PRs, billing changes, etc.)

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
feature/42-mcp-workflow-tools
defect/15-fix-state-persistence
```

## Development Expectations

- Work in small steps. After each step:
  - explain what changed
  - how to run it
  - what remains
- If you need to add dependencies, update `pyproject.toml` and explain why
- Keep scripts deterministic: explicit inputs/outputs, no hidden behavior

## Quality Bar

- Python >= 3.10
- Type hints where practical
- Clear error messages
- Minimal magic: configuration is explicit and serialized where appropriate
- Tests:
  - Add unit tests for state management and transitions
  - Add integration test for full workflow cycle

## Standard Commands (local dev)

- Create venv:
  - `python -m venv .venv`
  - activate: `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate` (Windows)
- Install:
  - `pip install -U pip`
  - `pip install -e ".[dev]"`
- Run tests:
  - `python -m pytest -q`
- Run MCP server (for debugging):
  - `python -m workflow.server`

## Directory Conventions

- `workflow/` — MCP server code
- `docs/` — design notes, decisions, references
- `src/` — library code (if any project code lives here)
- `tests/` — tests
- `scripts/` — runnable helpers
- `.workflow/` — workflow state files (auto-created, gitignored)

## "Ask Before Doing"

If you are about to:
- add new MCP tools beyond the core workflow
- introduce network calls
- add a new framework or major dependency
- change the state schema significantly

…then pause and surface the plan first.
