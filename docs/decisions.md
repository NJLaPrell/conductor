# Conductor: Decisions (ADR-lite)

Use this file to capture quick architectural decisions.

---

## 2024-12-16 — Project Renamed to Conductor

- **Context:** The project was originally named "crewDev" based on the CrewAI multi-agent approach. After pivoting to MCP, the name no longer made sense.
- **Decision:** Rename to "Conductor" — evokes orchestration, guiding the development process, appropriate for a workflow server.
- **Consequences:** All documentation updated. Folder and GitHub repo renamed.

---

## 2024-12-16 — Pivot from CrewAI to MCP Workflow Server

- **Context:** We had designed a CrewAI-based autonomous multi-agent pipeline with separate git worktrees for Developer, Architect, and QA agents. During implementation planning, we identified significant disconnects between this approach and what a Cursor developer would expect.

- **Problems with CrewAI approach:**
  1. **No IDE integration** — CLI-only, separate from Cursor
  2. **Worktree complexity** — 3 sibling directories, context switching hell
  3. **No human-in-the-loop** — fully autonomous with no intervention points
  4. **No real-time visibility** — artifacts only at end, no streaming
  5. **No codebase awareness** — agents start blind, must explore manually
  6. **MCP servers unused** — building parallel infrastructure
  7. **Overkill for most tasks** — heavy machinery for simple changes

- **Decision:** Pivot to an MCP workflow server that runs inside Cursor:
  - Single workspace (no worktrees)
  - MCP tools guide workflow phases (start → review → QA → complete)
  - Cursor's agent does the actual work using native tools
  - Human remains in the loop
  - Full access to Cursor's semantic search, diffs, etc.

- **Tradeoffs accepted:**
  - **Self-review bias** — same model reviews its own work
  - **No CI/headless mode** — Cursor-dependent
  - **Advisory only** — can't hard-enforce role restrictions
  - **No true multi-agent** — role-switching, not separate agents

- **Consequences:** 
  - Simpler implementation (~200 lines vs. complex orchestrator)
  - Better developer experience
  - Most of the CrewAI code becomes obsolete
  - Some concepts (safety patterns, logging) may be reusable

---

## 2024-12-13 — Project Directory Structure

- **Context:** Original design showed orchestrator files at repo root. Needed to clarify where AI orchestration code lives vs project code.
- **Decision:** Place all AI orchestration code under `crewai/` directory. Project source code (what agents work on) goes in `src/`. Tests go in `tests/`. Helper scripts go in `scripts/`.
- **Consequences:** Clear separation between pipeline infrastructure and the actual project being developed. Follows Python package conventions.
- **Update (2024-12-16):** With the MCP pivot, orchestration code moves to `workflow/` directory instead of `crewai/`.

---

## 2024-12-13 — This Repo is the Implementation Target

- **Context:** README described this as a "design workspace" — unclear if implementation would live here or in a separate repo.
- **Decision:** This repo IS the implementation target. The actual project code that agents work on will live in `src/`. The pipeline infrastructure lives in `crewai/` (now `workflow/`).
- **Consequences:** No need for a separate repo. This workspace evolves from design into working implementation.

---

## 2024-12-13 — LLM Model Selection

- **Context:** Original design referenced fictional models (`gpt-5.1`, `gpt-5.1-codex`). Needed real model names.
- **Decision:** Use `gpt-4o` as default model. OpenAI's Codex was deprecated; no direct replacement. `gpt-4o` is capable for code generation. Optional models: `gpt-4-turbo`, `o1-preview` (for complex reasoning), `gpt-4o-mini` (budget).
- **Consequences:** All documentation updated to reference real models. Model selection remains configurable via env/CLI.
- **Update (2024-12-16):** With MCP approach, model selection is handled by Cursor, not our code.

---

## 2024-12-13 — Collaborative Multi-Agent Workflow

- **Context:** Original design had sequential two-phase execution (Dev → Architect gate → QA). This didn't leverage CrewAI's multi-agent collaboration capabilities.
- **Decision:** Implement true collaborative workflow where agents iterate:
  - Developer implements → requests review
  - Architect reviews → provides feedback
  - Developer refines (loop until approved)
  - QA validates → reports issues
  - Developer fixes (loop until passing)
- **Consequences:** More natural development workflow. Better use of CrewAI. Higher quality output through iteration.
- **Update (2024-12-16):** This workflow is preserved in the MCP approach, but implemented via MCP tools and role-switching prompts instead of separate agents.

---

## 2024-12-13 — Only Developer Writes Code and Merges

- **Context:** Original design had Architect performing git merges. This was fragile (LLM doing merges) and violated separation of concerns.
- **Decision:** Only Developer agent can write code, commit, push, and merge. Architect and QA are read-only reviewers who provide direction.
- **Consequences:** Cleaner separation of roles. Less risk of git state corruption. Architect/QA focus on their core competencies.
- **Update (2024-12-16):** With MCP approach, this is advisory (prompts tell agent not to write code in review/QA phases) rather than enforced.

---

## Deprecated Decisions

The following decisions are no longer relevant after the MCP pivot:

- ~~Agent File Access via FileWriteTool~~ — Cursor handles file access natively
- ~~CrewAI Native LLM Configuration~~ — Not using CrewAI
- ~~Unrestricted Network Access for Agents~~ — Cursor handles this
- ~~CrewAI Tool Interface~~ — Using MCP tools instead
- ~~Tool Factory Pattern for Worktree Isolation~~ — No worktrees
- ~~Role-Based Tool Permissions~~ — Advisory via prompts
- ~~FileReadTool Addition~~ — Cursor handles this
- ~~Agent Output Mechanism~~ — Cursor handles output
- ~~CrewAI Version Pin~~ — Not using CrewAI
- ~~Secure Path Validation~~ — Cursor handles this

These decisions are preserved in git history for reference.
