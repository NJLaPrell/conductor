# Decisions (ADR-lite)

Use this file to capture quick architectural decisions.

---

## 2024-12-13 — Project Directory Structure

- **Context:** Original design showed orchestrator files at repo root. Needed to clarify where AI orchestration code lives vs project code.
- **Decision:** Place all AI orchestration code under `crewai/` directory. Project source code (what agents work on) goes in `src/`. Tests go in `tests/`. Helper scripts go in `scripts/`.
- **Consequences:** Clear separation between pipeline infrastructure and the actual project being developed. Follows Python package conventions.

---

## 2024-12-13 — This Repo is the Implementation Target

- **Context:** README described this as a "design workspace" — unclear if implementation would live here or in a separate repo.
- **Decision:** This repo IS the implementation target. The actual project code that agents work on will live in `src/`. The pipeline infrastructure lives in `crewai/`.
- **Consequences:** No need for a separate repo. This workspace evolves from design into working implementation.

---

## 2024-12-13 — LLM Model Selection

- **Context:** Original design referenced fictional models (`gpt-5.1`, `gpt-5.1-codex`). Needed real model names.
- **Decision:** Use `gpt-4o` as default model. OpenAI's Codex was deprecated; no direct replacement. `gpt-4o` is capable for code generation. Optional models: `gpt-4-turbo`, `o1-preview` (for complex reasoning), `gpt-4o-mini` (budget).
- **Consequences:** All documentation updated to reference real models. Model selection remains configurable via env/CLI.

---

## 2024-12-13 — Agent File Access via FileWriteTool

- **Context:** Original design only specified SafeShellTool for shell access, but agents need to write code files. Shell tool blocks redirects and `echo`, so file writing was impossible.
- **Decision:** Add a `FileWriteTool` that allows agents to write to any file within their assigned git worktree. Path validation ensures agents cannot write outside their worktree boundary.
- **Consequences:** Agents can now create and modify files. Security is maintained via worktree boundary enforcement.

---

## 2024-12-13 — CrewAI Native LLM Configuration

- **Context:** Original design specified a custom `LLMProvider` adapter class. CrewAI has evolved and now handles LLM configuration natively.
- **Decision:** Remove custom `LLMProvider`. Use CrewAI's built-in LLM configuration. Tools use CrewAI's `@tool` decorator.
- **Consequences:** Less custom code to maintain. Better compatibility with CrewAI updates. Simpler architecture.

---

## 2024-12-13 — Unrestricted Network Access for Agents

- **Context:** Original design mentioned "network calls in tests require explicit allowlist" but no mechanism was defined.
- **Decision:** Do not restrict network access for agents. Agents can make network calls as needed (e.g., `pip install`, API calls).
- **Consequences:** More flexibility for agents. Security relies on other constraints (worktree isolation, shell command restrictions). Users should be aware agents have network access.

---

## 2024-12-13 — CrewAI Tool Interface

- **Context:** Original design showed a class-based `SafeShellTool` with `__init__` and `run` methods. Needed to align with current CrewAI patterns.
- **Decision:** Use CrewAI's `@tool` decorator for tool definitions. Tools are functions, not classes. Context (worktree path, logger) passed via closure or global config.
- **Consequences:** Tools follow CrewAI conventions. Easier integration with CrewAI's agent system.

---

## 2024-12-13 — Tool Factory Pattern for Worktree Isolation

- **Context:** Each agent needs tools bound to its specific worktree. The `@tool` decorator creates functions, but each agent needs different path constraints.
- **Decision:** Implement a factory function `create_tools(worktree_path, run_logger, agent_name)` that returns tool instances with the worktree path captured via closure. Path validation uses resolved absolute paths.
- **Consequences:** Clean per-agent tool isolation. Agents cannot lie about their worktree because validation is hardcoded at tool creation time.

---

## 2024-12-13 — FileReadTool Addition

- **Context:** Agents need to read files. Using `cat` via SafeShellTool works but is awkward.
- **Decision:** Add a dedicated `FileReadTool` with the same worktree boundary restrictions as FileWriteTool.
- **Consequences:** Cleaner API for file operations. Consistent security model for reads and writes.

---

## 2024-12-13 — Agent Output Mechanism

- **Context:** Unclear how agents produce output artifacts (dev_output.md, review_output.json, etc.).
- **Decision:** Two types of output: (1) File artifacts — agents write directly using FileWriteTool (code, tests, diff.patch). (2) Summary artifacts — orchestrator captures agent's final response and writes to run directory.
- **Consequences:** Clear separation of concerns. Orchestrator manages run artifacts uniformly.

---

## 2024-12-13 — CrewAI Version Pin

- **Context:** Original design specified `crewai>=0.8.0` which is very old.
- **Decision:** Pin to `crewai>=0.80.0` targeting late 2024 releases with stable `@tool` decorator support.
- **Consequences:** Reproducible builds. Access to current CrewAI features.

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

---

## 2024-12-13 — Only Developer Writes Code and Merges

- **Context:** Original design had Architect performing git merges. This was fragile (LLM doing merges) and violated separation of concerns.
- **Decision:** Only Developer agent can write code, commit, push, and merge. Architect and QA are read-only reviewers who provide direction.
- **Consequences:** Cleaner separation of roles. Less risk of git state corruption. Architect/QA focus on their core competencies.

---

## 2024-12-13 — Role-Based Tool Permissions

- **Context:** All agents had the same tools. But Architect/QA shouldn't be able to write files or modify git state.
- **Decision:** Tool factory takes a `role` parameter. Permissions:
  - Developer: read_file, write_file, safe_shell (full git)
  - Architect: read_file, safe_shell (read-only git: status, diff, log, fetch, checkout)
  - QA: read_file, safe_shell (read-only git)
- **Consequences:** Enforced separation of concerns at the tool level. Agents can't accidentally (or intentionally) exceed their role.

---

## 2024-12-13 — QA Examines Code, Not Just Tests

- **Context:** Original QA role was just "run tests and report". This underutilizes the LLM's capabilities.
- **Decision:** QA agent should also examine code for logical issues, edge cases, potential breakage — beyond just test results.
- **Consequences:** Higher quality validation. Catches issues that tests might miss. Justifies using an LLM for QA.

---

## 2024-12-13 — Secure Path Validation

- **Context:** Original path validation used `str.startswith()` which is vulnerable to path traversal attacks (e.g., `/foo/bar` starts with `/foo/ba`).
- **Decision:** Use `Path.is_relative_to()` (Python 3.9+) for secure path validation.
- **Consequences:** Secure against path traversal attacks. Cleaner code.
