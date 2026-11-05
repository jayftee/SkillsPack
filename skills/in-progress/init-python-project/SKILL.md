---
name: init-python-project
description: Set up this repo's baseline Python tooling in a project folder — ruff, mypy, pytest with coverage, import-linter, crap4py and pip-audit, all configured in one pyproject.toml and run through poethepoet and VS Code tasks, a layered src/ package with a working sample, and a wheel build plus deployment smoke test — installed into a development environment the user names (typically an ArcGIS Pro clone). Use when starting a new Python project, or when asked to add the standard Python tooling to an existing one.
---

# Initialize a Python Project

Everything that can be copied as-is lives in [`files/`](./files/), plus [`files-arcgis/`](./files-arcgis/) for the
ArcGIS Pro path. [`scripts/apply_template.py`](./scripts/apply_template.py) copies those trees into the target, fills in the `{{TOKENS}}` and never overwrites. What the payload
contains and how to use it is in [`files/TOOLSET.md`](./files/TOOLSET.md), which travels with every project.
Why each choice was made is in [`CONTEXT.md`](./CONTEXT.md): read it before changing a decision.

The skill creates no environment. It installs into a **dedicated development environment** that the user
names: an ArcGIS Pro clone made for development, or any environment they created (`venv`, conda). Esri
clones are the normal unit of isolation, so a clone for development, a clean one for runtime testing and
the server's own are three separate environments.

In the commands below, `<python>` is the `python.exe` of that environment. Your own shell must have that
environment's folder and its `Scripts` folder **first on `PATH`** for every `python -m poethepoet` command:
poe finds `python` through `PATH`, not through the interpreter that launched it (see `CONTEXT.md`).

## 1. Inspect the target

The target is the current working directory unless the user named another folder. Record:

- **Stray config files**: any of `ruff.toml`, `.ruff.toml`, `mypy.ini`, `.mypy.ini`, `pytest.ini`,
  `.pytest.ini`, `.coveragerc`, `setup.cfg`, `tox.ini`, `.importlinter`, `pyrightconfig.json`.
  Each silently overrides its section of `pyproject.toml`. If any exist, stop here: show them to the
  user and agree on moving their settings into `pyproject.toml` (or deleting them) before going on.
  The script refuses to run while one exists.
- **Fresh or existing**: an existing project has a `pyproject.toml`, a `src/` package or other Python
  code. An existing project takes the merge path in step 4.
- **A project `.venv` from an earlier run of this skill**: it is no longer used. Tell the user; remove it
  only if they agree.

Done when: no stray config file remains, and you know which path (fresh or existing) applies.

## 2. Agree on names and the environment

Ask the user, then show the final values back before continuing:

- **Project name**: lowercase words joined by hyphens (`parcel-sync`). The **package name** is derived
  by replacing `-` with `_` (`parcel_sync`); the user may override it.
- **Development environment**: the path to its `python.exe`. For ArcGIS Pro, a clone made for development
  (`<Pro>\bin\Python\envs\<clone>\python.exe`, or `%LOCALAPPDATA%\ESRI\conda\envs\<clone>\python.exe`);
  if none exists, ask the user to clone one in ArcGIS Pro's Package Manager first. This step installs
  packages into it, so confirm it is dedicated to development: not the server's, not one that
  other tools depend on. If they want a plain-Python environment, they create it first (a `venv` in the
  project is fine) and give you its `python.exe`.
- **Identify what it really is**:
  `"<python>" -c "import sys, importlib.util; print(sys.executable, importlib.util.find_spec('arcpy') is not None)"`.
  If `arcpy` is found, this is the ArcGIS path; confirm with the user.
- **Python version**: read it from that interpreter, never ask for it:
  `"<python>" -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"`. It must be 3.11
  or later; it becomes `requires-python` and, through it, ruff's target version.
- **PATH**: put the environment's folder and its `Scripts` folder first on your shell's `PATH`, then
  `python -c "import sys; print(sys.executable)"` must print `<python>`. If it does not, the poe tasks
  below would run another environment's tools. Tell the user to do the same in their own terminals
  (activate the environment).

Done when: the user has confirmed project name, package name and environment, you know whether it is an
ArcGIS clone (`arcpy` found), you have the version, and `python` on your `PATH` is `<python>`.

## 3. Prepare the environment

Run `python -m pip --version`. `--group` needs pip 25.1 or later; if it is older, run
`python -m pip install --upgrade pip` (a development environment, so this is expected; tell the user).
Record `python -m pip freeze > <scratch>/before.txt` so step 5 can report what changed.

For an ArcGIS clone, `python -c "import importlib.util; print(importlib.util.find_spec('arcpy') is not None)"`
prints `True`.

Done when: pip is 25.1 or later and, for a clone, the `arcpy` check prints `True`.

## 4. Copy the template

Run the script from this skill's own folder (the folder holding this `SKILL.md`):

```text
python "<skill-folder>/scripts/apply_template.py" <target> --project-name <name> --python-version <3.N> [--package-name <name>] [--arcgis] --dry-run
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
python -m pip install -e . --group dev
```

**Before installing into a clone that already has `ruff`, tell the user to quit VS Code or disable its Ruff
extension for the workspace.** The extension runs `Scriptsuff.exe` as a language server, Windows will not
let pip replace a running exe, and killing the process is pointless because VS Code respawns it. The install
fails with `WinError 5` after pip has already removed ruff's files, leaving the clone half-upgraded
(`~uff` folders in `site-packages`, `Ignoring invalid distribution ~uff` on every pip call). Recovery: close
the server, `python -m pip uninstall ruff -y`, delete the `~uff*` folders, run the install again.

Then `python -m pip freeze` again and compare with `before.txt`. Tell the user which packages pip
upgraded or replaced rather than only added: it changed their environment.

Done when: the install exits 0 and `python -m poethepoet --help` lists the tasks `check`, `format`,
`lint`, `types`, `imports`, `test`, `crap`, `fix`, `audit`, `package` and `smoke`.

## 6. Verify

Run each check and fix whatever it reports before ticking it:

- [ ] `python -m poethepoet check` exits 0. On a fresh target this proves the whole chain on the
  sample: formatting, lint, strict types, layer imports, 14 tests at 100 % coverage, CRAP gate.
  On an existing project, report the findings on the user's own code instead of fixing them
  unasked; that first wave is the expected starting point.
- [ ] `python -m poethepoet audit` reports no known vulnerabilities in the packages that **this skill**
  installed. It scans the whole environment, so on an ArcGIS clone it may also list Esri's own packages:
  report those to the user, do not fix them. It needs network access: if it cannot reach its database,
  say so rather than reporting a pass. The project's own package is listed as "not found on PyPI and
  could not be audited"; that line is expected.
- [ ] `python -m <package_name>` prints `Hello, World!` (fresh target).
- [ ] `python -m poethepoet package` exits 0 and `dist/` holds exactly one wheel (needs network: the build
  backend is downloaded).
- [ ] `python -m poethepoet smoke` exits 0 and prints `smoke test passed`. If the user has a clean
  runtime-test environment, also run `smoke --python "<its python.exe>"`; a project that imports `arcpy`
  needs this form.
- [ ] If the target is a git repository, `git status --short --ignored` lists `.vscode/` and `scripts/`
  as untracked (committed on purpose) and the tool caches, `dist/`, `build/` and `lcov.info` as ignored.

Done when: every box is ticked, or the user has been told exactly which one failed and why.

## 7. Hand over

Tell the user, briefly:

- VS Code will offer the recommended extensions (`.vscode/extensions.json`); install them, and pick the
  development environment with *Python: Select Interpreter*.
- `Ctrl+Shift+B` runs `check`; every task is listed in `TOOLSET.md`. The terminal running the tasks must
  have the development environment first on `PATH`.
- To deploy: `package`, `smoke`, then `pip install <wheel>` on the target; the steps and the rules for
  data files, dependencies and versions are in `TOOLSET.md` under *Package and deploy*.
- The greeting sample exists to be replaced. Offer to remove it now (sample modules and their tests,
  keeping every folder and its `_what_goes_here.md`).

## Known gaps

- **The ArcGIS Pro path** has run end to end on Pro 3.7.2 (Python 3.13.13): `apply_template --arcgis`, the
  install straight into a clone, `check`, `audit`, `python -m <package>`, `package`, `smoke` and the git-ignore
  check, on a fresh folder. `smoke --python <clean clone>` has not been run, and the install changes the clone:
  pip replaced the conda-built `pytest` 8.4.2 and `rich` 13.9.4 with PyPI builds (pytest 9.1.1, rich 15.0.0).
  Two things remain outside the skill's control:
  - **arcpy licensing**: importing `arcpy` sometimes fails with `RuntimeError: The Product License has
    not been initialized` (seen both from the clone directly and under pytest). Tests that import
    `arcpy` will fail the same way until the licence initialises reliably; the sample never imports it.
  - **The `arcpy` stub** hides arcpy's real types. Remove `typings/arcpy` when a Pro release fixes
    `gp.pyi`. Side effect while it is there: mypy assumes `with arcpy.da.SearchCursor(...)` may swallow
    exceptions, so a `return` inside such a block needs a fallback `return` after it.
- **Deployment has been run with a venv made from the Pro clone's own Python** (no standalone Python is
  needed). That covers the wheel, the launchers and the data-file rules, but not a sample that imports `arcpy`.
- **`scripts/smoke.py` has no unit tests**; it is checked by running `smoke`.
- **Merge paths not yet exercised.** Every run so far started from an empty folder; `MERGING.md` is
  untested against a real existing project.
- **Thresholds are starting values**: line length 120, complexity 10, coverage 80 %, CRAP 30. Adjust them
  once real code shows what fits.
- **crap4py is pinned at 0.1.1**: a young, single-maintainer tool. Check PyPI for a newer release
  before bumping the pin; the complexity and coverage limits are the backstop if it is abandoned.
- **`files/TOOLSET.md` is kept in sync by hand.** When a pin, threshold, task or file changes, update
  it in the same edit, or new projects will receive a description that no longer matches.
