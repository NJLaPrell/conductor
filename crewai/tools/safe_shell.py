"""
SafeShellTool - Restricted shell command execution with safety guardrails.

Provides a safe way for agents to execute shell commands with:
- Command allowlist (git, pytest, python, etc.)
- Denylist patterns (rm, sudo, chmod, mv)
- Metacharacter blocking (|, ;, &&, etc.)
- Working directory enforcement
- Audit logging via RunLogger
"""

from __future__ import annotations

import re
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from crewai.run_logger import RunLogger


@dataclass
class SafeShellConfig:
    """Configuration for SafeShellTool."""

    # Commands that are allowed (first word of command)
    allowlist: set[str] = field(default_factory=lambda: {
        "git",
        "pytest",
        "python",
        "python3",
        "pip",
        "pip3",
        "cat",
        "ls",
        "head",
        "tail",
        "grep",
        "find",
        "echo",
        "pwd",
        "cd",
        "diff",
        "wc",
        "sort",
        "uniq",
        "mkdir",
        "touch",
    })

    # Patterns that are never allowed (substring match)
    denylist: set[str] = field(default_factory=lambda: {
        "rm",
        "sudo",
        "chmod",
        "chown",
        "mv",
        "dd",
        "mkfs",
        "fdisk",
        "kill",
        "pkill",
        "killall",
        "reboot",
        "shutdown",
        "halt",
        "poweroff",
    })

    # Shell metacharacters that indicate dangerous operations
    blocked_patterns: list[str] = field(default_factory=lambda: [
        "|",      # Pipe
        ";",      # Command separator
        "&&",     # AND chain
        "||",     # OR chain
        ">",      # Redirect output
        "<",      # Redirect input
        ">>",     # Append output
        "$(", 
        "`",      # Command substitution
        "${",     # Variable expansion
        "\\n",    # Newline escape
    ])

    # Timeout for command execution (seconds)
    timeout: int = 30

    # Maximum output length to return
    max_output_length: int = 10000


@dataclass
class CommandResult:
    """Result of a shell command execution."""

    status: Literal["ACCEPT", "REJECT"]
    command: str
    output: str
    exit_code: int | None = None
    rejection_reason: str | None = None


class SafeShellTool:
    """
    Safe shell command executor with security guardrails.
    
    Usage:
        tool = SafeShellTool(
            worktree_path="/path/to/worktree",
            run_logger=logger,
            agent_name="developer"
        )
        result = tool.execute("git status")
    """

    def __init__(
        self,
        worktree_path: str | Path,
        run_logger: RunLogger | None = None,
        agent_name: str = "unknown",
        config: SafeShellConfig | None = None,
    ):
        self.worktree = Path(worktree_path).resolve()
        self.run_logger = run_logger
        self.agent_name = agent_name
        self.config = config or SafeShellConfig()

    def validate_command(self, command: str) -> tuple[bool, str]:
        """
        Validate a command against safety rules.
        
        Args:
            command: The command string to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check for empty command
        if not command or not command.strip():
            return False, "Empty command"

        # Check for blocked metacharacters
        for pattern in self.config.blocked_patterns:
            if pattern in command:
                return False, f"Blocked metacharacter: {pattern!r}"

        # Parse command to get the base command
        try:
            parts = shlex.split(command)
        except ValueError as e:
            return False, f"Invalid command syntax: {e}"

        if not parts:
            return False, "Empty command after parsing"

        base_cmd = parts[0]

        # Check denylist (substring match anywhere in command)
        for denied in self.config.denylist:
            # Match as whole word to avoid false positives (e.g., "firmware" matching "rm")
            if re.search(rf'\b{re.escape(denied)}\b', command):
                return False, f"Denied command pattern: {denied!r}"

        # Check allowlist (base command must be in allowlist)
        if base_cmd not in self.config.allowlist:
            return False, f"Command not in allowlist: {base_cmd!r}"

        # Special validation for git commands
        if base_cmd == "git" and len(parts) > 1:
            git_subcmd = parts[1]
            dangerous_git_cmds = {"reset", "clean", "rebase", "push"}
            if git_subcmd in dangerous_git_cmds:
                # Allow push without --force
                if git_subcmd == "push":
                    if "--force" in parts or "-f" in parts:
                        return False, "git push --force is not allowed"
                elif git_subcmd == "reset":
                    if "--hard" in parts:
                        return False, "git reset --hard is not allowed"
                else:
                    return False, f"Dangerous git command: git {git_subcmd}"

        return True, "OK"

    def execute(self, command: str) -> CommandResult:
        """
        Execute a command with safety validation.
        
        Args:
            command: The command string to execute
            
        Returns:
            CommandResult with status, output, and metadata
        """
        # Validate command
        is_valid, reason = self.validate_command(command)

        if not is_valid:
            result = CommandResult(
                status="REJECT",
                command=command,
                output=f"Command rejected: {reason}",
                rejection_reason=reason,
            )
            self._log_command(result)
            return result

        # Execute the command
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=self.worktree,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
            )

            # Combine stdout and stderr
            output = proc.stdout
            if proc.stderr:
                output += f"\n[stderr]\n{proc.stderr}"

            # Truncate if too long
            if len(output) > self.config.max_output_length:
                output = output[:self.config.max_output_length] + "\n... [truncated]"

            result = CommandResult(
                status="ACCEPT",
                command=command,
                output=output or "(no output)",
                exit_code=proc.returncode,
            )

        except subprocess.TimeoutExpired:
            result = CommandResult(
                status="ACCEPT",  # Command was allowed but timed out
                command=command,
                output=f"Command timed out after {self.config.timeout}s",
                exit_code=-1,
            )

        except Exception as e:
            result = CommandResult(
                status="ACCEPT",  # Command was allowed but failed
                command=command,
                output=f"Execution error: {e}",
                exit_code=-1,
            )

        self._log_command(result)
        return result

    def _log_command(self, result: CommandResult) -> None:
        """Log the command to the RunLogger if available."""
        if self.run_logger is not None:
            summary = result.rejection_reason or result.output[:100]
            self.run_logger.log_command(
                agent_name=self.agent_name,
                work_dir=str(self.worktree),
                status=result.status,
                command=result.command,
                result_summary=summary,
            )

    def __call__(self, command: str) -> str:
        """
        Execute command and return output string (for CrewAI tool compatibility).
        
        Args:
            command: The command to execute
            
        Returns:
            Command output or rejection message
        """
        result = self.execute(command)
        return result.output

