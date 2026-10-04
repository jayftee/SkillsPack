---
name: init-python-project
description: Set up this repo's baseline Python environment in a project folder — a project .venv (from system Python or an ArcGIS Pro clone), ruff, mypy, pytest with coverage, import-linter, crap4py and pip-audit, all configured in one pyproject.toml and run through poethepoet and VS Code tasks, plus a layered src/ package with a working sample. Use when starting a new Python project, or when asked to add the standard Python tooling to an existing one.
---

# Initialize a Python Project

Everything that can be copied as-is lives in [`files/`](./files/), plus [`files-arcgis/`](./files-arcgis/) for the
ArcGIS Pro path. [`scripts/apply_template.py`](./scripts/apply_template.py) copies those trees into the target, fills in the `{{TOKENS}}` and never overwrites. What the payload
contains and how to use it is in [`files/TOOLSET.md`](./files/TOOLSET.md), which travels with every project.
Why each choice was made is in [`CONTEXT.md`](./CONTEXT.md): read it before changing a decision.

In the commands below, `<venv-python>` is `.venv\Scripts\python.exe` at the target root
(`.venv/bin/python` outside Windows).

## 1. Inspect the target

The target is the current working directory unless the user named another folder. Record:

- **Stray config files**: any of `ruff.toml`, `.ruff.toml`, `mypy.ini`, `.mypy.ini`, `pytest.ini`,
  `.pytest.ini`, `.coveragerc`, `setup.cfg`, `tox.ini`, `.importlinter`, `pyrightconfig.json`.
  Each silently overrides its section of `pyproject.toml`. If any exist, stop here: show them to the
  user and agree on moving their settings into `pyproject.toml` (or deleting them) before going on.
  The script refuses to run while one exists.
- **Fresh or existing**: an existing project has a `pyproject.toml`, a `src/` package or other Python
  code. An existing project takes the merge path in step 4.
- **Existing `.venv`**: whether one exists, and its version (`<venv-python> --version`).

Done when: no stray config file remains, and you know which path (fresh or existing) and whether a
`.venv` exists.

## 2. Agree on names and the base Python

Ask the user, then show the final values back before continuing:

- **Project name**: lowercase words joined by hyphens (`parcel-sync`). The **package name** is derived
  by replacing `-` with `_` (`parcel_sync`); the user may override it.
- **Base Python**, the interpreter that creates `.venv`:
  - **System Python** (default): a specific version the user names (`py -3.13`), or `python` on PATH.
  - **An ArcGIS Pro clone**: the path to the clone's `python.exe`, in the `envs` folder of the Pro
    install (`<Pro>\bin\Python\envs\<clone>\python.exe`) or under
    `%LOCALAPPDATA%\ESRI\conda\envs\<clone>\python.exe`. Accept a clone only: `arcgispro-py3` is Esri's
    environment and stays untouched; offer to have the user clone it in ArcGIS Pro's Package Manager first.
- **Identify what the base Python really is** before using it:
  `"<base>" -c "import sys, importlib.util; print(sys.executable, importlib.util.find_spec('arcpy') is not None)"`.
  On an ArcGIS machine the clone is often first on PATH, so plain `python` may well be the clone. If
  `arcpy` is found, this is the ArcGIS path, whatever the user called it; confirm with them.
- **Python version**: read it from the base Python, never ask for it:
  `"<base>" -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"`. It must be 3.11
  or later; it becomes `requires-python` and, through it, ruff's target version.

Done when: the user has confirmed project name, package name and base Python path, you know whether
it is an ArcGIS clone (`arcpy` found), and you have the version printed by that interpreter.

## 3. Create the `.venv`

Skip creation if a `.venv` already exists and its version matches step 2; otherwise ask before
replacing it.

```text
"<base>" -m venv .venv                              # system Python
"<base>" -m venv --system-site-packages .venv       # ArcGIS Pro clone: arcpy stays importable
<venv-python> -m pip install --upgrade pip          # --group needs pip 25.1+; old pips also fail `audit`
```

For a clone, confirm `arcpy` is visible from the new environment:
`<venv-python> -c "import importlib.util; print(importlib.util.find_spec('arcpy') is not None)"`
prints `True`.

Done when: `<venv-python> -m pip --version` reports 25.1 or later (and, for a clone, the `arcpy` check
prints `True`).

## 4. Copy the template

Run the script from this skill's own folder (the folder holding this `SKILL.md`), with the new
`.venv`'s Python:

```text
<venv-python> "<skill-folder>/scripts/apply_template.py" <target> --project-name <name> --python-version <3.N> [--package-name <name>] [--arcgis] --dry-run
```

Add `--arcgis` on the ArcGIS path: it also copies `files-arcgis/`, a local `arcpy` stub that replaces
Esri's broken one for mypy (the reason is in the stub itself).

Read the dry-run list, then run it again without `--dry-run`. Each line is `created` or `exists`.

- **Fresh target**: every line should be `created`.
- **Any `exists` line**: the script left that file alone. Resolve each one with
  [`MERGING.md`](./MERGING.md) before going on.

Done when: the script has exited 0 and every `exists` file has been merged, kept or replaced as
`MERGING.md` directs, with the user's agreement wherever it asks for it.

## 5. Install

```text
<venv-python> -m pip install -e . --group dev
```

Done when: the install exits 0 and `<venv-python> -m poethepoet --help` lists the tasks `check`,
`format`, `lint`, `types`, `imports`, `test`, `crap`, `fix` and `audit`.

## 6. Verify

Run each check and fix whatever it reports before ticking it:

- [ ] `<venv-python> -m poethepoet check` exits 0. On a fresh target this proves the whole chain on the
  sample: formatting, lint, strict types, layer imports, 14 tests at 100 % coverage, CRAP gate.
  On an existing project, report the findings on the user's own code instead of fixing them
  unasked; that first wave is the expected starting point.
- [ ] `<venv-python> -m poethepoet audit` reports no known vulnerabilities. It needs network access:
  if it cannot reach its database, say so rather than reporting a pass. The project's own package is
  listed as "not found on PyPI and could not be audited"; that line is expected.
- [ ] `<venv-python> -m <package_name>` prints `Hello, World!` (fresh target).
- [ ] If the target is a git repository, `git status --short --ignored` lists `.vscode/` as untracked
  (committed on purpose) and `.venv/`, the tool caches and `lcov.info` as ignored.
- [ ] For an ArcGIS clone, the clone is unchanged: run `"<base>" -m pip freeze` before step 3 and again
  now; the two lists are identical.

Done when: every box is ticked, or the user has been told exactly which one failed and why.

## 7. Hand over

Tell the user, briefly:

- VS Code will offer the recommended extensions (`.vscode/extensions.json`); install them, and pick
  `.venv` if VS Code asks for an interpreter.
- `Ctrl+Shift+B` runs `check`; every task is listed in `TOOLSET.md`.
- The greeting sample exists to be replaced. Offer to remove it now (sample modules and their tests,
  keeping every folder and its `_what_goes_here.md`).

## Known gaps

- **ArcGIS Pro path run on Pro 3.7.2 (Python 3.13.13), fresh folder only.** `check` and `audit` pass and
  the clone is left unchanged. Two things remain outside the skill's control:
  - **arcpy licensing**: importing `arcpy` sometimes fails with `RuntimeError: The Product License has
    not been initialized` (seen both from the clone directly and under pytest). Tests that import
    `arcpy` will fail the same way until the licence initialises reliably; the sample never imports it.
  - **The `arcpy` stub** hides arcpy's real types. Remove `typings/arcpy` when a Pro release fixes
    `gp.pyi`. Side effect while it is there: mypy assumes `with arcpy.da.SearchCursor(...)` may swallow
    exceptions, so a `return` inside such a block needs a fallback `return` after it.
- **Merge paths not yet exercised.** Every run so far started from an empty folder; `MERGING.md` is
  untested against a real existing project.
- **Thresholds are starting values**: line length 120, complexity 10, coverage 80 %, CRAP 30. Adjust them
  once real code shows what fits.
- **crap4py is pinned at 0.1.1**: a young, single-maintainer tool. Check PyPI for a newer release
  before bumping the pin; the complexity and coverage limits are the backstop if it is abandoned.
- **`files/TOOLSET.md` is kept in sync by hand.** When a pin, threshold, task or file changes, update
  it in the same edit, or new projects will receive a description that no longer matches.
