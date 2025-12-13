"""
Tool factory for creating agent-specific tool instances.

Each agent gets its own set of tools bound to its worktree.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crewai.run_logger import RunLogger


def create_tools(worktree_path: str, run_logger: "RunLogger", agent_name: str) -> list:
    """
    Create tools bound to a specific worktree.

    Args:
        worktree_path: Absolute path to the agent's worktree
        run_logger: RunLogger instance for audit logging
        agent_name: Name of the agent (for logging)

    Returns:
        List of tool functions bound to the worktree
    """
    # TODO: Implement in Phase 1
    # - safe_shell tool
    # - write_file tool
    # - read_file tool
    raise NotImplementedError("Tool factory not yet implemented")

