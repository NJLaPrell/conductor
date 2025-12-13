#!/usr/bin/env bash
#
# Setup git worktrees for the multi-agent pipeline.
#
# This script creates the required branches and worktrees as siblings
# of the main repo directory.
#
# Usage:
#   ./scripts/setup_worktrees.sh
#
# Prerequisites:
#   - Must be run from the main repo root
#   - Git repo must be initialized
#   - No uncommitted changes (clean working tree)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Verify we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    error "Not in a git repository. Run this from the main repo root."
fi

# Verify clean working tree
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    error "Working tree is dirty. Commit or stash changes first."
fi

# Get repo root and parent directory
REPO_ROOT=$(git rev-parse --show-toplevel)
PARENT_DIR=$(dirname "$REPO_ROOT")

info "Repo root: $REPO_ROOT"
info "Worktrees will be created in: $PARENT_DIR"

# Define branches and worktree paths
declare -A WORKTREES=(
    ["feature/dev-task"]="$PARENT_DIR/developer-agent-work"
    ["feature/arch-review"]="$PARENT_DIR/architect-agent-work"
    ["feature/qa-test"]="$PARENT_DIR/qa-agent-work"
)

# Get current branch for reference
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
info "Current branch: $CURRENT_BRANCH"

# Create branches if they don't exist
for branch in "${!WORKTREES[@]}"; do
    if git show-ref --verify --quiet "refs/heads/$branch"; then
        info "Branch '$branch' already exists"
    else
        info "Creating branch '$branch' from '$CURRENT_BRANCH'"
        git branch "$branch"
    fi
done

# Create worktrees
for branch in "${!WORKTREES[@]}"; do
    worktree_path="${WORKTREES[$branch]}"
    
    if [ -d "$worktree_path" ]; then
        warn "Worktree already exists: $worktree_path"
    else
        info "Creating worktree: $worktree_path -> $branch"
        git worktree add "$worktree_path" "$branch"
    fi
done

# Verify setup
info ""
info "=== Worktree Setup Complete ==="
git worktree list

info ""
info "Next steps:"
info "  1. cd $REPO_ROOT"
info "  2. pip install -e '.[dev]'"
info "  3. Run the pipeline: python -m crewai.orchestrator --spec '...'"

