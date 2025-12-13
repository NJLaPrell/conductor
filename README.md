# crewDev

A CLI-driven autonomous software development pipeline using **CrewAI** and **git worktrees**.

Three AI agents (Developer → Architect → QA) work in isolated worktrees with restricted tool access, producing auditable artifacts for every run.

## Quick Start

### 1. Create and activate a venv

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -U pip
pip install -e ".[dev]"
```

### 3. Set up git worktrees

```bash
chmod +x scripts/setup_worktrees.sh
./scripts/setup_worktrees.sh
```

### 4. Set environment variables

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-4o"  # optional, defaults to gpt-4o
```

### 5. Run the pipeline

```bash
python -m crewai.orchestrator --spec "Add feature X ..."
```

## Project Structure

```
crewDev/                        # Main repo (this workspace)
├── crewai/                     # AI orchestration code
│   ├── orchestrator.py         # CLI entry point
│   ├── crew_config.py          # Agent/task definitions
│   ├── preflight.py            # Pre-run validation
│   ├── tools/                  # CrewAI tools
│   │   ├── safe_shell.py       # Restricted shell access
│   │   ├── file_write.py       # File writing
│   │   └── file_read.py        # File reading
│   ├── models.py               # Pydantic models
│   └── run_logger.py           # Logging/artifacts
├── src/                        # Project source code (agents work here)
├── tests/                      # Project tests (QA runs these)
├── scripts/                    # Helper scripts
├── docs/                       # Design documentation
│   ├── DESIGN.md               # Technical design spec
│   ├── TASKS.md                # Implementation tasks
│   └── decisions.md            # Architecture decisions
└── .runs/                      # Run artifacts (created per-run)
```

### Sibling Worktrees (created by setup script)

```
../developer-agent-work/        # Developer agent → feature/dev-task
../architect-agent-work/        # Architect agent → feature/arch-review
../qa-agent-work/               # QA agent → feature/qa-test
```

## Documentation

- **[DESIGN.md](docs/DESIGN.md)** — Full technical design and architecture
- **[TASKS.md](docs/TASKS.md)** — Implementation task breakdown
- **[decisions.md](docs/decisions.md)** — Architecture decision records
- **[AGENTS.md](AGENTS.md)** — Workspace operating rules for AI assistants

## CLI Options

```bash
python -m crewai.orchestrator \
  --spec "Add feature X ..."    # Feature specification (required)
  --run-id auto                 # Run ID (default: timestamp)
  --model gpt-4o                # LLM model (default: gpt-4o)
  --test-cmd "python -m pytest" # Test command (default)
  --local-only                  # Skip remote push
  --verbose                     # Extra logging
  --force                       # Override advisory lock
  --fast-forward                # Fast-forward branches from main
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | SUCCESS — approved and tests passed |
| `2` | REJECTED — architect did not approve |
| `3` | INFRA FAIL — preflight or tool failure |
| `4` | TESTS FAIL — approved but QA tests failed |

## Development

Run tests:

```bash
python -m pytest
```

See `docs/TASKS.md` for the implementation roadmap.
