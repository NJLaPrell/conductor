# Tasks: Autonomous Multi-Agent Dev Pipeline

## Project Summary

Build a CLI-driven autonomous dev pipeline using CrewAI and git worktrees. Three AI agents collaborate in isolated worktrees:

- **Developer** — implements features, addresses feedback, merges code
- **Architect** — reviews code, provides direction (read-only)
- **QA** — validates code, runs tests, reports issues (read-only)

The workflow is **collaborative and iterative**: agents communicate, provide feedback, and loop until quality standards are met.

**Target:** Python ≥3.10, CrewAI, OpenAI API

---

## Phase 0: Project Setup

Initial scaffolding before any implementation.

### 0.1 Package Structure ✅

- [x] Create `pyproject.toml` with dependencies (crewai, pydantic, openai, pytest)
- [x] Create `crewai/__init__.py`
- [x] Create `crewai/tools/__init__.py`
- [x] Create `src/.gitkeep` (placeholder for project code)
- [x] Create `tests/.gitkeep` (placeholder for tests)
- [x] Create `scripts/.gitkeep` (placeholder for helper scripts)

### 0.2 Git Worktree Setup Script ✅

- [x] Create `scripts/setup_worktrees.sh`
- [x] Create branches: `feature/dev-task`, `feature/arch-review`, `feature/qa-test`
- [x] Create worktrees as siblings: `../developer-agent-work`, `../architect-agent-work`, `../qa-agent-work`
- [x] Validate setup succeeded
- [x] Document usage in README

---

## Phase 1: Foundation (RunLogger + Tools)

Core infrastructure that everything else depends on. All code goes in `crewai/`.

### 1.1 RunLogger (`crewai/run_logger.py`) ✅

- [x] Create run directory at `.runs/<run_id>/`
- [x] Generate `config.json` with spec, model, branches, timestamps
- [x] Write `preflight.md` with check results
- [x] Append entries to `commands.log` (ISO timestamp, agent, dir, status, command, result)
- [x] Write `failure_summary.md` on failure (stage, last command, traceback, next steps)

### 1.2 SafeShellTool (`crewai/tools/safe_shell.py`) ✅

- [x] Implement using CrewAI's `@tool` decorator
- [x] Parse commands with `shlex.split`
- [x] Reject chaining metacharacters: `;`, `&&`, `||`, `|`, `>`, `<`, `` ` ``, `$(`
- [x] Allowlist executables: `git`, `python`, `pytest`, `ls`, `cat`
- [x] Allowlist git subcommands: `status`, `diff`, `log`, `add`, `commit`, `fetch`, `pull`, `push`, `checkout`, `merge`
- [x] Denylist tokens: `rm`, `mv`, `chmod`, `chown`, `sudo`, `rebase`, `reset`, `clean`, `-f` flags
- [x] Enforce one command per call
- [x] Integrate with RunLogger for audit logging
- [x] Return command output or rejection message

### 1.3 FileWriteTool (`crewai/tools/file_write.py`)

- [ ] Implement using CrewAI's `@tool` decorator
- [ ] Accept `path` and `content` parameters
- [ ] Validate path is within agent's worktree boundary
- [ ] Create parent directories if needed
- [ ] Write file content
- [ ] Log action to commands.log

### 1.4 FileReadTool (`crewai/tools/file_read.py`)

- [ ] Implement using CrewAI's `@tool` decorator
- [ ] Accept `path` parameter
- [ ] Validate path is within agent's worktree boundary
- [ ] Return file contents as string
- [ ] Handle file-not-found gracefully
- [ ] Log action to commands.log

### 1.5 Tool Factory (`crewai/tools/factory.py`)

- [ ] Implement `create_tools(worktree_path, run_logger, agent_name, role)` function
- [ ] Role parameter: `"developer"`, `"architect"`, or `"qa"`
- [ ] Return list of tools bound to specific worktree
- [ ] Path validation uses `Path.is_relative_to()` (Python 3.9+)
- [ ] Role-based permissions:
  - Developer: read_file, write_file, safe_shell (full git)
  - Architect: read_file, safe_shell (read-only git)
  - QA: read_file, safe_shell (read-only git)
- [ ] Each agent gets its own tool instances

---

## Phase 2: Preflight & Validation

Fail-fast checks before any agent runs.

### 2.1 Environment Checks

- [ ] Verify `OPENAI_API_KEY` is set
- [ ] Verify model name present (env or CLI, default `gpt-4o`)
- [ ] Check Python version ≥3.10
- [ ] Check test runner available (`python -m pytest`)

### 2.2 Worktree Validation

- [ ] Verify `../developer-agent-work` exists
- [ ] Verify `../architect-agent-work` exists
- [ ] Verify `../qa-agent-work` exists

### 2.3 Branch Verification

- [ ] Check each worktree is on expected branch
- [ ] Auto-checkout to correct branch if wrong (MVP default)
- [ ] Fail if checkout fails
- [ ] Optionally fast-forward branches from `main` if `--fast-forward` flag set (default OFF)

### 2.4 Clean State Checks

- [ ] Run `git status --porcelain` on each worktree
- [ ] Fail with instructions if dirty

### 2.5 Remote Checks (Optional)

- [ ] Warn if `origin` remote missing
- [ ] Allow local-only mode

### 2.6 Preflight Output

- [ ] Write all results to `.runs/<run_id>/preflight.md`
- [ ] Exit with code `3` on any failure

---

## Phase 3: CrewAI & Agents

Agent definitions, prompts, and LLM integration.

### 3.1 LLM Configuration

CrewAI handles LLM config natively — no custom provider needed.

- [ ] Configure agents to use model from env/CLI (default `gpt-4o`)
- [ ] Support per-agent model override if needed (e.g., `o1-preview` for Architect)
- [ ] Support temperature override via env var

### 3.2 Developer Agent (writes code, merges)

- [ ] Define role: "You are the ONLY agent that can write code and merge"
- [ ] Define capabilities: read, write, commit, push, merge
- [ ] Task: read repo, implement code in `src/`, add tests in `tests/`
- [ ] Task: run tests locally until pass
- [ ] Task: commit and push to `feature/dev-task`
- [ ] Task: request review from Architect
- [ ] Task: refine based on Architect feedback (loop)
- [ ] Task: merge to QA branch when approved
- [ ] Task: fix issues reported by QA (loop)
- [ ] Output: `dev_output.md` summary

### 3.3 Architect Agent (review only, no code)

- [ ] Define role: "You REVIEW code but do NOT write code"
- [ ] Define capabilities: read files, view diffs (read-only)
- [ ] Define restrictions: cannot write, commit, push, merge
- [ ] Task: fetch/checkout developer's branch
- [ ] Task: review diff for quality, architecture, safety
- [ ] Task: provide specific feedback with file/line references
- [ ] Task: approve only when quality bar is met
- [ ] Output: `Approval` pydantic model (`approved`, `feedback`, `issues[]`)
- [ ] Output: `review_output.json`

### 3.4 QA Agent (validation only, no code)

- [ ] Define role: "You VALIDATE code but do NOT write code"
- [ ] Define capabilities: read files, run tests (read-only)
- [ ] Define restrictions: cannot write, commit, push, merge
- [ ] Task: pull latest merged code
- [ ] Task: run test suite
- [ ] Task: examine code for logical issues and potential breakage
- [ ] Task: report specific issues with file/line references
- [ ] Output: `QAResult` pydantic model (`tests_passed`, `test_summary`, `logical_issues[]`, `recommendations[]`)
- [ ] Output: `qa_output.json`, `pytest_output.txt`

### 3.5 Tool Binding (role-based)

- [ ] Use tool factory to create tools per agent with role parameter
- [ ] Developer: gets read_file, write_file, safe_shell (full git)
- [ ] Architect: gets read_file, safe_shell (read-only git)
- [ ] QA: gets read_file, safe_shell (read-only git)
- [ ] Ensure each agent can only access its own worktree

---

## Phase 4: Orchestrator

CLI entry point and two-phase execution logic.

### 4.1 CLI Parsing (`crewai/orchestrator.py`)

- [ ] `--spec` (required): feature specification text
- [ ] `--run-id`: default `auto` (timestamp-based)
- [ ] `--model`: default from env or `gpt-4o`
- [ ] `--test-cmd`: default `python -m pytest`
- [ ] `--local-only`: toggle remote push requirement
- [ ] `--verbose`: toggle extra logging
- [ ] `--force`: override advisory lock if present
- [ ] `--fast-forward`: optional fast-forward branches from `main` before run (default OFF)

### 4.2 Run Initialization

- [ ] Generate run ID
- [ ] Initialize RunLogger
- [ ] Write initial `config.json`

### 4.3 Preflight Execution

- [ ] Run all preflight checks
- [ ] Exit `3` on failure

### 4.4 Implementation Phase (Dev ↔ Architect collaboration)

- [ ] Run Developer task: implement feature spec
- [ ] Developer requests review from Architect
- [ ] Architect reviews and provides feedback
- [ ] Loop: Developer refines → Architect re-reviews (max 3 iterations)
- [ ] Parse `Approval` from Architect output
- [ ] If max iterations without approval: write `failure_summary.md`, exit `2`
- [ ] Developer merges to QA branch
- [ ] Capture `dev_output.md`, `review_output.json`

### 4.5 Validation Phase (QA ↔ Developer collaboration)

- [ ] Run QA task: run tests + examine code
- [ ] QA reports issues
- [ ] Loop: Developer fixes → QA re-validates (max 2 iterations)
- [ ] If max iterations without passing: write `failure_summary.md`, exit `4`
- [ ] Capture `qa_output.json`, `pytest_output.txt`
- [ ] If all passing: exit `0`

### 4.6 Finalization

- [ ] Update `config.json` with final SHAs (per branch at start/end), result, exit code
- [ ] Clean up any advisory lock file

### 4.7 Advisory Lock (Optional)

- [ ] Create `.crew-lock` at start
- [ ] Refuse to run if lock exists (unless `--force`)
- [ ] Delete lock at end or on exception

---

## Phase 5: Testing & Validation

Prove the system works and is safe.

### 5.1 SafeShellTool Unit Tests

- [ ] Test: rejects `;` chaining
- [ ] Test: rejects `&&` chaining
- [ ] Test: rejects `|` piping
- [ ] Test: rejects `rm`, `mv`, `sudo`
- [ ] Test: rejects `git reset`, `git clean`
- [ ] Test: allows `git status`, `git diff`, `git add`, `git commit`
- [ ] Test: allows `python -m pytest`
- [ ] Test: logs all commands to audit log

### 5.2 FileWriteTool Unit Tests

- [ ] Test: writes file within worktree
- [ ] Test: creates parent directories
- [ ] Test: rejects path outside worktree
- [ ] Test: rejects absolute paths outside worktree
- [ ] Test: rejects path traversal (`../`)
- [ ] Test: logs all writes to audit log

### 5.3 FileReadTool Unit Tests

- [ ] Test: reads file within worktree
- [ ] Test: returns file contents as string
- [ ] Test: rejects path outside worktree
- [ ] Test: rejects path traversal (`../`)
- [ ] Test: handles file-not-found gracefully
- [ ] Test: logs all reads to audit log

### 5.4 Preflight Unit Tests

- [ ] Test: detects missing worktree directory
- [ ] Test: detects wrong branch, auto-checkouts
- [ ] Test: detects dirty worktree
- [ ] Test: passes when all conditions met

### 5.5 Smoke Test

- [ ] Script: `scripts/smoke_test_pipeline.py`
- [ ] Create temp repo with worktrees
- [ ] Run orchestrator on trivial spec (e.g., "add date util function")
- [ ] Assert exit code `0`
- [ ] Assert all required artifacts exist
- [ ] Assert tests pass in QA

### 5.6 Integration Validation

- [ ] Run full pipeline on real-ish spec
- [ ] Verify rejection flow (Architect rejects → exit `2`, no QA)
- [ ] Verify test failure flow (approved but tests fail → exit `4`)
- [ ] Verify artifact completeness

---

## Milestone: MVP Complete

When all phases are done:

1. ✅ Preflight blocks misconfigurations with clear errors
2. ✅ SafeShellTool blocks chaining/injection and logs everything
3. ✅ Architect approval gates QA phase
4. ✅ Every run produces `.runs/<run_id>/` with all artifacts
5. ✅ Smoke test passes end-to-end

