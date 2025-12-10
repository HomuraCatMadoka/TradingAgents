# Contributing Guide

- [Branch Strategy](#branch-strategy)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Environment Setup](#environment-setup)
- [Running Tests & Quality Checks](#running-tests--quality-checks)
- [Documentation Updates](#documentation-updates)
- [FAQ](#faq)

## Branch Strategy
- Use short-lived branches from `main`: `feature/*` for new work, `bugfix/*` for fixes, `hotfix/*` for urgent production issues.
- Keep diffs small; rebase on `main` before opening a PR.
- Delete merged branches to avoid drift.

## Commit Messages
- Follow Conventional Commits: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
- Scope is optional but encouraged (e.g., `feat(frontend): add theme hook`).
- One logical change per commit; avoid noisy reformat-only commits unless necessary.

## Pull Request Process
- Title: concise summary of change and area (e.g., `Add cursor pagination to /api/protocols`).
- Checklist before requesting review:
  - [ ] All tests/linters pass (see below).
  - [ ] Added/updated docs when behavior or commands change.
  - [ ] Checked for breaking changes and called them out explicitly.
  - [ ] Linked issues and described risk/rollback plan.
- Review standards:
  - Prefer clear, minimal solutions (KISS/YAGNI). Reject speculative abstractions.
  - Fail PRs on missing error handling, unsafe defaults, or untested edge cases.
  - Require examples for APIs and configs touched.

## Environment Setup
### Frontend (miniapp)
```bash
cd miniapp/frontend
npm install
npm run dev     # local dev server
npm run build   # type-check + production build
npm run lint    # eslint
```

### Backend (miniapp)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
pip install -r miniapp/backend/requirements.txt
pip install pytest ruff mypy
```

## Running Tests & Quality Checks
- Backend: `python -m pytest`, `ruff check .`, `mypy .`
- Frontend: `npm run lint` (add vitest later when available)
- Root project tests: `python -m pytest tests`
- Keep checks fast; prefer focused tests over broad integration unless required.

## Documentation Updates
- Follow `CLAUDE.md` rules:
  - Update `PROJECT_STATUS.md` when completing tasks or adding TODOs.
  - Append to `DeFiAgent_CHANGELOG.md` for major changes only; never rewrite history.
  - Add new docs to `docs/README.md` index.
- For new APIs/configs, include request/response samples and default values.

## FAQ
- **Where do I record progress?** Update `PROJECT_STATUS.md`; for major milestones append `DeFiAgent_CHANGELOG.md`.
- **How to report breaking changes?** Call them out in the PR description and add migration steps in the doc relevant to the module.
- **Tests are slow—what can I skip?** Nothing critical: at minimum run linters + targeted pytest on changed areas; add more tests instead of skipping. If a check is flaky, document it in the PR and open an issue.
