# Briefcase — Agent Development Guide

Briefcase converts Python projects into standalone native applications for macOS, Windows, Linux, iOS, Android, and Web. This guide provides the context AI coding agents need to contribute effectively.

## Quick Reference

- **Language**: Python >= 3.10 (3.10–3.14 supported)
- **Dev environment**: Python 3.13 virtualenv with `dev` dependency group
- **License**: BSD-3-Clause
- **Entry point**: `briefcase` via `src/briefcase/__main__.py:main()`
- **Test framework**: pytest (100% coverage required, no exceptions)
- **Linting**: ruff (format + check), codespell, docformatter
- **Docs**: MkDocs via beeware-docs-tools

## Development Environment Setup

All development must use a Python 3.13 virtual environment with the `dev` dependency group installed:

```bash
python3.13 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e . --group dev
```

This installs tox, pre-commit, and other development tooling. All test execution and CI-equivalent checks run through tox.

## Project Layout

```text
src/briefcase/
├── __main__.py          # CLI entry point
├── cmdline.py           # Command-line parsing and dispatch
├── config.py            # AppConfig / GlobalConfig from pyproject.toml
├── console.py           # Rich-based Console (ALL user I/O)
├── exceptions.py        # BriefcaseError hierarchy
├── constants.py         # Reserved words and constants
├── commands/            # Command implementations
│   ├── base.py          # BaseCommand ABC
│   ├── create.py, build.py, run.py, update.py, package.py,
│   │   publish.py, dev.py, new.py, open.py, convert.py, upgrade.py
├── platforms/           # Platform plugins (one subdir per OS)
│   ├── __init__.py      # get_platforms(), get_output_formats()
│   ├── macOS/, linux/, windows/, android/, iOS/, web/
├── integrations/        # External tool wrappers
│   ├── base.py          # Tool / ManagedTool ABCs, ToolCache
│   └── subprocess.py, android_sdk.py, docker.py, xcode.py, ...
├── bootstraps/          # App template bootstraps
├── channels/            # Publication channels (App Store, Play Store)
└── debuggers/           # Debugger plugins (pdb, debugpy)

tests/                   # Mirrors src/ structure exactly
├── conftest.py          # Root fixtures (no_print, dummy_console, configs)
├── utils.py             # DummyConsole, PartialMatchString, file helpers
├── commands/
├── platforms/
├── integrations/
└── ...

docs/en/                 # MkDocs documentation (English)
changes/                 # Towncrier changelog fragments
automation/              # Separate automation subpackage
debugger/                # Separate debugger subpackage (own pyproject.toml)
```

## Critical Rules

### No `print()` — ever

All user-facing output MUST go through the `Console` object, never raw `print()`. The `T20` ruff rule bans print statements in source code, and the `no_print` autouse test fixture will **fail any test** where briefcase code calls `print()`.

Use `self.tools.console.info()`, `.verbose()`, `.debug()`, `.warning()`, or `.error()` instead.

### 100% test coverage — no exceptions

Coverage is enforced by `coverage report --fail-under=100` in CI. Every line of new code must be covered. Platform-specific code that is unreachable on certain OSes must use conditional coverage pragmas:

```python
# pragma: no-cover-if-not-macos
# pragma: no-cover-if-is-windows
# pragma: no-cover-if-lt-py312
```

Each pragma must have a corresponding rule in `pyproject.toml` under `[tool.coverage.coverage_conditional_plugin.rules]`.

### Warnings are errors

pytest is configured with `filterwarnings = ["error"]`. Do not suppress warnings — fix the cause.

## Architecture Patterns

### Command dispatch

1. `cmdline.parse_cmdline()` resolves platform + format from CLI args
2. Loads the format module via entry points
3. Gets the command class via `getattr(format_module, command_name)`
4. Command classes are composed via **multiple inheritance**:

```python
class macOSAppBuildCommand(
    macOSAppMixin,          # format-specific paths/behavior
    macOSSigningMixin,      # platform signing logic
    AppPackagesMergeMixin,  # utility mixin
    BuildCommand,           # base command from commands/
):
    ...
```

### Platform module conventions

Each format file (e.g., `platforms/macOS/app.py`) must export **module-level aliases** matching command names:

```python
create = macOSAppCreateCommand
update = macOSAppUpdateCommand
build = macOSAppBuildCommand
run = macOSAppRunCommand
package = macOSAppPackageCommand
publish = macOSAppPublishCommand
open = macOSAppOpenCommand
```

New platforms/formats MUST register via entry points in `pyproject.toml`, never by hard-coding in core logic.

### Tool system

- `Tool` ABC with `verify()` classmethod (calls `verify_host()` then `verify_install()`)
- `ManagedTool(Tool)` adds `exists()`, `install()`, `uninstall()`, `upgrade()`
- Tools register via `__init_subclass__` into `tool_registry`
- Accessed through `ToolCache` on `command.tools` (e.g., `self.tools.subprocess`, `self.tools.java`)
- `ToolCache` wraps stdlib modules (`os`, `platform`, `shutil`, `sys`) to enable test mocking

### Error handling

All errors derive from `BriefcaseError(Exception)` with an `error_code` integer. Key subtypes:

- `BriefcaseCommandError` (200) — general operational errors
- `BriefcaseConfigError` (100) — configuration problems
- `NetworkFailure`, `MissingToolError`, `InvalidDeviceError` — specific failure modes
- `HelpText` — displays help, not an error
- `BriefcaseWarning` — non-fatal (exit code 0)

## Testing Patterns

All commands below assume the `dev` dependency group is installed in a Python 3.13 virtual environment (see setup above).

### Test organization

Tests mirror the source tree. Within each area, tests are organized by method/behavior:

```text
tests/commands/create/test_install_app_requirements.py
tests/commands/build/test_call.py
tests/platforms/macOS/app/test_build.py
```

### Dummy command pattern

Tests create concrete subclasses of abstract commands that track method calls in an `actions` list:

```python
class DummyBuildCommand(BuildCommand):
    def build(self, app, **kwargs):
        self.actions.append(("build", app.app_name))
        return {}

# Then assert exact action sequence:
assert build_command.actions == [
    ("verify-host",),
    ("verify-tools",),
    ("build", "first"),
]
```

### Mock conventions

- Use `MagicMock(spec_set=...)` (not `spec=`) for strict mocking
- External tools: mock via `mock.MagicMock(spec_set=Subprocess)` on `command.tools.subprocess`
- Filesystem layout: use `create_file()` from `tests/utils.py`
- Downloads: use `mock_file_download()`, `mock_zip_download()`, `mock_tgz_download()` side-effect factories from `tests/utils.py`
- `ToolCache` mocks wrap stdlib modules for test isolation

### Key fixtures (from `tests/conftest.py`)

- `no_print` (autouse) — fails tests that call `print()` from briefcase code
- `dummy_console` — `DummyConsole` that records prompts and returns programmed values
- `sleep_zero` — replaces `time.sleep` with instant returns
- `first_app_config` / `first_app_unbuilt` / `first_app` — graduated app fixtures (config only / bundle exists / binary exists)

### Key helpers (from `tests/utils.py`)

- `DummyConsole` — captures user interaction
- `PartialMatchString` / `NoMatchString` — flexible assertion matching
- `create_file()`, `create_plist_file()`, `create_zip_file()`, `create_tgz_file()` — filesystem helpers
- `create_wheel()`, `create_installed_package()` — fake Python package creation

## Running Tests and Checks

All commands below assume the `dev` dependency group is installed in a Python 3.13 virtual environment (see Development Environment Setup above).

```bash
# Run full test suite with coverage
tox -e py-cov

# Run tests fast (parallel, no coverage)
tox -e py-fast

# Run pre-commit hooks
tox -e pre-commit

# Run just ruff
ruff check src/ tests/
ruff format --check src/ tests/

# Coverage report (must be 100%)
tox -e coverage

# Lint docs
tox -e docs-lint

# Build docs
tox -e docs-all

# Check changelog fragments
tox -e towncrier-check
```

## Changelog

Every change requires a towncrier fragment in `changes/`:

```text
changes/{issue_number}.{type}.md
```

Types: `feature`, `bugfix`, `removal`, `doc`, `misc`.

Fragment text must describe user-facing impact, not implementation details. Use `misc` for housekeeping, minor changes, or changes to features not yet in a formal release.

## Documentation Style

Markdown files in this project (including `AGENTS.md`, `docs/en/`, and `changes/` fragments) must **not** use hard line breaks to enforce an 80-character column limit. Each paragraph or list item must be written as a single unbroken line, regardless of its length. Let the reader's editor or renderer handle wrapping.

This rule applies to all prose. Code blocks, directory trees, and other pre-formatted blocks are exempt — keep those readable within their own constraints.

When writing or editing any `.md` file, do not insert newlines mid-sentence or mid-paragraph to stay within 80 columns.

## Code Style

- **Class naming**: `{Platform}{Format}{Action}Command` (e.g., `macOSAppBuildCommand`)
- **Mixin naming**: `{Platform}{Feature}Mixin` (e.g., `macOSSigningMixin`)
- **Platform casing**: Preserve original (macOS, iOS, not macos)
- **Docstrings**: Google/Sphinx style with `:param:` / `:returns:` / `:raises:` — formatted by docformatter
- **Imports**: `from __future__ import annotations` used widely for PEP 604 unions
- **Paths**: Always use `pathlib.Path` objects, never raw strings
