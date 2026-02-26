<!--
  SYNC IMPACT REPORT
  ==================
  Version: 1.0.0
  Bump rationale: Initial ratification of project constitution.

  Principles:
    - I. Cross-Platform Compatibility
    - II. Plugin Architecture
    - III. Comprehensive Testing (NON-NEGOTIABLE)
    - IV. Code Quality Enforcement
    - V. Dependency Stewardship

  Sections:
    - Technology & Dependency Constraints
    - Development Workflow
    - Governance

  Templates requiring updates:
    - .specify/templates/plan-template.md ........... ✅ no changes needed
    - .specify/templates/spec-template.md ........... ✅ no changes needed
    - .specify/templates/tasks-template.md .......... ✅ no changes needed
    - .specify/templates/checklist-template.md ...... ✅ no changes needed
    - .specify/templates/agent-file-template.md ..... ✅ no changes needed
    - .specify/templates/commands/*.md .............. ✅ no command files exist

  Follow-up TODOs: None
-->

# Briefcase Constitution

## Core Principles

### I. Cross-Platform Compatibility

Briefcase exists to convert Python projects into standalone native
applications across macOS, Windows, Linux, iOS, Android, and Web.

- Every feature MUST work on all actively supported platforms, or
  MUST be explicitly scoped to a platform-specific module with clear
  documentation of platform applicability.
- Platform-specific behavior MUST be isolated in dedicated platform
  modules (`src/briefcase/platforms/<platform>/`). Shared logic MUST
  NOT contain platform conditionals when a platform module can own
  the behavior instead.
- New platform or format support MUST be added via the entry-point
  plugin system, never by hard-coding platform names in core logic.
- Regressions on any supported platform are treated as blocking
  defects regardless of which platform the contributor develops on.

### II. Plugin Architecture

Briefcase uses Python entry points to provide an extensible,
composable system of platforms, formats, bootstraps, debuggers,
and publication channels.

- All platform backends, output formats, app bootstraps, debuggers,
  and publication channels MUST be registered as `setuptools`
  entry points in `pyproject.toml`.
- New extension categories MUST follow the existing entry-point
  pattern (`briefcase.<category>`) and MUST NOT introduce
  alternative registration mechanisms.
- Core code MUST discover capabilities through entry-point
  enumeration; it MUST NOT import platform/format modules directly
  except via the plugin interface.
- Third-party plugins MUST be a first-class consideration: public
  APIs consumed by plugins MUST be documented and changes MUST
  follow the project's deprecation policy.

### III. Comprehensive Testing (NON-NEGOTIABLE)

The project enforces 100% code coverage with no exceptions.

- Test coverage MUST remain at 100% as enforced by
  `coverage report --fail-under=100` in CI. Any new code that
  reduces coverage below 100% MUST NOT be merged.
- Tests MUST run across all supported Python versions
  (currently 3.10 through 3.14) and across macOS, Linux, and
  Windows via the CI matrix.
- Platform-conditional coverage exclusions (`no-cover-if-*`) are
  permitted only for code that is genuinely unreachable on a given
  OS or Python version. Each exclusion MUST have a corresponding
  rule in `pyproject.toml` under
  `[tool.coverage.coverage_conditional_plugin.rules]`.
- `pytest` warnings MUST be treated as errors
  (`filterwarnings = ["error"]`). New warnings MUST be resolved,
  not suppressed, unless a documented upstream issue justifies a
  temporary filter.

### IV. Code Quality Enforcement

Automated tooling gates MUST run before code reaches review.

- Pre-commit hooks (`ruff-format`, `ruff-check`, `codespell`,
  `docformatter`, `trailing-whitespace`, `end-of-file-fixer`) MUST
  pass on every commit. Contributors MUST NOT bypass hooks via
  `--no-verify`.
- Ruff lint rules defined in `pyproject.toml` under `[tool.ruff.lint]`
  are the project standard. Adding new `ignore` entries requires
  explicit justification in the PR description.
- Changelog entries MUST be present for *all* changes, managed via
  `towncrier` fragments in the `changes/` directory. Minor changes
  or housekeeping updates SHOULD use the `misc` fragment type, as
  SHOULD any bugfix or change to a feature that has not yet been
  part of a formal release. Snippet text MUST describe the user-
  facing impact of a change, not the specifics of the
  implementation. CI enforces this with `towncrier check`.
- Spelling MUST be verified by `codespell`. Domain-specific terms
  MUST be added to the ignore list rather than disabling the check.

### V. Dependency Stewardship

Briefcase is an end-user tool; dependency choices directly affect
every downstream project that uses it.

- Runtime dependencies MUST specify version ranges: a minimum
  version satisfying the project's API needs and, for semver
  packages, an upper bound excluding the next major version.
- Core Python ecosystem toolchain dependencies (e.g., `pip`,
  `wheel`, `setuptools`, `build`) MUST specify only a minimum
  version with no upper cap, because the latest version is always
  preferred.
- Calendar-versioned dependencies MUST NOT have an upper pin,
  as calendar versions provide no API-stability signal.
- Developer/test dependencies MUST be pinned to exact versions
  to guarantee reproducible environments.
- New runtime dependencies require justification in the PR
  description addressing: why the dependency is necessary, license
  compatibility (BSD-3-Clause), impact on installation size, and
  project maturity. Dependencies MUST only be added if the upstream
  project has a history of consistent maintenance and of stable,
  backward-compatible development.

## Technology & Dependency Constraints

- **Language**: Python >= 3.10 (currently 3.10 through 3.14).
- **License**: BSD-3-Clause. All dependencies and contributions
  MUST be compatible with this license.
- **Build system**: setuptools with setuptools_scm for versioning.
  Version is derived from git tags; MUST NOT be hard-coded.
- **CLI entry point**: `briefcase` via `briefcase.__main__:main`.
- **Output rendering**: `rich` library for terminal UI. All user-
  facing output MUST go through Rich's console interface, not raw
  `print()` (enforced by the `T20` ruff rule).
- **HTTP client**: `httpx` for all network operations.
- **Template engine**: `cookiecutter` for app scaffolding.
- **Platform-specific dependencies**: All platform-specific
  dependencies (e.g., `dmgbuild` for macOS) MUST use appropriate
  environment markers (e.g., `sys_platform == 'darwin'`) so they
  are only installed on the relevant platform.

## Development Workflow

- **Branching**: Feature branches off `main`. All changes arrive
  via pull request.
- **CI gates**: Pre-commit, test suite (all Python versions x
  platforms), coverage (100%), towncrier check, and docs build
  MUST pass before merge.
- **Changelog**: Every change MUST include a towncrier fragment
  categorized as `feature`, `bugfix`, `removal`, `doc`, or `misc`.
  Fragments MUST describe user-facing impact, not implementation
  details. Minor or housekeeping changes SHOULD use `misc`, as
  SHOULD any bugfix or change to a feature that has not yet been
  part of a formal release.
- **Documentation**: Docs are built using `tox -e docs-all`
  (MkDocs via beeware-docs-tools, on Python 3.12). API or
  behavioral changes MUST include corresponding documentation
  updates.
- **Versioning**: The project uses setuptools_scm (git-tag-derived
  versions). Release tags MUST follow PEP 440.

## Governance

This constitution is the authoritative reference for Briefcase
development practices. It supersedes informal conventions and
ad-hoc decisions.

- **Amendment procedure**: Amendments MUST be proposed via pull
  request modifying this file. The PR description MUST state the
  rationale and the semantic version bump (MAJOR/MINOR/PATCH).
  Amendments require maintainer approval before merge.
- **Versioning policy**: This constitution follows semantic
  versioning. MAJOR for principle removals or incompatible
  redefinitions; MINOR for new principles or materially expanded
  guidance; PATCH for clarifications and typo fixes.
- **Compliance review**: All pull requests SHOULD be evaluated
  against these principles. Deviations MUST be explicitly justified
  in the PR description and approved by a maintainer.
- **Guidance file**: Runtime development guidance (IDE setup,
  local workflow tips) belongs in the agent-file or project README,
  not in this constitution.

**Version**: 1.0.0 | **Ratified**: 2026-02-26 | **Last Amended**: 2026-02-26
