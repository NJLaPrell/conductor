"""Tests for SafeShellTool."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from crewai.tools.safe_shell import SafeShellTool, SafeShellConfig, CommandResult


class TestSafeShellValidation:
    """Test command validation logic."""

    @pytest.fixture
    def tool(self, tmp_path: Path) -> SafeShellTool:
        """Create a SafeShellTool for testing."""
        return SafeShellTool(worktree_path=tmp_path)

    # Allowlist tests
    def test_allows_git_commands(self, tool: SafeShellTool) -> None:
        """Git commands should be allowed."""
        is_valid, reason = tool.validate_command("git status")
        assert is_valid is True

    def test_allows_python_commands(self, tool: SafeShellTool) -> None:
        """Python commands should be allowed."""
        is_valid, _ = tool.validate_command("python -m pytest")
        assert is_valid is True

    def test_allows_basic_commands(self, tool: SafeShellTool) -> None:
        """Basic read commands should be allowed."""
        for cmd in ["ls -la", "cat file.txt", "pwd", "echo hello"]:
            is_valid, _ = tool.validate_command(cmd)
            assert is_valid is True, f"Expected {cmd} to be allowed"

    def test_rejects_unknown_commands(self, tool: SafeShellTool) -> None:
        """Commands not in allowlist should be rejected."""
        is_valid, reason = tool.validate_command("curl http://example.com")
        assert is_valid is False
        assert "allowlist" in reason.lower()

    # Denylist tests
    def test_rejects_rm(self, tool: SafeShellTool) -> None:
        """rm should be denied."""
        is_valid, reason = tool.validate_command("rm -rf /")
        assert is_valid is False
        assert "rm" in reason

    def test_rejects_sudo(self, tool: SafeShellTool) -> None:
        """sudo should be denied."""
        is_valid, reason = tool.validate_command("sudo apt update")
        assert is_valid is False
        assert "sudo" in reason

    def test_rejects_chmod(self, tool: SafeShellTool) -> None:
        """chmod should be denied."""
        is_valid, reason = tool.validate_command("chmod 777 file.txt")
        assert is_valid is False
        assert "chmod" in reason

    def test_rejects_mv(self, tool: SafeShellTool) -> None:
        """mv should be denied."""
        is_valid, reason = tool.validate_command("mv file1 file2")
        assert is_valid is False
        assert "mv" in reason

    # Metacharacter tests
    def test_rejects_pipe(self, tool: SafeShellTool) -> None:
        """Pipe character should be blocked."""
        is_valid, reason = tool.validate_command("ls | grep foo")
        assert is_valid is False
        assert "metacharacter" in reason.lower()

    def test_rejects_semicolon(self, tool: SafeShellTool) -> None:
        """Semicolon should be blocked."""
        is_valid, reason = tool.validate_command("ls; rm -rf /")
        assert is_valid is False
        assert "metacharacter" in reason.lower()

    def test_rejects_and_chain(self, tool: SafeShellTool) -> None:
        """&& should be blocked."""
        is_valid, reason = tool.validate_command("ls && rm -rf /")
        assert is_valid is False
        assert "metacharacter" in reason.lower()

    def test_rejects_or_chain(self, tool: SafeShellTool) -> None:
        """|| should be blocked."""
        is_valid, reason = tool.validate_command("ls || echo fail")
        assert is_valid is False
        assert "metacharacter" in reason.lower()

    def test_rejects_redirect(self, tool: SafeShellTool) -> None:
        """Redirect should be blocked."""
        is_valid, reason = tool.validate_command("echo hello > file.txt")
        assert is_valid is False
        assert "metacharacter" in reason.lower()

    def test_rejects_command_substitution(self, tool: SafeShellTool) -> None:
        """$() command substitution should be blocked."""
        is_valid, reason = tool.validate_command("echo $(whoami)")
        assert is_valid is False
        assert "metacharacter" in reason.lower()

    def test_rejects_backtick_substitution(self, tool: SafeShellTool) -> None:
        """Backtick command substitution should be blocked."""
        is_valid, reason = tool.validate_command("echo `whoami`")
        assert is_valid is False
        assert "metacharacter" in reason.lower()

    # Git-specific tests
    def test_allows_git_push(self, tool: SafeShellTool) -> None:
        """git push without --force should be allowed."""
        is_valid, _ = tool.validate_command("git push origin main")
        assert is_valid is True

    def test_rejects_git_push_force(self, tool: SafeShellTool) -> None:
        """git push --force should be denied."""
        is_valid, reason = tool.validate_command("git push --force origin main")
        assert is_valid is False
        assert "force" in reason.lower()

    def test_rejects_git_push_f(self, tool: SafeShellTool) -> None:
        """git push -f should be denied."""
        is_valid, reason = tool.validate_command("git push -f origin main")
        assert is_valid is False
        assert "force" in reason.lower()

    def test_rejects_git_reset_hard(self, tool: SafeShellTool) -> None:
        """git reset --hard should be denied."""
        is_valid, reason = tool.validate_command("git reset --hard HEAD~1")
        assert is_valid is False
        assert "hard" in reason.lower()

    def test_allows_git_reset_soft(self, tool: SafeShellTool) -> None:
        """git reset without --hard should be allowed."""
        is_valid, _ = tool.validate_command("git reset --soft HEAD~1")
        assert is_valid is True

    def test_rejects_git_clean(self, tool: SafeShellTool) -> None:
        """git clean should be denied."""
        is_valid, reason = tool.validate_command("git clean -fd")
        assert is_valid is False
        assert "clean" in reason.lower()

    def test_rejects_git_rebase(self, tool: SafeShellTool) -> None:
        """git rebase should be denied."""
        is_valid, reason = tool.validate_command("git rebase main")
        assert is_valid is False
        assert "rebase" in reason.lower()

    # Edge cases
    def test_rejects_empty_command(self, tool: SafeShellTool) -> None:
        """Empty command should be rejected."""
        is_valid, _ = tool.validate_command("")
        assert is_valid is False

    def test_rejects_whitespace_only(self, tool: SafeShellTool) -> None:
        """Whitespace-only command should be rejected."""
        is_valid, _ = tool.validate_command("   ")
        assert is_valid is False

    def test_handles_quoted_strings(self, tool: SafeShellTool) -> None:
        """Commands with quoted strings should work."""
        is_valid, _ = tool.validate_command('echo "hello world"')
        assert is_valid is True

    def test_denylist_word_boundary(self, tool: SafeShellTool) -> None:
        """Denylist should match whole words, not substrings."""
        # "firmware" contains "rm" but should not be blocked
        is_valid, _ = tool.validate_command("echo firmware")
        assert is_valid is True


class TestSafeShellExecution:
    """Test command execution."""

    @pytest.fixture
    def tool(self, tmp_path: Path) -> SafeShellTool:
        """Create a SafeShellTool for testing."""
        return SafeShellTool(worktree_path=tmp_path)

    def test_executes_allowed_command(self, tool: SafeShellTool) -> None:
        """Allowed commands should execute successfully."""
        result = tool.execute("echo hello")
        assert result.status == "ACCEPT"
        assert "hello" in result.output
        assert result.exit_code == 0

    def test_returns_exit_code(self, tool: SafeShellTool, tmp_path: Path) -> None:
        """Exit code should be captured."""
        result = tool.execute("python -c 'exit(42)'")
        assert result.exit_code == 42

    def test_rejects_denied_command(self, tool: SafeShellTool) -> None:
        """Denied commands should not execute."""
        result = tool.execute("rm -rf /")
        assert result.status == "REJECT"
        assert "rejected" in result.output.lower()
        assert result.exit_code is None

    def test_runs_in_worktree(self, tmp_path: Path) -> None:
        """Commands should run in the worktree directory."""
        tool = SafeShellTool(worktree_path=tmp_path)
        result = tool.execute("pwd")
        assert str(tmp_path) in result.output

    def test_captures_stderr(self, tool: SafeShellTool) -> None:
        """stderr should be captured."""
        # Use a Python script file to avoid semicolon in command
        result = tool.execute("python3 -c 'import sys\nsys.stderr.write(\"error\")'")
        assert "stderr" in result.output.lower() or "error" in result.output

    def test_callable_interface(self, tool: SafeShellTool) -> None:
        """Tool should be callable and return string."""
        output = tool("echo test")
        assert isinstance(output, str)
        assert "test" in output


class TestSafeShellLogging:
    """Test RunLogger integration."""

    def test_logs_accepted_command(self, tmp_path: Path) -> None:
        """Accepted commands should be logged."""
        mock_logger = MagicMock()
        tool = SafeShellTool(
            worktree_path=tmp_path,
            run_logger=mock_logger,
            agent_name="developer",
        )

        tool.execute("echo hello")

        mock_logger.log_command.assert_called_once()
        call_kwargs = mock_logger.log_command.call_args
        assert call_kwargs[1]["agent_name"] == "developer"
        assert call_kwargs[1]["status"] == "ACCEPT"
        assert "echo" in call_kwargs[1]["command"]

    def test_logs_rejected_command(self, tmp_path: Path) -> None:
        """Rejected commands should be logged."""
        mock_logger = MagicMock()
        tool = SafeShellTool(
            worktree_path=tmp_path,
            run_logger=mock_logger,
            agent_name="qa",
        )

        tool.execute("rm -rf /")

        mock_logger.log_command.assert_called_once()
        call_kwargs = mock_logger.log_command.call_args
        assert call_kwargs[1]["status"] == "REJECT"


class TestSafeShellConfig:
    """Test custom configuration."""

    def test_custom_allowlist(self, tmp_path: Path) -> None:
        """Custom allowlist should be respected."""
        config = SafeShellConfig(allowlist={"custom_cmd"})
        tool = SafeShellTool(worktree_path=tmp_path, config=config)

        # Default command should be rejected
        is_valid, _ = tool.validate_command("git status")
        assert is_valid is False

        # Custom command should be allowed
        is_valid, _ = tool.validate_command("custom_cmd arg")
        assert is_valid is True

    def test_custom_denylist(self, tmp_path: Path) -> None:
        """Custom denylist should be respected."""
        config = SafeShellConfig(denylist={"dangerous"})
        tool = SafeShellTool(worktree_path=tmp_path, config=config)

        # rm should now be allowed (not in custom denylist)
        is_valid, _ = tool.validate_command("echo rm")
        assert is_valid is True

        # Custom denied pattern should be blocked
        is_valid, reason = tool.validate_command("dangerous command")
        assert is_valid is False

    def test_custom_timeout(self, tmp_path: Path) -> None:
        """Custom timeout should be used."""
        # Add sleep to allowlist for this test
        config = SafeShellConfig(
            timeout=1,
            allowlist={"sleep"},
        )
        tool = SafeShellTool(worktree_path=tmp_path, config=config)

        result = tool.execute("sleep 5")
        assert "timed out" in result.output.lower()

