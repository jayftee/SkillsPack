# Toolset

This project's environment, quality tools and folder layout were set up by the `init-python-project`
skill. This file says what each piece is and how to run it. `README.md` stays the project's own.

## Everyday commands

Every command runs in the development environment, so that environment's `python` must be the first
one on `PATH` (activate it, or put its folder and its `Scripts` folder first):

```text
python -m poethepoet <task>
```

Poe finds `python` through `PATH`, not through the interpreter that launched it. With another Python
first, tasks run that Python's tools, or fail with `No module named ...`. See [The environment](#the-environment).

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
| `audit` | `pip-audit --local`: known vulnerabilities in the environment's installed packages (needs network) | no |
| `package` | `check`, then a fresh wheel in `dist/` (needs network for the build backend) | `dist/`, `build/` |
| `smoke` | installs the newest wheel into a clean environment and runs the commands from another folder | no |

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

The tools are installed into one **dedicated development environment**, not into a folder inside the
project. For ArcGIS Pro that is a clone made for development; for plain Python it is any environment you
create (a `venv`, a conda environment). It must be one that nothing else depends on, because the install
below adds and may upgrade packages in it:

```text
python -m pip install -e . --group dev
```

(`--group` needs pip 25.1 or later.) The dev tools are listed in `pyproject.toml` under
`[dependency-groups]`, separate from the project's runtime `dependencies`, so installing the project
never pulls them in.

- **Quit VS Code, or disable its Ruff extension, before the first install into a clone that already has
  `ruff`.** The extension keeps `Scriptsuff.exe` running, Windows will not let pip replace it, and the
  install fails halfway, leaving `~uff*` folders in `site-packages` to delete by hand.
- **First on `PATH`.** `python -c "import sys; print(sys.executable)"` must print this environment's
  interpreter before you run any task (see above).
- **One development environment per project is safest.** Two projects installed into one share a single
  set of tool versions; whichever was installed last wins.
- **Keep a second, clean environment for runtime testing** (`poe smoke --python <its python>`). The
  development environment holds your tools and every other project you installed, so a missing
  dependency can hide there. A clean one cannot.
- **VS Code:** pick the environment with *Python: Select Interpreter*. The tasks, Ruff, mypy and the test
  runner follow that choice.

**ArcGIS Pro clones:**

- `typings/arcpy/__init__.pyi` makes mypy treat `arcpy` as untyped, because the stubs Esri ships with
  Pro 3.7.2 contain a syntax error that stops mypy. The file explains when to remove it.
- Importing `arcpy` needs a working ArcGIS Pro licence; when it is not initialised, `import arcpy` fails
  with `RuntimeError: The Product License has not been initialized`, including inside tests.
- The clone ships with some conflicts of its own (on Pro 3.7.2, `lifelines` wants `pandas<3` and the clone
  has 3.0.3); `pip check` reports them. They are not caused by the dev tools.
- `audit` scans the whole clone, Esri's packages included.

## Package and deploy

The deliverable is a **wheel**: one file that `pip` installs into any Python of the right version.

```text
python -m poethepoet package        # check, then dist/{{PROJECT_NAME}}-<version>-py3-none-any.whl
python -m poethepoet smoke          # try it in a throwaway venv, from another folder
```

`smoke` installs the newest wheel into a clean environment, runs every command in `[project.scripts]`
from an unrelated folder and uninstalls it again. It catches what the development environment hides:
files that did not make it into the wheel, dependencies that were never declared, and paths that only
work from the project folder. The arguments passed to each command are `[tool.smoke] arguments` in
`pyproject.toml`; each run must exit 0. To test in your clean runtime environment instead, for example
an ArcGIS Pro clone that sees `arcpy`:

```text
python -m poethepoet smoke --python "<clone>\python.exe"
```

**On the target machine**, install into the Python whose `Scripts` folder is on the user's `PATH`:

```text
python -m pip install <wheel>                  # the commands appear in that Scripts folder
python -m pip install --upgrade <wheel>        # a newer version
python -m pip uninstall {{PROJECT_NAME}}
```

Rules that keep this working:

- **Bump `version` in `pyproject.toml` by hand** for every release; pip skips a wheel whose version it
  already has.
- **Runtime dependencies go in `[project].dependencies`**, never in the `dev` group. Everything installed
  into one Python shares it, so keep them few and their version ranges loose.
- **Data the program needs goes inside the package**, is listed under `[tool.setuptools.package-data]`,
  and is read with `importlib.resources`. A path like `data/x.json` only works from the project folder.
- **Give each command a distinctive name.** Two packages installing the same command name overwrite
  each other silently.
- **`arcpy` cannot be declared as a dependency** (it is not on PyPI). The target machine's Python must
  already provide it, and `requires-python` is the development environment's version.
- **Never copy the environment itself** to another machine; ship the wheel.

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
scripts/
    smoke.py         the deployment smoke test (poe smoke)
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
