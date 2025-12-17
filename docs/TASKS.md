# Conductor: Tasks

## Project Summary

Build an MCP server that guides developers through a structured workflow (Developer → Architect Review → QA Validation) while maintaining full Cursor IDE integration.

**Target:** Python ≥3.10, MCP SDK, Cursor IDE

---

## Milestones

| Milestone | Description | Phases | Status |
|-----------|-------------|--------|--------|
| **M0: Clean Slate** | Project restructured for MCP approach | Phase 0 | 🔲 Not Started |
| **M1: Hello MCP** | Cursor can connect to server and see tools | Phase 1 | 🔲 Not Started |
| **M2: Workflow Works** | All workflow tools functional, state persists | Phase 2 | 🔲 Not Started |
| **M3: Context-Aware** | Prompts include codebase context and rules | Phase 3 | 🔲 Not Started |
| **M4: Production Ready** | Tested, documented, error handling complete | Phases 4-6 | 🔲 Not Started |

### Milestone Criteria

**M0: Clean Slate**
- [ ] `workflow/` directory exists with `__init__.py`
- [ ] `pyproject.toml` updated (no CrewAI dependency)
- [ ] Clean install works in fresh venv

**M1: Hello MCP**
- [ ] MCP server starts without errors
- [ ] Cursor connects and lists tools
- [ ] `workflow_status` returns "no active workflow"
- [ ] State model defined and serializes correctly

**M2: Workflow Works**
- [ ] Can start a task and get developer prompt
- [ ] Can transition through all phases
- [ ] State persists to `.workflow/` directory
- [ ] Invalid transitions return clear errors

**M3: Context-Aware**
- [ ] Developer prompt includes file tree summary
- [ ] Developer prompt includes workspace rules (AGENTS.md)
- [ ] Prompts render correctly with placeholders filled

**M4: Production Ready**
- [ ] Unit tests pass for state and transitions
- [ ] Integration test completes full workflow cycle
- [ ] Manual Cursor test documented and passing
- [ ] Error messages are actionable
- [ ] README installation steps verified

---

## Current Status

**Active Milestone:** M0: Clean Slate

**Blockers:** None

**Next Action:** Create `workflow/` directory structure

---

## Phase 0: Project Restructure

*Milestone: M0 — Clean Slate*

Clean up from previous CrewAI approach and set up new structure.

### 0.1 Directory Restructure

- [ ] Create `workflow/` directory for MCP server code
- [ ] Create `workflow/__init__.py`
- [ ] Create `workflow/prompts/` directory
- [ ] Create `.workflow/.gitkeep` for state directory
- [ ] Decide: keep or remove `crewai/` directory (some code may be reusable)

### 0.2 Dependencies Update

- [x] Update `pyproject.toml`:
  - Remove `crewai` dependency
  - Add `mcp` (MCP Python SDK)
  - Keep `pydantic` for state models
  - Keep `pytest` for testing
- [ ] Test clean install in fresh venv

---

## Phase 1: Core MCP Server

*Milestone: M1 — Hello MCP*

Minimal MCP server that Cursor can connect to.

### 1.1 Server Skeleton (`workflow/server.py`)

- [ ] Implement MCP server using `mcp` SDK
- [ ] Register as stdio transport (Cursor default)
- [ ] Add basic health check / list tools
- [ ] Test: Cursor can connect and see tools

### 1.2 State Management (`workflow/state.py`)

- [ ] Define `WorkflowState` pydantic model:
  - task_id, spec, phase, iteration
  - created_at, updated_at
  - history (list of transitions)
  - feedback (accumulated review feedback)
  - files_changed
- [ ] Implement `load_state(task_id)` → WorkflowState
- [ ] Implement `save_state(state)` → writes to `.workflow/<task_id>/state.json`
- [ ] Implement `get_active_task()` → current task_id or None
- [ ] Handle state file corruption gracefully

### 1.3 Phase Enum & Transitions

- [ ] Define `Phase` enum: `implementation`, `review`, `qa`, `complete`, `abandoned`
- [ ] Define valid transitions:
  - `implementation` → `review` (via request_review)
  - `review` → `implementation` (via request_changes)
  - `review` → `qa` (via approve)
  - `qa` → `implementation` (via report_issues)
  - `qa` → `complete` (via pass_qa)
  - any → `abandoned` (via abandon_task)
- [ ] Implement `transition(from_phase, to_phase)` with validation

---

## Phase 2: Workflow Tools

*Milestone: M2 — Workflow Works*

The MCP tools that drive the workflow.

### 2.1 `start_task` Tool

- [ ] Create new workflow state
- [ ] Generate task_id (timestamp-based if not provided)
- [ ] Set phase to `implementation`
- [ ] Load and return developer prompt with:
  - Task spec
  - Codebase summary (placeholder for now)
  - Workspace rules (placeholder for now)
- [ ] Log to history

### 2.2 `request_review` Tool

- [ ] Validate current phase is `implementation`
- [ ] Transition to `review` phase
- [ ] Store summary and files_changed
- [ ] Return architect prompt with:
  - Implementation summary
  - Files to review
  - Previous feedback (if iteration > 1)
- [ ] Log to history

### 2.3 `approve` Tool

- [ ] Validate current phase is `review`
- [ ] Transition to `qa` phase
- [ ] Return QA prompt
- [ ] Log to history

### 2.4 `request_changes` Tool

- [ ] Validate current phase is `review`
- [ ] Transition back to `implementation`
- [ ] Increment iteration counter
- [ ] Accumulate feedback
- [ ] Return developer prompt with feedback context
- [ ] Log to history
- [ ] Warn if iteration > MAX_ITERATIONS

### 2.5 `report_issues` Tool

- [ ] Validate current phase is `qa`
- [ ] Transition back to `implementation`
- [ ] Increment iteration counter
- [ ] Accumulate QA feedback
- [ ] Return developer prompt with QA feedback
- [ ] Log to history

### 2.6 `pass_qa` Tool

- [ ] Validate current phase is `qa`
- [ ] Transition to `complete`
- [ ] Generate completion summary:
  - Total iterations
  - Files changed
  - Timeline
- [ ] Log to history

### 2.7 `workflow_status` Tool

- [ ] Return current state:
  - Phase
  - Iteration count
  - Pending feedback summary
  - Files changed
- [ ] Handle "no active workflow" case

### 2.8 `abandon_task` Tool

- [ ] Set phase to `abandoned`
- [ ] Log reason
- [ ] Return confirmation

---

## Phase 3: Context & Prompts

*Milestone: M3 — Context-Aware*

Make agents codebase-aware.

### 3.1 Codebase Summary (`workflow/context.py`)

- [ ] Implement `get_file_tree(root)` → formatted tree string
- [ ] Implement `get_module_summaries(root)` → docstrings from Python files
- [ ] Implement `get_codebase_summary(root)` → combined context
- [ ] Respect `.gitignore` patterns
- [ ] Truncate to reasonable size (~2000 tokens)

### 3.2 Rules Loader

- [ ] Implement `load_workspace_rules(root)`:
  - Read `AGENTS.md`
  - Read `.cursor/rules/*.mdc` and `.cursor/rules/*.md`
  - Read `.github/copilot-instructions.md`
- [ ] Combine into single rules string
- [ ] Handle missing files gracefully

### 3.3 Role Prompts

- [ ] Create `workflow/prompts/developer.md`:
  - Role description
  - Capabilities
  - Workflow instructions
  - Placeholders for: {spec}, {feedback}, {codebase_summary}, {rules}
- [ ] Create `workflow/prompts/architect.md`:
  - Role description
  - Review checklist
  - Actions (approve/request_changes)
  - Placeholders for: {summary}, {files_changed}, {diff_hint}
- [ ] Create `workflow/prompts/qa.md`:
  - Role description
  - Validation steps
  - Actions (pass/report_issues)
  - Placeholders for: {summary}, {files_changed}

### 3.4 Prompt Rendering

- [ ] Implement `render_prompt(role, context)` → formatted prompt string
- [ ] Load template from prompts directory
- [ ] Fill in placeholders from context dict

---

## Phase 4: Cursor Integration

*Milestone: M4 — Production Ready (part 1)*

Make it work in Cursor.

### 4.1 MCP Configuration

- [ ] Create example `.cursor/mcp.json` for local config
- [ ] Document global config option
- [ ] Test: Cursor connects to server on startup

### 4.2 Tool Registration

- [ ] Ensure all tools appear in Cursor's tool list
- [ ] Verify tool descriptions are clear
- [ ] Test: Can invoke tools from chat

### 4.3 Error Handling

- [ ] Return clear error messages for invalid transitions
- [ ] Handle "no active workflow" gracefully
- [ ] Log errors for debugging

---

## Phase 5: Testing

*Milestone: M4 — Production Ready (part 2)*

Prove it works.

### 5.1 Unit Tests

- [ ] Test state load/save
- [ ] Test phase transitions (valid and invalid)
- [ ] Test codebase summary generation
- [ ] Test rules loading
- [ ] Test prompt rendering

### 5.2 Integration Test

- [ ] Script that simulates full workflow:
  - start_task → request_review → request_changes → request_review → approve → pass_qa
- [ ] Verify state file at each step
- [ ] Verify history is complete

### 5.3 Manual Cursor Test

- [ ] Connect MCP server in Cursor
- [ ] Run through complete workflow manually
- [ ] Verify prompts appear correctly
- [ ] Document any issues

---

## Phase 6: Polish

*Milestone: M4 — Production Ready (part 3)*

Nice-to-haves for MVP.

### 6.1 Workflow History

- [ ] Write human-readable `history.md` alongside `state.json`
- [ ] Include timestamps, summaries, feedback
- [ ] Useful for post-mortem review

### 6.2 Iteration Warnings

- [ ] Warn when iteration > 3
- [ ] Suggest breaking task into smaller pieces
- [ ] Don't block, just advise

### 6.3 Cleanup Command

- [ ] Add `cleanup_old_workflows` tool or script
- [ ] Remove `.workflow/<task_id>/` older than N days
- [ ] Keep completed workflows for reference

---

## Deprecated: Previous CrewAI Implementation

The following from the original design are **no longer applicable**:

- ~~SafeShellTool~~ — Cursor has its own shell tool
- ~~FileWriteTool / FileReadTool~~ — Cursor handles this natively
- ~~Tool Factory~~ — Not needed with MCP approach
- ~~Preflight checks~~ — Not needed (Cursor manages env)
- ~~CrewAI agents~~ — Replaced by role prompts
- ~~Orchestrator CLI~~ — Replaced by MCP tools
- ~~Git worktrees setup~~ — Not needed (single workspace)

**Code to evaluate for reuse:**
- `crewai/run_logger.py` — Logging concepts may apply to workflow history
- `crewai/tools/safe_shell.py` — Safety patterns could inform prompt guidelines

---

## Summary: Task Count by Phase

| Phase | Tasks | Completed |
|-------|-------|-----------|
| Phase 0: Project Restructure | 6 | 1 |
| Phase 1: Core MCP Server | 12 | 0 |
| Phase 2: Workflow Tools | 24 | 0 |
| Phase 3: Context & Prompts | 13 | 0 |
| Phase 4: Cursor Integration | 7 | 0 |
| Phase 5: Testing | 9 | 0 |
| Phase 6: Polish | 6 | 0 |
| **Total** | **77** | **1** |
