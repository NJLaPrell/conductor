"""Tests for RunLogger."""

import json
from pathlib import Path

import pytest

from crewai.run_logger import RunLogger, RunConfig


class TestRunLogger:
    """Test suite for RunLogger functionality."""

    def test_create_run_directory(self, tmp_path: Path) -> None:
        """RunLogger.create() should create the run directory."""
        logger = RunLogger.create(
            run_id="test_run_123",
            spec="Test feature spec",
            model="gpt-4o",
            runs_dir=tmp_path,
        )

        assert logger.run_dir.exists()
        assert logger.run_dir.name == "test_run_123"

    def test_auto_run_id_generates_timestamp(self, tmp_path: Path) -> None:
        """run_id='auto' should generate a timestamp-based ID."""
        logger = RunLogger.create(
            run_id="auto",
            spec="Test spec",
            runs_dir=tmp_path,
        )

        # Should be format YYYYMMDD_HHMMSS
        assert len(logger.config.run_id) == 15
        assert "_" in logger.config.run_id

    def test_config_json_created(self, tmp_path: Path) -> None:
        """config.json should be created with correct content."""
        logger = RunLogger.create(
            run_id="config_test",
            spec="My feature spec",
            model="gpt-4-turbo",
            test_cmd="pytest -v",
            runs_dir=tmp_path,
        )

        config_path = logger.run_dir / "config.json"
        assert config_path.exists()

        config_data = json.loads(config_path.read_text())
        assert config_data["run_id"] == "config_test"
        assert config_data["spec"] == "My feature spec"
        assert config_data["model"] == "gpt-4-turbo"
        assert config_data["test_cmd"] == "pytest -v"
        assert config_data["result"] == "pending"

    def test_log_command_appends_to_log(self, tmp_path: Path) -> None:
        """log_command() should append entries to commands.log."""
        logger = RunLogger.create(run_id="cmd_test", runs_dir=tmp_path)

        logger.log_command(
            agent_name="developer",
            work_dir="/path/to/worktree",
            status="ACCEPT",
            command="git status",
            result_summary="clean",
        )

        logger.log_command(
            agent_name="architect",
            work_dir="/path/to/arch",
            status="REJECT",
            command="rm -rf /",
            result_summary="Blocked: destructive command",
        )

        log_path = logger.run_dir / "commands.log"
        assert log_path.exists()

        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 2
        assert "developer" in lines[0]
        assert "git status" in lines[0]
        assert "ACCEPT" in lines[0]
        assert "architect" in lines[1]
        assert "REJECT" in lines[1]

    def test_log_command_escapes_pipes(self, tmp_path: Path) -> None:
        """log_command() should escape pipe characters."""
        logger = RunLogger.create(run_id="pipe_test", runs_dir=tmp_path)

        logger.log_command(
            agent_name="developer",
            work_dir="/path",
            status="REJECT",
            command="ls | grep foo",
            result_summary="Blocked: pipe character",
        )

        log_content = (logger.run_dir / "commands.log").read_text()
        assert "\\|" in log_content

    def test_write_preflight_success(self, tmp_path: Path) -> None:
        """write_preflight() should create preflight.md with results."""
        logger = RunLogger.create(run_id="preflight_test", runs_dir=tmp_path)

        logger.write_preflight({
            "checks": [
                {"name": "OPENAI_API_KEY", "passed": True, "message": "Set"},
                {"name": "Worktrees", "passed": True, "message": "All exist"},
            ],
            "warnings": ["Origin remote not configured"],
            "passed": True,
        })

        preflight_path = logger.run_dir / "preflight.md"
        assert preflight_path.exists()

        content = preflight_path.read_text()
        assert "# Preflight Check Results" in content
        assert "✅" in content
        assert "OPENAI_API_KEY" in content
        assert "⚠️" in content
        assert "Origin remote" in content
        assert "PASS" in content

    def test_write_preflight_failure(self, tmp_path: Path) -> None:
        """write_preflight() should show FAIL for failed checks."""
        logger = RunLogger.create(run_id="preflight_fail", runs_dir=tmp_path)

        logger.write_preflight({
            "checks": [
                {"name": "Worktrees", "passed": False, "message": "Missing developer-agent-work"},
            ],
            "passed": False,
        })

        content = (logger.run_dir / "preflight.md").read_text()
        assert "❌" in content
        assert "FAIL" in content

    def test_write_failure_summary(self, tmp_path: Path) -> None:
        """write_failure_summary() should create failure_summary.md."""
        logger = RunLogger.create(run_id="failure_test", runs_dir=tmp_path)

        logger.write_failure_summary(
            stage="REVIEW",
            error_message="Architect rejected the code after 3 iterations",
            last_command="git diff feature/dev-task",
            next_steps=[
                "Review the feedback in review_output.json",
                "Address the architectural concerns",
                "Re-run the pipeline",
            ],
        )

        failure_path = logger.run_dir / "failure_summary.md"
        assert failure_path.exists()

        content = failure_path.read_text()
        assert "# Failure Summary" in content
        assert "REVIEW" in content
        assert "rejected" in content
        assert "git diff" in content
        assert "Review the feedback" in content

    def test_write_failure_summary_with_exception(self, tmp_path: Path) -> None:
        """write_failure_summary() should include exception traceback."""
        logger = RunLogger.create(run_id="exception_test", runs_dir=tmp_path)

        try:
            raise ValueError("Something went wrong")
        except ValueError as e:
            logger.write_failure_summary(
                stage="EXCEPTION",
                error_message="Unexpected error during execution",
                exception=e,
            )

        content = (logger.run_dir / "failure_summary.md").read_text()
        assert "ValueError" in content
        assert "Something went wrong" in content

    def test_write_artifact(self, tmp_path: Path) -> None:
        """write_artifact() should create arbitrary files."""
        logger = RunLogger.create(run_id="artifact_test", runs_dir=tmp_path)

        path = logger.write_artifact("dev_output.md", "# Developer Output\n\nDone!")

        assert path.exists()
        assert path.name == "dev_output.md"
        assert "Developer Output" in path.read_text()

    def test_finalize_updates_config(self, tmp_path: Path) -> None:
        """finalize() should update config with exit code and result."""
        logger = RunLogger.create(run_id="finalize_test", runs_dir=tmp_path)

        logger.finalize(exit_code=0, result="success")

        config_data = json.loads((logger.run_dir / "config.json").read_text())
        assert config_data["exit_code"] == 0
        assert config_data["result"] == "success"
        assert config_data["timestamp_end"] is not None

    def test_set_shas(self, tmp_path: Path) -> None:
        """set_shas() should store git SHAs in config."""
        logger = RunLogger.create(run_id="sha_test", runs_dir=tmp_path)

        logger.set_shas({"developer": "abc123", "architect": "def456"}, phase="start")
        logger.set_shas({"developer": "ghi789", "architect": "jkl012"}, phase="end")

        config_data = json.loads((logger.run_dir / "config.json").read_text())
        assert config_data["shas_start"]["developer"] == "abc123"
        assert config_data["shas_end"]["developer"] == "ghi789"

    def test_get_last_command(self, tmp_path: Path) -> None:
        """get_last_command() should return the last logged command."""
        logger = RunLogger.create(run_id="last_cmd_test", runs_dir=tmp_path)

        assert logger.get_last_command() is None  # No commands yet

        logger.log_command("dev", "/path", "ACCEPT", "git status", "ok")
        logger.log_command("dev", "/path", "ACCEPT", "git add .", "ok")

        last = logger.get_last_command()
        assert last is not None
        assert "git add" in last

