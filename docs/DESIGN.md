# Design: Autonomous Multi-Agent Dev Pipeline

This document captures the technical design, architecture, and dependencies for the CrewAI + Git Worktrees autonomous development pipeline.

---

## Overview

A **CLI-driven autonomous software development pipeline** that runs multiple AI agents (Developer → Architect/Reviewer → QA) in a controlled, repeatable workflow.

**Core principles:**

- **Safe by default** — restricted shell access, no destructive commands
- **Deterministic & debuggable** — every run produces artifacts for reproduction/diagnosis
- **IDE-agnostic** — runs from any terminal (Cursor, VS Code, bare shell)
- **Single-feature MVP** — one "ticket" per run

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Orchestrator CLI                            │
│  (preflight → Phase A: Dev+Review → gate → Phase B: QA → artifacts) │
└─────────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Developer    │   │   Architect   │   │      QA       │
│    Agent      │   │     Agent     │   │    Agent      │
│ (worktree A)  │   │ (worktree B)  │   │ (worktree C)  │
└───────────────┘   └───────────────┘   └───────────────┘
        │                    │                    │
        └────────────────────┴────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  SafeShellTool  │
                    │ (allowlist/log) │
                    └─────────────────┘
```

### Components

| Component | Purpose |
|-----------|---------|
| **Orchestrator** | CLI entry point; runs preflight, phases, collects artifacts |
| **Preflight** | Validates env, worktrees, branches, deps before any agent runs |
| **SafeShellTool** | Wraps shell access with allowlist/denylist + audit logging |
| **FileWriteTool** | Write files within agent's worktree boundary |
| **FileReadTool** | Read files within agent's worktree boundary |
| **RunLogger** | Creates run directory, writes config/logs/artifacts |
| **Agents** | CrewAI agents (Developer, Architect, QA) with constrained tooling |

---

## Directory Layout

```
multi-agent-project/
├── main-repo/                  # Primary repo (this workspace)
│   ├── crewai/                 # AI orchestration code
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # CLI entry point
│   │   ├── crew_config.py      # Agent/task definitions
│   │   ├── preflight.py        # Pre-run validation
│   │   ├── tools/              # CrewAI tools
│   │   │   ├── __init__.py
│   │   │   ├── safe_shell.py   # Restricted shell access
│   │   │   └── file_write.py   # File writing within worktree
│   │   ├── models.py           # Pydantic models (Approval, etc.)
│   │   └── run_logger.py       # Logging/artifact management
│   ├── src/                    # Actual project code (non-AI)
│   ├── tests/                  # Project tests
│   ├── scripts/                # Helper scripts (smoke tests, etc.)
│   ├── .runs/                  # Run artifacts (created per-run)
│   │   └── <run_id>/
│   │       ├── config.json
│   │       ├── preflight.md
│   │       ├── commands.log
│   │       ├── dev_output.md
│   │       ├── review_output.json
│   │       ├── diff.patch
│   │       ├── qa_output.md
│   │       ├── pytest_output.txt
│   │       └── failure_summary.md  (only on failure)
│   └── pyproject.toml
├── developer-agent-work/       # Git worktree → feature/dev-task
├── architect-agent-work/       # Git worktree → feature/arch-review
└── qa-agent-work/              # Git worktree → feature/qa-test
```

**Important:** Worktrees are **siblings** of `main-repo`, not children.

**Directory purposes:**
- `crewai/` — AI orchestration, agents, tools (the pipeline itself)
- `src/` — Actual project source code that agents work on
- `tests/` — Project tests that QA agent runs
- `scripts/` — Helper scripts for smoke tests, setup, etc.

---

## Git Branching Strategy

| Branch | Owner | Purpose |
|--------|-------|---------|
| `main` | Human | Stable baseline |
| `feature/dev-task` | Developer Agent | Implementation work |
| `feature/arch-review` | Architect Agent | Review staging |
| `feature/qa-test` | QA Agent | Post-merge testing |

### Merge Flow

```
feature/dev-task ──► feature/arch-review ──► feature/qa-test
       │                    │
   (Developer)         (Architect merges both)
```

- Developer commits only to `feature/dev-task`
- Architect merges dev → arch → qa (if approved)
- QA tests only `feature/qa-test`

### Reset Policy

- Worktrees must be clean at run start; **we do not auto-stash**
- Optionally, orchestrator may fast-forward branches from `main` **only if configured** (default OFF)

---

## Collaborative Workflow

This pipeline uses **true multi-agent collaboration** — agents communicate, provide feedback, and iterate until the work is complete.

### Agent Roles

| Agent | Can Write Code? | Can Merge? | Primary Role |
|-------|----------------|------------|--------------|
| **Developer** | ✅ Yes | ✅ Yes | Implement, refine based on feedback, merge |
| **Architect** | ❌ No | ❌ No | Review code, provide architectural direction |
| **QA** | ❌ No | ❌ No | Run tests, examine for logical issues/breakage |

### Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION PHASE                      │
├─────────────────────────────────────────────────────────────┤
│  Developer: Implements feature spec                          │
│      ↓                                                       │
│  Developer: Requests review from Architect                   │
│      ↓                                                       │
│  Architect: Reviews diff, provides feedback                  │
│      ↓                                                       │
│  ┌──────────────────────────────────────────┐               │
│  │ REVIEW LOOP (until approved)             │               │
│  │   Developer refines based on feedback    │               │
│  │   Architect re-reviews                   │               │
│  └──────────────────────────────────────────┘               │
│      ↓                                                       │
│  Architect: Approves                                         │
│      ↓                                                       │
│  Developer: Merges to QA branch                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    VALIDATION PHASE                          │
├─────────────────────────────────────────────────────────────┤
│  QA: Runs tests + examines code for logical issues          │
│      ↓                                                       │
│  ┌──────────────────────────────────────────┐               │
│  │ QA LOOP (until passing)                  │               │
│  │   QA reports issues                      │               │
│  │   Developer fixes                        │               │
│  │   QA re-validates                        │               │
│  └──────────────────────────────────────────┘               │
│      ↓                                                       │
│  QA: Passes validation                                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
                    SUCCESS (exit 0)
```

### Key Principles

1. **Only Developer writes code** — Architect and QA provide direction, not implementations
2. **Only Developer merges** — Other agents checkout to review, but don't modify git state
3. **Iterative refinement** — Agents loop until quality bar is met, not just one pass
4. **True collaboration** — Agents communicate via CrewAI's multi-agent conversation

### Iteration Limits (MVP defaults)

To prevent runaway loops and token costs:

| Loop | Default Limit |
|------|---------------|
| Dev ↔ Architect review | 3 iterations |
| Dev ↔ QA validation | 2 iterations |

If limits are exceeded without success, the run fails with appropriate exit code.

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | SUCCESS (approved + QA passed) |
| `2` | MAX_ITERATIONS (review loop exceeded limit without approval) |
| `3` | INFRA FAIL (preflight, tool failure, exceptions) |
| `4` | QA FAIL (QA loop exceeded limit without passing) |

---

## SafeShellTool

The primary safety mechanism. Wraps all shell access with **role-based permissions**.

### Allowlist by Role

**All agents:**
- `python`, `pytest` — run code and tests
- `ls`, `cat` — read-only inspection (though prefer FileReadTool)

**Git commands by role:**

| Command | Developer | Architect | QA |
|---------|-----------|-----------|-----|
| `status` | ✅ | ✅ | ✅ |
| `diff` | ✅ | ✅ | ✅ |
| `log` | ✅ | ✅ | ✅ |
| `fetch` | ✅ | ✅ | ✅ |
| `checkout` | ✅ | ✅ | ✅ |
| `pull` | ✅ | ✅ | ✅ |
| `add` | ✅ | ❌ | ❌ |
| `commit` | ✅ | ❌ | ❌ |
| `push` | ✅ | ❌ | ❌ |
| `merge` | ✅ | ❌ | ❌ |

### Denylist (all agents)

Reject commands containing:
- `rm`, `mv`, `chmod`, `chown`, `sudo`
- `rebase`, `reset`, `clean`
- `checkout -f`, `push --force`, `-f` (force flags)

### Blocked Patterns

Reject if command contains:
- `;`, `&&`, `||`, `|` (chaining)
- `>`, `<` (redirects)
- `` ` ``, `$(` (subshells)
- Newlines

### Logging

Every command (accepted or rejected) is logged to `.runs/<run_id>/commands.log`:

```
ISO_TIMESTAMP | AGENT_NAME | WORK_DIR | ACCEPT/REJECT | COMMAND | RESULT_SUMMARY
```

### API Shape

Uses CrewAI's `@tool` decorator:

```python
from crewai.tools import tool

@tool("safe_shell")
def safe_shell(command: str) -> str:
    """Execute a shell command with safety restrictions."""
    # Validate against allowlist/denylist
    # Log to commands.log
    # Execute and return output
    ...
```

---

## FileWriteTool

Agents can write to any file within their assigned worktree.

### Capabilities

- Write or overwrite files within the agent's worktree
- Create directories as needed
- **No access outside the worktree boundary**

---

## FileReadTool

Agents can read any file within their assigned worktree.

### Capabilities

- Read file contents within the agent's worktree
- Return file contents as string
- **No access outside the worktree boundary**

---

## Tool Context Mechanism

Each agent operates in a different worktree. Tools need to know which worktree they're bound to.

### Factory Pattern

Create tool instances per-agent using a factory:

```python
from crewai.tools import tool
from pathlib import Path
from typing import Literal

AgentRole = Literal["developer", "architect", "qa"]

def create_tools(
    worktree_path: str,
    run_logger: "RunLogger",
    agent_name: str,
    role: AgentRole
):
    """
    Factory to create tools bound to a specific worktree.
    
    Tool permissions vary by role:
    - developer: read, write, full shell
    - architect: read only, restricted shell (no commits/merges)
    - qa: read only, restricted shell (no commits/merges)
    """
    
    worktree = Path(worktree_path).resolve()
    tools = []
    
    def validate_path(path: str) -> Path | None:
        """Validate path is within worktree. Returns resolved path or None."""
        target = (worktree / path).resolve()
        # Use is_relative_to for secure path validation (Python 3.9+)
        if not target.is_relative_to(worktree):
            return None
        return target
    
    @tool("read_file")
    def read_file(path: str) -> str:
        """Read a file from within the worktree."""
        target = validate_path(path)
        if target is None:
            return "ERROR: Path outside worktree boundary"
        if not target.exists():
            return f"ERROR: File not found: {path}"
        run_logger.log_command(agent_name, str(worktree), "ACCEPT", f"read_file: {path}", "OK")
        return target.read_text()
    
    tools.append(read_file)
    
    # Only Developer can write files
    if role == "developer":
        @tool("write_file")
        def write_file(path: str, content: str) -> str:
            """Write content to a file within the worktree."""
            target = validate_path(path)
            if target is None:
                return "ERROR: Path outside worktree boundary"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            run_logger.log_command(agent_name, str(worktree), "ACCEPT", f"write_file: {path}", "OK")
            return f"Wrote {len(content)} bytes to {path}"
        
        tools.append(write_file)
    
    # Shell tool with role-based restrictions
    @tool("safe_shell")
    def safe_shell(command: str) -> str:
        """Execute a shell command with safety restrictions."""
        # Role-based git command restrictions:
        # - developer: full git access (add, commit, push, merge)
        # - architect/qa: read-only git (status, diff, log, fetch, checkout)
        # Validation and execution logic...
        ...
    
    tools.append(safe_shell)
    
    return tools
```

**Key changes:**
- **Path validation uses `is_relative_to()`** — secure against path traversal attacks
- **Role-based tool permissions** — only Developer gets `write_file`
- **Shell restrictions vary by role** — Architect/QA get read-only git commands

---

## Preflight Checks

Run before any agent touches the repo. Fail fast with actionable errors.

### Checks Performed

1. **Environment** — `OPENAI_API_KEY` exists, model name present
2. **Worktrees exist** — all three sibling directories present
3. **Correct branches** — each worktree on expected branch (auto-checkout if wrong)
4. **Clean working trees** — `git status --porcelain` is empty
5. **Git remotes** — warn if `origin` missing (allow local-only mode)
6. **Tooling** — Python ≥3.10, test runner available

### Output

Writes `.runs/<run_id>/preflight.md` with:
- Paths, branches, tool versions
- Warnings
- Final PASS/FAIL state

---

## Agent Roles

### Role Summary

| Agent | Writes Code | Merges | Git Commands | Primary Function |
|-------|-------------|--------|--------------|------------------|
| Developer | ✅ | ✅ | Full access | Implement and refine |
| Architect | ❌ | ❌ | Read-only (checkout, fetch, diff) | Review and direct |
| QA | ❌ | ❌ | Read-only (checkout, pull) | Validate and report |

### Common Constraints (all agents)

- Must use provided tools for filesystem/git actions
- Operate only inside assigned worktree
- Must not bypass tool restrictions
- Must not change git config, remotes, hooks

### Developer Agent

- **Branch:** `feature/dev-task`
- **Worktree:** `developer-agent-work`
- **Can:** Write files, run tests, commit, push, merge
- **Tasks:**
  1. Inspect existing codebase
  2. Implement feature spec in `src/`
  3. Add tests in `tests/`
  4. Run tests until pass
  5. Commit and push
  6. Request review from Architect
  7. Refine based on feedback (loop)
  8. Merge to QA branch when approved
  9. Fix issues reported by QA (loop)
- **Output:** `dev_output.md` (implementation summary)

### Architect Agent

- **Branch:** `feature/arch-review`
- **Worktree:** `architect-agent-work`
- **Can:** Read files, checkout branches, view diffs
- **Cannot:** Write files, commit, merge, push
- **Tasks:**
  1. Checkout/fetch developer's branch
  2. Review diff for quality, architecture, safety
  3. Provide specific, actionable feedback
  4. Approve when quality bar is met
- **Output:** `review_output.json` (Approval struct)

```python
class Approval(BaseModel):
    approved: bool
    feedback: str  # Specific direction if not approved
    issues: list[str] = []  # Individual issues to address
```

### QA Agent

- **Branch:** `feature/qa-test`
- **Worktree:** `qa-agent-work`
- **Can:** Read files, checkout branches, run tests
- **Cannot:** Write files, commit, merge, push
- **Tasks:**
  1. Pull latest merged code
  2. Run test suite
  3. **Examine code for logical issues and potential breakage**
  4. Report specific issues with file/line references
  5. Re-validate after Developer fixes
- **Output:** `qa_output.json` (QAResult struct), `pytest_output.txt`

```python
class QAResult(BaseModel):
    tests_passed: bool
    test_summary: str
    logical_issues: list[str]  # Code review findings
    recommendations: list[str]  # Suggestions for Developer
```

---

## Agent Output Mechanism

Agents produce two types of output:

### 1. File Artifacts (agent writes directly)

Agents use `FileWriteTool` to write artifacts within their worktree:
- **Developer:** Writes code to `src/`, tests to `tests/`
- **Architect:** Writes `diff.patch` (via `git diff > file` equivalent using FileWriteTool)

### 2. Summary Artifacts (orchestrator captures)

The **orchestrator** captures the agent's final response and writes it to the run directory:
- `dev_output.md` — Developer's final summary
- `review_output.json` — Architect's `Approval` struct (parsed from response)
- `qa_output.md` — QA's test report summary
- `pytest_output.txt` — Raw test command output (captured by orchestrator)

This separation ensures:
- Agents write project files (code, tests) using tools
- Orchestrator manages run artifacts uniformly

---

## Agent Prompt Guidelines

Each agent's system prompt should include role-specific constraints and collaborative instructions.

### Common Constraints (all agents)

```
You are an AI agent working in a controlled, collaborative development environment.

CONSTRAINTS:
- You MUST use the provided tools for all file and git operations
- You can ONLY access files within your assigned worktree
- You MUST NOT attempt to bypass tool restrictions
- You MUST NOT modify git config, remotes, or hooks
- If a tool returns an error, report it and adjust your approach

COLLABORATION:
- Communicate clearly with other agents
- Provide specific, actionable feedback
- Reference file paths and line numbers when discussing code
```

### Developer Agent Prompt

```
You are the Developer agent. You are the ONLY agent that can write code and merge changes.

YOUR WORKTREE: developer-agent-work (branch: feature/dev-task)

CAPABILITIES:
- Read and write files
- Run tests
- Commit, push, and merge

WORKFLOW:
1. Read the existing codebase to understand structure
2. Implement the required changes in src/
3. Add tests in tests/
4. Run tests until they pass
5. Commit your changes with a clear message
6. Request review from the Architect agent
7. Address feedback from Architect (refine and re-request review)
8. When approved, merge to the QA branch
9. Address any issues reported by QA

Keep commits small and well-named. Be receptive to feedback.

OUTPUT: Provide a summary of what you implemented and any notes.
```

### Architect Agent Prompt

```
You are the Architect agent. You REVIEW code but do NOT write code.

YOUR WORKTREE: architect-agent-work (branch: feature/arch-review)

CAPABILITIES:
- Read files (read-only)
- View git diffs and logs
- Checkout branches to review

CANNOT:
- Write or modify files
- Commit, push, or merge

WORKFLOW:
1. Fetch/checkout the developer's branch
2. Review the diff for:
   - Code quality and style
   - Architectural soundness
   - Security and safety
   - Test coverage
3. Provide specific, actionable feedback with file/line references
4. Approve only when the quality bar is met

Be constructive but thorough. The Developer will implement your suggestions.

OUTPUT: Return JSON: {"approved": bool, "feedback": "...", "issues": [...]}
```

### QA Agent Prompt

```
You are the QA agent. You VALIDATE code but do NOT write code.

YOUR WORKTREE: qa-agent-work (branch: feature/qa-test)

CAPABILITIES:
- Read files (read-only)
- Run tests
- Checkout branches to review

CANNOT:
- Write or modify files
- Commit, push, or merge

WORKFLOW:
1. Pull the latest merged code
2. Run the test suite
3. Examine the code for:
   - Logical errors
   - Edge cases not covered
   - Potential runtime issues
   - Breaking changes
4. Report specific issues with file/line references
5. The Developer will fix issues you identify

Be thorough. Look beyond just test results — analyze the code itself.

OUTPUT: Return JSON: {"tests_passed": bool, "test_summary": "...", "logical_issues": [...], "recommendations": [...]}
```

---

## Dependencies

### Python Packages

```toml
[project]
requires-python = ">=3.10"
dependencies = [
  "crewai>=0.80.0",
  "pydantic>=2.0.0",
  "openai>=1.0.0",
  "pytest>=8.0.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
]
```

> **Note:** CrewAI version `>=0.80.0` targets late 2024 releases with stable `@tool` decorator support.

### LLM Configuration

CrewAI handles LLM configuration natively. No custom `LLMProvider` needed.

**Recommended models:**
- `gpt-4o` — default for all agents (fast, capable, good at code)
- `gpt-4-turbo` — alternative for complex reasoning
- `o1-preview` — for complex architectural decisions (Architect agent)
- `gpt-4o-mini` — budget option for simpler tasks

All model names are configurable via env/CLI.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_MODEL` | No | Default model (default: `gpt-4o`) |
| `OPENAI_TEMPERATURE` | No | Model temperature |
| `CREW_VERBOSE` | No | Enable verbose logging |

---

## CLI Interface

```bash
python -m crewai.orchestrator \
  --spec "Add feature X ..." \
  --run-id auto \
  --model gpt-4o \
  --test-cmd "python -m pytest" \
  --local-only \
  --verbose
```

| Flag | Default | Description |
|------|---------|-------------|
| `--spec` | (required) | Feature specification text |
| `--run-id` | `auto` | Run identifier (auto = timestamp) |
| `--model` | env or `gpt-4o` | LLM model name |
| `--test-cmd` | `python -m pytest` | Test runner command |
| `--local-only` | OFF | Skip remote push requirements |
| `--verbose` | OFF | Extra logging |
| `--force` | OFF | Override advisory lock if present |
| `--fast-forward` | OFF | Fast-forward branches from `main` before run |

---

## Logging & Observability

### Run Directory

All artifacts go to: `main-repo/.runs/<run_id>/`

### Required Artifacts

| File | When | Content |
|------|------|---------|
| `config.json` | Always | Spec, models, branches, SHAs, result |
| `preflight.md` | Always | Preflight check results |
| `commands.log` | Always | All shell commands (accepted/rejected) |
| `dev_output.md` | After Dev | Developer agent summary |
| `review_output.json` | After Arch | Approval struct |
| `diff.patch` | After Arch | Code diff |
| `qa_output.md` | After QA | QA agent summary |
| `pytest_output.txt` | After QA | Raw test output |
| `failure_summary.md` | On failure | Stage, last command, traceback, next steps |

### config.json Contents

Must include:
- Spec, model(s), test command
- Branch names, worktree paths
- Timestamp
- **Git commit SHAs for each branch at start and end**
- Result status and exit code

---

## IDE Compatibility

The system is CLI-first. IDEs are used for viewing artifacts, debugging, and optional manual edits.

### Recommended Usage Patterns

- Open `developer-agent-work/` as the primary IDE folder
- Use integrated terminal to run `python main-repo/orchestrator.py ...`
- **Avoid human edits to agent branches while a run is active**

### Optional Lock File

Advisory lock in `main-repo/.crew-lock` during a run:
- If present at start: refuse to run unless `--force`
- Delete at end or on exception

---

## Feature Spec Format (Recommended)

The orchestrator accepts free-text, but encourage this structure for better autonomy:

- **Problem statement**
- **Requirements** (bullets)
- **Acceptance criteria**
- **Constraints** (e.g., "no new dependencies")
- **Test instructions** (if special)

### Example

```
Problem:
Add helper function to return current date.

Requirements:
- Create src/date_utils.py
- Function get_current_date_iso() -> str returns YYYY-MM-DD

Acceptance criteria:
- New tests in tests/test_date_utils.py pass using python -m pytest
- No breaking changes
```

---

## Non-Goals (MVP)

Explicitly out of scope for MVP:

- Parallel features / multi-ticket scheduling
- Full PR + GitHub review automation
- Deep threat model / sandboxing beyond command allowlists
- Complex CI integration (GitHub Actions can come later)
- Multi-language project templates (assume Python initially)

---

## Future Enhancements

Documented for post-MVP development:

### Configuration File Support

YAML config for customizing behavior without code changes:
```yaml
# crewai/config.yaml
agents:
  developer:
    model: gpt-4o
    temperature: 0.7
  architect:
    model: o1-preview
    review_criteria:
      - "Check for security issues"
      - "Ensure test coverage"
workflow:
  max_review_iterations: 3
  max_qa_iterations: 2
```

### Iteration Limits

Configurable limits to prevent runaway loops:
- `MAX_REVIEW_ITERATIONS` — default 3
- `MAX_QA_ITERATIONS` — default 2
- Graceful failure when limits exceeded

### Mock Mode for Testing

`--mock` flag for deterministic testing:
- Canned agent responses
- Record/replay capability
- Enables fast CI without API calls

### Checkpoint/Resume

Save state between iterations:
- Resume from last checkpoint on crash
- Useful for long-running runs or debugging

### Metrics & Observability

Track and log:
- Token usage per agent
- Iteration counts per phase
- Time per phase
- Cost estimates

### Agent Abstraction Layer

Interface to decouple from CrewAI:
```python
class AgentRunner(Protocol):
    def run(self, task: str, tools: list) -> str: ...
```
Enables swapping to LangGraph, AutoGen, or raw OpenAI later.

### Worktree Simplification

Consider reducing from 3 to 2 worktrees:
- Developer worktree + main repo
- Architect/QA review via checkout in main repo
- Reduces setup complexity

---

## Security Notes

- SafeShellTool is the primary safety layer for shell commands
- FileWriteTool restricts writes to agent's worktree only
- Never run with elevated privileges
- Use a dedicated virtualenv
- **Network access is unrestricted** — agents can make network calls as needed
- `--local-only` default OFF (pushes enabled); ON for local-only iteration

---

## Definition of Done (MVP)

1. Preflight reliably blocks misconfigurations with clear errors
2. SafeShellTool blocks chaining/injection and logs every action
3. Architect approval gating prevents QA run when rejected
4. Every run creates `.runs/<run_id>/` with required artifacts
5. Smoke test can run end-to-end successfully on a trivial feature

