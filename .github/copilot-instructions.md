# Copilot Instructions (Workspace)

You are helping implement a design/prototype repo for an autonomous multi-agent pipeline.

## Git Workflow (Required)

For every task:
1. Create GitHub issue if it doesn't exist
2. Create branch from `main`: `feature/<issue>-<desc>` or `defect/<issue>-<desc>`
3. Checkout the branch
4. Implement with tests
5. Commit and push
6. Open a PR

## Constraints

- Safety first: no destructive shell commands, no force git operations, no command chaining.
- Do not write secrets into files. Read keys from env vars only.
- Prefer small, reviewable diffs; write tests for safety-critical logic.
- Keep configuration explicit and documented in `docs/`.
- Don't add heavyweight dependencies unless necessary; justify any new dependency.