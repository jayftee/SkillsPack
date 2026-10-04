# Toolset

This project's environment, quality tools and folder layout were set up by the `init-python-project`
skill. This file says what each piece is and how to run it. `README.md` stays the project's own.

## Everyday commands

Every command runs through the project's interpreter, so nothing needs to be activated first:

```text
{{INTERPRETER}} -m poethepoet <task>
```

In VS Code the same tasks are under **Terminal > Run Task**, and `Ctrl+Shift+B` runs `check`.

| Task | What it does | Changes files? |
|---|---|---|
| `check` | `format`, `lint`, `types`, `imports`, `test`, `crap` in that order; stops at the first failure | no |
| `format` | `ruff format --check`: is the code formatted? | no |
| `lint` | `ruff check`: lint rules | no |
| `types` | `mypy` (strict) on `src` and `tests` | no |
| `imports` | `lint-imports`: layers only import downwards (see below) | no |
| `test` | `pytest` with branch coverage; fails under 80 %; writes `lcov.info` | no |
| `crap` | `crap4py`: fails if any function's CRAP score is above 30 (run `test` first) | no |
| `fix` | applies ruff's safe fixes, then formats | **yes** |
| `audit` | `pip-audit --local`: known vulnerabilities in the `.venv`'s own packages (needs network) | no |

The commands themselves are defined once, in `pyproject.toml` under `[tool.poe.tasks]`.
`.vscode/tasks.json` only calls them.

## One configuration file

All tool settings live in `pyproject.toml`: ruff, mypy, pytest, coverage, import-linter and poe.
**Do not add** `ruff.toml`, `.ruff.toml`, `mypy.ini`, `.mypy.ini`, `pytest.ini`, `.coveragerc`,
`setup.cfg`, `tox.ini`, `.importlinter` or `pyrightconfig.json`. Each tool reads its own file *first*
and then silently ignores its section in `pyproject.toml`, so edits there would stop having any effect.

Only `.editorconfig`, `.gitignore`, `.gitattributes` and `.vscode/` sit outside it, because they are
not Python tools.

## The environment

The project always uses its own `.venv`. Dev tools are installed with:

```text
{{INTERPRETER}} -m pip install -e . --group dev
```

(`--group` needs pip 25.1 or later.) The dev tools are listed in `pyproject.toml` under
`[dependency-groups]`, separate from the project's runtime `dependencies`, so installing the project
never pulls them in.

**ArcGIS Pro projects:** the `.venv` was created from a clone's `python.exe` with
`--system-site-packages`. `arcpy` and the clone's packages are importable, but the dev tools live only
in `.venv`; the clone itself is never modified. To rebuild it:

```text
"<clone>\python.exe" -m venv --system-site-packages .venv
```

Things to know on that path:

- When the clone already has a dev tool (it ships with pytest, for example), pip uses the clone's copy
  instead of installing one into `.venv`. That is why every poe task starts with `python -m`: it finds
  the tool wherever it lives, instead of whatever happens to be first on PATH.
- A few packages in `.venv` replace the clone's version for code run from `.venv` (on Pro 3.7.2:
  `rich`, needed by a dev tool). `<interpreter> -m pip list --local` shows what `.venv` holds.
- `typings/arcpy/__init__.pyi` makes mypy treat `arcpy` as untyped, because the stubs Esri ships with
  Pro 3.7.2 contain a syntax error that stops mypy. The file explains when to remove it.
- Importing `arcpy` needs a working ArcGIS Pro licence; when it is not initialised, `import arcpy` fails
  with `RuntimeError: The Product License has not been initialized`, including inside tests.

## Code layout

```text
src/{{PACKAGE_NAME}}/
    __main__.py      entry point: python -m {{PACKAGE_NAME}}, or the {{PROJECT_NAME}} command
    services/        business logic                     (top layer)
    repositories/    your stored data    | clients/     other people's systems
    config/          settings
    models/          domain objects
    enums/           enumerations
    exceptions/      errors
    utils/           generic helpers                    (bottom layer)
tests/
    unit/            mirrors src/{{PACKAGE_NAME}}/ folder by folder
    integration/     grouped by workflow or boundary
docs/
```

Each layer folder has a `_what_goes_here.md`. Read it before adding a file; `utils/` has the strictest
rules.

A layer may import the layers listed below it, never the ones above. `repositories` and `clients` sit
side by side and may not import each other. `poe imports` enforces this (`[tool.importlinter]`).
If you delete an unused layer folder, remove it from that contract too.

Imports are always absolute (`from {{PACKAGE_NAME}}.services.x import Y`); relative imports fail
`poe lint`.

## Tests

The folder says what kind of test it is: `tests/unit/` or `tests/integration/`. Markers describe traits
that cut across both: `slow`, `database`, `external` (e.g. `pytest -m "not external"`). Unknown markers
are errors. Tests run in a random order on every run (`pytest-randomly`), which exposes tests that depend
on each other. To repeat the previous order while debugging a failure, run `test --randomly-seed=last`;
`test -p no:randomly` switches the shuffling off.

## The sample

The greeting code (`GREETING_NAME` / `GREETING_STYLE` environment variables in, one line of text out)
shows each convention and gives every tool something real to check. Replace it with your own code:
delete the sample modules and their tests, keep the folders and their `_what_goes_here.md`, and run
`check`.

## Thresholds to revisit

These are starting values, not decisions made against real code:

| Setting | Where | Value |
|---|---|---|
| Line length | `[tool.ruff]` | 120 |
| Cyclomatic complexity per function | `[tool.ruff.lint.mccabe]` | 10 |
| Minimum coverage | `[tool.coverage.report]` | 80 % |
| Maximum CRAP score | `crap` task | 30 |

`crap4py` is pinned to `0.1.1` because it is a young, single-maintainer tool. If it ever stops working,
the complexity limit and the coverage minimum still cover most of what it checks.
