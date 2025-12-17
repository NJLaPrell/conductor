# Conductor

An **MCP workflow server** that guides developers through a structured development process (Developer → Architect Review → QA Validation) while maintaining full **Cursor IDE integration**.

## What Is This?

Instead of building a separate autonomous agent pipeline, Conductor provides an MCP server that works *inside* Cursor. You get:

- **Structured workflow** — enforced phases with clear handoffs
- **Role-based prompts** — Developer, Architect, and QA perspectives
- **Full Cursor integration** — diffs, semantic search, all native tools
- **Human-in-the-loop** — you drive, the workflow guides

## Quick Example

```
You: @workflow start_task "Add a date utility that returns ISO format"

Agent: [Developer mode]
I'll implement this feature. Let me first check the existing codebase...
[implements code, writes tests]
@workflow request_review --summary "Added src/date_utils.py" --files "src/date_utils.py,tests/test_date_utils.py"

Agent: [Architect mode] 
Reviewing the changes...
The implementation looks good, but needs timezone support.
@workflow request_changes --feedback "Add timezone parameter" --issues "Missing TZ support"

Agent: [Developer mode]
Addressing feedback...
[updates implementation]
@workflow request_review --summary "Added timezone support"

Agent: [Architect mode]
LGTM!
@workflow approve

Agent: [QA mode]
Running tests... All pass.
Checking for edge cases... Looks solid.
@workflow pass_qa --summary "All tests pass, no issues found"

Agent: ✅ Workflow complete! Task finished in 3 iterations.
```

## Installation

### 1. Clone and set up environment

```bash
git clone <repo-url> conductor
cd conductor
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -U pip
pip install -e ".[dev]"
```

### 3. Configure Cursor MCP

Add to your Cursor MCP config (`.cursor/mcp.json` or global settings):

```json
{
  "mcpServers": {
    "conductor": {
      "command": "python",
      "args": ["-m", "workflow.server"],
      "cwd": "/path/to/conductor"
    }
  }
}
```

### 4. Restart Cursor

The workflow tools should now appear in your tool list.

## Workflow Tools

| Tool | Description |
|------|-------------|
| `start_task` | Begin a new development task |
| `request_review` | Developer requests architecture review |
| `approve` | Architect approves changes |
| `request_changes` | Architect requests changes |
| `report_issues` | QA reports validation issues |
| `pass_qa` | QA validation passed |
| `workflow_status` | Check current workflow state |
| `abandon_task` | Cancel current workflow |

## Project Structure

```
conductor/
├── workflow/                   # MCP workflow server
│   ├── server.py               # MCP server entry point
│   ├── tools.py                # Workflow tool definitions
│   ├── state.py                # State management
│   ├── context.py              # Codebase context generation
│   └── prompts/                # Role-specific prompts
│       ├── developer.md
│       ├── architect.md
│       └── qa.md
├── src/                        # Your project source code
├── tests/                      # Your project tests
├── docs/                       # Documentation
│   ├── DESIGN.md               # Technical design
│   ├── TASKS.md                # Implementation tasks
│   └── decisions.md            # Architecture decisions
├── .workflow/                  # Workflow state (auto-created)
├── pyproject.toml
└── README.md
```

## Documentation

- **[DESIGN.md](docs/DESIGN.md)** — Full technical design and architecture
- **[TASKS.md](docs/TASKS.md)** — Implementation task breakdown
- **[decisions.md](docs/decisions.md)** — Architecture decision records
- **[AGENTS.md](AGENTS.md)** — Workspace rules for AI assistants

## How It Works

1. **You start a task** — MCP server creates workflow state, returns Developer prompt
2. **Agent works as Developer** — implements code using Cursor's native tools
3. **Agent requests review** — MCP switches to Architect prompt
4. **Agent reviews as Architect** — provides feedback or approves
5. **Loop until approved** — Developer addresses feedback, re-requests review
6. **QA validation** — Agent runs tests, checks for issues
7. **Complete** — workflow finishes, state saved for reference

The MCP server tracks state, enforces transitions, and provides role-appropriate prompts. Cursor's agent does the actual work.

## Why MCP Instead of Autonomous Agents?

We originally designed a CrewAI-based autonomous pipeline. We pivoted to MCP because:

| Autonomous Pipeline | MCP Workflow |
|--------------------|--------------|
| CLI-only, no IDE | Full Cursor integration |
| Separate git worktrees | Single workspace |
| Fully autonomous | Human-in-the-loop |
| Complex infrastructure | ~200 lines of Python |

See [decisions.md](docs/decisions.md) for the full rationale.

## Limitations

- **Cursor-only** — requires Cursor IDE with MCP support
- **Self-review** — same model reviews its own work (mitigated by structured prompts)
- **Advisory** — workflow is guided, not strictly enforced
- **No CI mode** — can't run headless

## Development

Run tests:

```bash
python -m pytest
```

Run MCP server manually (for debugging):

```bash
python -m workflow.server
```

## Status

🚧 **In Development** — See [TASKS.md](docs/TASKS.md) for current progress.
