"""
RunLogger - Centralized logging and artifact management for pipeline runs.

Creates and manages the .runs/<run_id>/ directory with all required artifacts:
- config.json: Run configuration and results
- preflight.md: Preflight check results
- commands.log: Audit log for all tool commands
- failure_summary.md: Error details on failure
"""

from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class RunConfig(BaseModel):
    """Configuration and state for a pipeline run."""

    run_id: str
    spec: str
    model: str
    test_cmd: str
    timestamp_start: str
    timestamp_end: str | None = None

    # Branch configuration
    branches: dict[str, str] = Field(default_factory=lambda: {
        "developer": "feature/dev-task",
        "architect": "feature/arch-review",
        "qa": "feature/qa-test",
    })

    # Worktree paths (populated during preflight)
    worktree_paths: dict[str, str] = Field(default_factory=dict)

    # Git SHAs (populated during run)
    shas_start: dict[str, str] = Field(default_factory=dict)
    shas_end: dict[str, str] = Field(default_factory=dict)

    # Result
    result: Literal["pending", "success", "rejected", "qa_failed", "infra_failed"] = "pending"
    exit_code: int | None = None


class RunLogger:
    """
    Manages logging and artifacts for a single pipeline run.
    
    Usage:
        logger = RunLogger.create(run_id="auto", spec="...", model="gpt-4o")
        logger.log_command("developer", "/path/to/worktree", "ACCEPT", "git status", "clean")
        logger.write_preflight({"checks": [...], "passed": True})
        logger.finalize(exit_code=0, result="success")
    """

    def __init__(self, run_dir: Path, config: RunConfig):
        self.run_dir = run_dir
        self.config = config
        self._commands_file = run_dir / "commands.log"

    @classmethod
    def create(
        cls,
        run_id: str | None = None,
        spec: str = "",
        model: str = "gpt-4o",
        test_cmd: str = "python -m pytest",
        runs_dir: Path | None = None,
    ) -> RunLogger:
        """
        Create a new RunLogger for a pipeline run.
        
        Args:
            run_id: Run identifier. "auto" or None generates timestamp-based ID.
            spec: Feature specification text.
            model: LLM model name.
            test_cmd: Test command to run.
            runs_dir: Base directory for runs. Defaults to .runs/ in current dir.
        
        Returns:
            Initialized RunLogger with run directory created.
        """
        # Generate run ID if auto
        if run_id is None or run_id == "auto":
            run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # Determine runs directory
        if runs_dir is None:
            runs_dir = Path.cwd() / ".runs"

        run_dir = runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Create config
        config = RunConfig(
            run_id=run_id,
            spec=spec,
            model=model,
            test_cmd=test_cmd,
            timestamp_start=datetime.now(timezone.utc).isoformat(),
        )

        logger = cls(run_dir, config)
        logger._write_config()

        return logger

    def _write_config(self) -> None:
        """Write current config to config.json."""
        config_path = self.run_dir / "config.json"
        config_path.write_text(
            json.dumps(self.config.model_dump(), indent=2, default=str)
        )

    def log_command(
        self,
        agent_name: str,
        work_dir: str,
        status: Literal["ACCEPT", "REJECT"],
        command: str,
        result_summary: str,
    ) -> None:
        """
        Append a command entry to the audit log.
        
        Args:
            agent_name: Name of the agent (developer, architect, qa)
            work_dir: Working directory where command was executed
            status: ACCEPT if command was allowed, REJECT if blocked
            command: The command string
            result_summary: Brief summary of result or rejection reason
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Escape pipes in command and result for log format
        safe_command = command.replace("|", "\\|")
        safe_result = result_summary.replace("|", "\\|").replace("\n", " ")[:200]
        
        entry = f"{timestamp} | {agent_name} | {work_dir} | {status} | {safe_command} | {safe_result}\n"
        
        with self._commands_file.open("a") as f:
            f.write(entry)

    def write_preflight(self, results: dict[str, Any]) -> None:
        """
        Write preflight check results to preflight.md.
        
        Args:
            results: Dictionary with preflight check results.
                     Expected keys: checks (list), passed (bool), warnings (list)
        """
        preflight_path = self.run_dir / "preflight.md"
        
        lines = [
            "# Preflight Check Results",
            "",
            f"**Run ID:** {self.config.run_id}",
            f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}",
            "",
        ]

        # Checks
        checks = results.get("checks", [])
        if checks:
            lines.append("## Checks")
            lines.append("")
            for check in checks:
                status = "✅" if check.get("passed", False) else "❌"
                name = check.get("name", "Unknown")
                message = check.get("message", "")
                lines.append(f"- {status} **{name}**: {message}")
            lines.append("")

        # Warnings
        warnings = results.get("warnings", [])
        if warnings:
            lines.append("## Warnings")
            lines.append("")
            for warning in warnings:
                lines.append(f"- ⚠️ {warning}")
            lines.append("")

        # Final status
        passed = results.get("passed", False)
        status_text = "✅ PASS" if passed else "❌ FAIL"
        lines.append(f"## Result: {status_text}")
        lines.append("")

        preflight_path.write_text("\n".join(lines))

    def write_failure_summary(
        self,
        stage: Literal["PREFLIGHT", "DEV", "REVIEW", "QA", "EXCEPTION"],
        error_message: str,
        last_command: str | None = None,
        exception: Exception | None = None,
        next_steps: list[str] | None = None,
    ) -> None:
        """
        Write failure details to failure_summary.md.
        
        Args:
            stage: Which stage failed
            error_message: Human-readable error description
            last_command: Last command executed (from commands log)
            exception: Exception object if applicable
            next_steps: Suggested remediation steps
        """
        failure_path = self.run_dir / "failure_summary.md"
        
        lines = [
            "# Failure Summary",
            "",
            f"**Run ID:** {self.config.run_id}",
            f"**Failed Stage:** {stage}",
            f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Error",
            "",
            error_message,
            "",
        ]

        if last_command:
            lines.extend([
                "## Last Command",
                "",
                f"```",
                last_command,
                f"```",
                "",
            ])

        if exception:
            lines.extend([
                "## Exception",
                "",
                f"```",
                f"{type(exception).__name__}: {exception}",
                "",
                traceback.format_exc(),
                f"```",
                "",
            ])

        if next_steps:
            lines.extend([
                "## Suggested Next Steps",
                "",
            ])
            for step in next_steps:
                lines.append(f"1. {step}")
            lines.append("")

        failure_path.write_text("\n".join(lines))

    def write_artifact(self, filename: str, content: str) -> Path:
        """
        Write an arbitrary artifact to the run directory.
        
        Args:
            filename: Name of the file to write
            content: Content to write
            
        Returns:
            Path to the written file
        """
        artifact_path = self.run_dir / filename
        artifact_path.write_text(content)
        return artifact_path

    def set_worktree_paths(self, paths: dict[str, str]) -> None:
        """Set worktree paths in config."""
        self.config.worktree_paths = paths
        self._write_config()

    def set_shas(self, shas: dict[str, str], phase: Literal["start", "end"]) -> None:
        """Set git SHAs for branches at start or end of run."""
        if phase == "start":
            self.config.shas_start = shas
        else:
            self.config.shas_end = shas
        self._write_config()

    def finalize(
        self,
        exit_code: int,
        result: Literal["success", "rejected", "qa_failed", "infra_failed"],
    ) -> None:
        """
        Finalize the run with exit code and result.
        
        Args:
            exit_code: Process exit code (0, 2, 3, or 4)
            result: Result status string
        """
        self.config.exit_code = exit_code
        self.config.result = result
        self.config.timestamp_end = datetime.now(timezone.utc).isoformat()
        self._write_config()

    def get_last_command(self) -> str | None:
        """Get the last command from the commands log."""
        if not self._commands_file.exists():
            return None
        
        lines = self._commands_file.read_text().strip().split("\n")
        if lines:
            return lines[-1]
        return None

