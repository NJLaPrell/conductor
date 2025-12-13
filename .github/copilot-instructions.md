# Copilot Instructions (Workspace)

You are helping implement a design/prototype repo for an autonomous multi-agent pipeline.

Constraints:
- Safety first: no destructive shell commands, no force git operations, no command chaining.
- Do not write secrets into files. Read keys from env vars only.
- Prefer small, reviewable diffs; write tests for safety-critical logic.
- Keep configuration explicit and documented in `docs/`.
- Don’t add heavyweight dependencies unless necessary; justify any new dependency.