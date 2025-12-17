# Conductor: Design Document

This document captures the technical design for a structured development workflow using an MCP server integrated with Cursor IDE.

---

## Overview

An **MCP-based workflow server** that guides developers through a structured dev process (Developer → Architect Review → QA Validation) while maintaining full Cursor IDE integration.

**Core principles:**

- **Cursor-native** — works within Cursor, preserving all IDE features (diffs, semantic search, etc.)
- **Structured workflow** — enforced phases with clear handoffs
- **Human-in-the-loop** — developer drives, MCP guides
- **Single conversation** — one chat, role-switching via MCP tools

---

## Why MCP Instead of Multi-Agent Pipeline?

We originally designed a CrewAI-based autonomous pipeline with separate git worktrees. After analysis, we pivoted to MCP for these reasons:

| CrewAI Pipeline | MCP Workflow |
|-----------------|--------------|
| CLI-only, no IDE integration | Full Cursor integration |
| Separate worktrees (context switching) | Single workspace |
| Fully autonomous (no intervention) | Human-in-the-loop |
| Complex infrastructure | ~200 lines of Python |
| Can run headless | Cursor-dependent |

The MCP approach trades full autonomy for a better developer experience.

**Tradeoffs accepted:**
- Same model reviewing its own work (self-review bias)
- Can't run in CI/headless mode
- Advisory workflow, not hard enforcement

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CURSOR IDE                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Chat / Composer                       │    │
│  │  User: "@workflow start 'Add date utility'"              │    │
│  │  Agent: [Implementation mode] Working on it...           │    │
│  │  Agent: "@workflow request_review ..."                   │    │
│  │  Agent: [Review mode] Examining changes...               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              MCP Workflow Server                         │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │    │
│  │  │ start_task  │  │request_review│  │ submit_qa   │     │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │    │
│  │                         │                                │    │
│  │                         ▼                                │    │
│  │              ┌─────────────────────┐                    │    │
│  │              │   Workflow State    │                    │    │
│  │              │   (JSON file)       │                    │    │
│  │              └─────────────────────┘                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [Native Cursor Tools: codebase_search, grep, read_file, etc.]  │
└─────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Purpose |
|-----------|---------|
| **MCP Workflow Server** | Python MCP server exposing workflow tools |
| **Workflow State** | JSON file tracking current phase, history, feedback |
| **Role Prompts** | Phase-specific instructions injected by tools |
| **Cursor Agent** | Does the actual work using native Cursor tools |

---

## Directory Layout

```
conductor/
├── workflow/                   # MCP workflow server
│   ├── __init__.py
│   ├── server.py               # MCP server entry point
│   ├── tools.py                # Workflow tool definitions
│   ├── state.py                # State management
│   └── prompts/                # Role-specific prompts
│       ├── developer.md
│       ├── architect.md
│       └── qa.md
├── src/                        # Project source code
├── tests/                      # Project tests
├── docs/                       # Documentation
│   ├── DESIGN.md               # This file
│   ├── TASKS.md                # Implementation tasks
│   └── decisions.md            # Architecture decisions
├── .workflow/                  # Workflow artifacts (created per-task)
│   └── <task_id>/
│       ├── state.json          # Current workflow state
│       ├── history.md          # Full workflow history
│       └── feedback/           # Review feedback files
├── pyproject.toml
└── README.md
```

---

## Workflow Phases

### Phase Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     IMPLEMENTATION PHASE                         │
├─────────────────────────────────────────────────────────────────┤
│  Role: Developer                                                 │
│  Can: Read files, write code, run tests, commit                 │
│                                                                  │
│  1. Understand the spec                                          │
│  2. Examine existing code patterns                               │
│  3. Implement changes                                            │
│  4. Write/update tests                                           │
│  5. Run tests locally                                            │
│  6. → request_review                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       REVIEW PHASE                               │
├─────────────────────────────────────────────────────────────────┤
│  Role: Architect (advisory)                                      │
│  Should: Review only, provide feedback, not write code          │
│                                                                  │
│  1. Examine the diff                                             │
│  2. Check code quality, patterns, architecture                  │
│  3. Identify issues with file/line references                   │
│  4. → approve OR request_changes                                │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
        [Changes Requested]              [Approved]
              │                               │
              ▼                               ▼
┌─────────────────────────┐   ┌─────────────────────────────────┐
│  Back to IMPLEMENTATION │   │        QA PHASE                  │
│  (with feedback)        │   ├─────────────────────────────────┤
└─────────────────────────┘   │  Role: QA (advisory)            │
                              │  Should: Validate, not fix      │
                              │                                  │
                              │  1. Run full test suite          │
                              │  2. Examine for logical issues   │
                              │  3. Check edge cases             │
                              │  4. → pass OR report_issues      │
                              └─────────────────────────────────┘
                                              │
                              ┌───────────────┴───────────────┐
                              ▼                               ▼
                        [Issues Found]                   [Pass]
                              │                               │
                              ▼                               ▼
                ┌─────────────────────────┐         ┌─────────────┐
                │  Back to IMPLEMENTATION │         │  COMPLETE   │
                │  (with QA feedback)     │         │  (exit 0)   │
                └─────────────────────────┘         └─────────────┘
```

### Phase Transitions

| From | To | Trigger | Notes |
|------|-----|---------|-------|
| (none) | Implementation | `start_task` | Begins new workflow |
| Implementation | Review | `request_review` | Developer ready for review |
| Review | Implementation | `request_changes` | Architect requests changes |
| Review | QA | `approve` | Architect approves |
| QA | Implementation | `report_issues` | QA found problems |
| QA | Complete | `pass` | All validation passed |

---

## MCP Tools

### `start_task`

Begin a new workflow.

```python
@tool("start_task")
def start_task(spec: str, task_id: str | None = None) -> str:
    """
    Start a new development task workflow.
    
    Args:
        spec: Description of the feature/fix to implement
        task_id: Optional ID (auto-generated if not provided)
    
    Returns:
        Developer role prompt with task context
    """
```

**Returns:** Developer role prompt + codebase context.

### `request_review`

Developer requests architecture review.

```python
@tool("request_review")  
def request_review(summary: str, files_changed: list[str]) -> str:
    """
    Request architecture review of current changes.
    
    Args:
        summary: Summary of what was implemented
        files_changed: List of modified files
    
    Returns:
        Architect role prompt with review context
    """
```

**Returns:** Architect role prompt + diff context.

### `approve`

Architect approves the changes.

```python
@tool("approve")
def approve(notes: str = "") -> str:
    """
    Approve the current changes and move to QA phase.
    
    Args:
        notes: Optional approval notes
    
    Returns:
        QA role prompt
    """
```

**Returns:** QA role prompt.

### `request_changes`

Architect requests changes.

```python
@tool("request_changes")
def request_changes(feedback: str, issues: list[str]) -> str:
    """
    Request changes from Developer.
    
    Args:
        feedback: Overall feedback
        issues: Specific issues to address (file:line references encouraged)
    
    Returns:
        Developer role prompt with feedback context
    """
```

**Returns:** Developer role prompt with accumulated feedback.

### `report_issues`

QA reports validation issues.

```python
@tool("report_issues")
def report_issues(test_results: str, issues: list[str]) -> str:
    """
    Report QA issues back to Developer.
    
    Args:
        test_results: Test output summary
        issues: Specific issues found
    
    Returns:
        Developer role prompt with QA feedback
    """
```

**Returns:** Developer role prompt with QA feedback.

### `pass_qa`

QA validation passed.

```python
@tool("pass_qa")
def pass_qa(summary: str) -> str:
    """
    Mark QA validation as passed. Workflow complete.
    
    Args:
        summary: Final QA summary
    
    Returns:
        Completion message with workflow summary
    """
```

**Returns:** Completion summary.

### `workflow_status`

Check current workflow state.

```python
@tool("workflow_status")
def workflow_status() -> str:
    """
    Get current workflow status.
    
    Returns:
        Current phase, iteration count, pending feedback
    """
```

### `abandon_task`

Cancel current workflow.

```python
@tool("abandon_task")
def abandon_task(reason: str) -> str:
    """
    Abandon the current task workflow.
    
    Args:
        reason: Why the task is being abandoned
    
    Returns:
        Confirmation message
    """
```

---

## Workflow State

State persisted to `.workflow/<task_id>/state.json`:

```json
{
  "task_id": "20241216_143022",
  "spec": "Add a date utility function that returns ISO format",
  "phase": "review",
  "iteration": 2,
  "created_at": "2024-12-16T14:30:22Z",
  "updated_at": "2024-12-16T14:45:00Z",
  "history": [
    {
      "phase": "implementation",
      "timestamp": "2024-12-16T14:30:22Z",
      "action": "start_task"
    },
    {
      "phase": "review", 
      "timestamp": "2024-12-16T14:35:00Z",
      "action": "request_review",
      "summary": "Added src/date_utils.py with get_iso_date()"
    },
    {
      "phase": "implementation",
      "timestamp": "2024-12-16T14:40:00Z", 
      "action": "request_changes",
      "feedback": "Add timezone support"
    }
  ],
  "feedback": [
    {
      "from": "architect",
      "iteration": 1,
      "issues": ["Add timezone parameter", "Missing docstring"]
    }
  ],
  "files_changed": ["src/date_utils.py", "tests/test_date_utils.py"]
}
```

---

## Role Prompts

### Developer Prompt (`prompts/developer.md`)

```markdown
# Developer Role

You are in DEVELOPER mode. You implement code changes.

## Capabilities
- Read and write files
- Run tests
- Use git (status, diff, add, commit)
- Use all Cursor tools (codebase_search, grep, etc.)

## Current Task
{spec}

## Workflow
1. Understand the existing codebase (use codebase_search)
2. Implement the required changes
3. Write/update tests
4. Run tests until passing
5. Call `request_review` with a summary when ready

## Previous Feedback (if any)
{feedback}

## Guidelines
- Follow existing code patterns
- Keep changes minimal and focused
- Write clear commit messages
- Reference specific files when summarizing
```

### Architect Prompt (`prompts/architect.md`)

```markdown
# Architect Role

You are in ARCHITECT mode. You review code but DO NOT write code.

## Your Job
- Review the changes for quality, architecture, security
- Provide specific, actionable feedback
- Reference file paths and line numbers

## Changes to Review
{summary}

## Files Modified
{files_changed}

## Review Checklist
- [ ] Follows existing patterns?
- [ ] Proper error handling?
- [ ] Test coverage adequate?
- [ ] Security implications?
- [ ] Clear naming and documentation?

## Actions
- If changes are good: Call `approve`
- If changes need work: Call `request_changes` with specific issues

## Important
Do NOT write code. Provide direction for the Developer to implement.
```

### QA Prompt (`prompts/qa.md`)

```markdown
# QA Role

You are in QA mode. You validate but DO NOT fix issues.

## Your Job
- Run the test suite
- Examine code for logical issues
- Check edge cases
- Report specific issues for Developer to fix

## Validation Steps
1. Run: `python -m pytest -v`
2. Check test output
3. Review code for:
   - Logic errors
   - Unhandled edge cases
   - Potential runtime issues
   - Breaking changes

## Actions
- If all validation passes: Call `pass_qa`
- If issues found: Call `report_issues` with specific problems

## Important
Do NOT fix issues. Report them clearly for the Developer.
```

---

## Codebase Context

The MCP server provides codebase awareness by:

### 1. File Tree in Prompts

At `start_task`, generate and include:

```python
def get_codebase_summary(root: Path) -> str:
    """Generate file tree and module summaries."""
    # List relevant files (respecting .gitignore)
    # Extract docstrings from Python modules
    # Return formatted summary
```

### 2. Workspace Rules Injection

Load and inject rules from:
- `AGENTS.md`
- `.cursor/rules/*.mdc`
- `.github/copilot-instructions.md`

```python
def load_workspace_rules(root: Path) -> str:
    """Load all workspace rules for context."""
```

### 3. Leverage Cursor's Tools

Remind agents they have access to:
- `codebase_search` — semantic search
- `grep` — text search  
- `read_file` — read files
- Native git integration

---

## Configuration

### MCP Server Config

Add to Cursor's MCP settings (`.cursor/mcp.json` or global):

```json
{
  "mcpServers": {
    "workflow": {
      "command": "python",
      "args": ["-m", "workflow.server"],
      "cwd": "/path/to/conductor"
    }
  }
}
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `WORKFLOW_DIR` | No | Override workflow state directory (default: `.workflow/`) |
| `WORKFLOW_MAX_ITERATIONS` | No | Max review iterations before warning (default: 5) |

---

## Safety Considerations

### What's Enforced

- Phase transitions only via MCP tools
- State is logged and auditable
- Iteration limits prevent infinite loops

### What's Advisory

- Role restrictions (Architect "shouldn't" write code, but Cursor can)
- The agent can ignore MCP tool suggestions
- No hard sandboxing

### Mitigations

1. **Self-review bias:** Use aggressive review prompts ("find at least 2 issues")
2. **Skipped phases:** Log all transitions, review history
3. **Runaway iterations:** Warn after N iterations, require explicit continue

---

## Limitations

### Cannot Do

- Run headless / in CI
- True multi-agent with separate contexts
- Hard enforcement of role restrictions
- Parallel workflows in same workspace

### Accepted Tradeoffs

- Self-review is "good enough" for most solo dev work
- Human is always in the loop to catch issues
- Cursor integration worth the autonomy tradeoff

---

## Future Enhancements

### Different Models Per Phase

If Cursor supports it, use different models:
- Developer: `gpt-4o` (fast, good at code)
- Architect: `claude-3-opus` (thorough review)
- QA: `gpt-4o` (test analysis)

### Integration with Git Hooks

Auto-trigger QA phase on commit via git hooks.

### Metrics & Reporting

Track across workflows:
- Average iterations per phase
- Common review feedback
- Time per phase

### Headless Mode (Separate Tool)

Keep a simplified CrewAI version for CI/batch use cases where Cursor integration isn't needed.

---

## Definition of Done (MVP)

1. MCP server runs and connects to Cursor
2. All workflow tools implemented and working
3. State persists across chat sessions
4. Role prompts include codebase context
5. Can complete a full workflow cycle (start → review → QA → complete)
6. Workspace rules injected into prompts
