# init-python-project — background

Internal to the `SkillsPack` repo: it sits beside `SKILL.md`, outside `files/`, so it never reaches a
target project. It records why the payload is the way it is. Read it before changing a decision; most
of them were made against an alternative that looked simpler.

## Lineage

This replaces an earlier, never-committed draft (ruff.toml + mypy + Pyright + requirements.txt +
pre-commit) and three throwaway attempts outside this repo. The draft's ruff rule selection, mypy
strictness and project/package name split carried over; its file layout did not. Its bugs that were
fixed on the way: `fix = true` (a check that edits files), `preview = true`, COM812 conflicting with the
formatter, no test-file ignores, coverage `source = ["."]` without branch coverage, `.gitignore`
ignoring `.vscode/`, and a hard-coded Python 3.13.

## One configuration file

Every tool reads its own dedicated file *before* `pyproject.toml` and then ignores its
`pyproject.toml` section without warning. A mix of both was the original source of "I can never tell
where my configuration lives". So all tool settings go in `pyproject.toml`, and both the script and
step 1 refuse to proceed while a dedicated file exists. `.editorconfig`, `.gitignore`, `.gitattributes`
and `.vscode/` stay separate because they are not Python tools.

Python has no `Directory.Build.props` equivalent: `pyproject.toml` is both the project's identity and
the tool hub. That is why this skill, unlike the C# one, has to merge into the project file
(`MERGING.md`) and substitute names into it.

## No project `.venv`: one dedicated environment per role

The skill installs into an environment the user names and creates none. Esri clones already are the unit
of isolation: a clone for development (the tools, the project installed with `-e`), a clean clone for
runtime testing (only the wheel), and the server's own. A `.venv` layered over a clone with
`--system-site-packages` was a second isolation mechanism on top of that one, with its own checks
(`pip freeze` unchanged, tools found in the wrong place).

This replaces the first two designs. The first installed the dev tools straight into a clone that was
also used to run `arcpy` code. The second put a `.venv` over the clone because that polluted the
environment `arcpy` depends on. Dedicated clones remove that reason; the clone is expected to change.

The `.venv` had a second job that the new design still has to cover. Poe runs a task's tools from an
environment only when it finds a `./.venv` or `./venv` in the project; otherwise it resolves `python`
through `PATH`. Observed on the user's machine with the first design: it ran a global ruff 0.15 instead
of the project's 0.16 and could not find mypy at all. Re-tested with a stand-in environment outside the
project, no `.venv`, and poe launched by that environment's own python:

- System Python first on `PATH`: `poe types` failed with `No module named mypy`; `poe test` could not use
  pytest-cov. Launching poe from the right interpreter does **not** select the environment.
- The environment's `Scripts` folder first on `PATH` (what activating does): `poe check` passed.
- Poe's `executor = { type = "simple" }` changed nothing. `executor = { type = "virtualenv", location = ... }`
  worked, but needs a machine-specific path in a committed file.

So the rule is that the development environment's `python` is first on `PATH` for every poe task, and step 2
of `SKILL.md` verifies it before anything runs. A silent wrong-tool run is the failure it prevents.

The development environment holds the tools and any other project installed in it, so it can hide an
undeclared dependency. `poe smoke` therefore installs the wheel into a clean environment (a throwaway
venv, or a clean clone with `--python`) and runs the commands from an unrelated folder.

First real run, ArcGIS Pro 3.7.2 (clone on Python 3.13.13, under the earlier `.venv` design), surfaced three things:

- **Every task is `python -m <tool>`.** pip skipped installing pytest into the `.venv` because the clone
  already had 9.1.1, so `.venv\Scripts` had no `pytest.exe` and poe ran some other pytest from PATH,
  one without pytest-cov. A bare tool name is looked up on `PATH` and may be another environment's;
  `python -m <tool>` finds it in whichever environment `python` is. That still holds. import-linter is the
  exception: `python -m importlinter.cli` prints nothing and exits 0 (no `__main__` guard), a silent
  pass, so `imports` is a poe `script` task calling `importlinter.cli:lint_imports_command`; it was
  checked to fail on a real violation.
- **Esri's arcpy stubs are broken** (`arcpy/typing/gp.pyi`, an overload with no body). mypy stops at
  the first syntax error in any stub it reads, and neither `follow_imports = "skip"` nor `"silent"`,
  per module or global, stops it reading that file. A local stub in `typings/` (on `mypy_path`, ahead
  of installed packages) does. It ships in `files-arcgis/`, copied only with `--arcgis`.
- **arcpy licensing is intermittent**: `import arcpy` alternated between working and
  `The Product License has not been initialized`, directly from the clone, so it is not caused by the
  `.venv`. The clone also ships with a conflict of its own (`lifelines` wants `pandas<3`, the clone has
  3.0.3) that `pip check` reports in `.venv` too.

First run straight into a clone (Pro 3.7.2, Python 3.13.13, new design) worked end to end, with two effects:

- **VS Code's Ruff extension locks `Scriptsuff.exe`.** It runs the exe as a language server, Windows will
  not let pip replace a running exe, and VS Code respawns the process if it is killed. pip had already
  removed ruff's files when it failed, so the clone was left half-upgraded (`~uff` folders in
  `site-packages`). Step 5 of `SKILL.md` now tells the user to quit VS Code or disable the extension first.
- **pip replaces conda-built packages**: pytest 8.4.2 and rich 13.9.4 became PyPI builds. Accepted: the
  clone is dedicated to development and the skill reports the change from `pip freeze`.

## pip, dependency groups

The user's choice over uv. Dev tools sit in `[dependency-groups] dev` (PEP 735, `pip install --group`,
pip 25.1+), not in an extra, so installing the project never pulls them in and they are not published
as an installable option. `requirements.txt` is gone: runtime dependencies belong in
`[project].dependencies`, one list.

## poethepoet + VS Code tasks

The user always works in VS Code and asked whether `tasks.json` alone would do. It would not:
Claude Code, a terminal and CI cannot run VS Code tasks, so the six commands would be written twice and
drift. Poe holds them once in `pyproject.toml`; `tasks.json` only calls
`${command:python.interpreterPath} -m poethepoet <task>` and adds problem matchers for ruff
(`output-format = "concise"`) and mypy (`show_column_numbers`).

`[tool.poe] env = { PYTHONUTF8 = "1" }` is not decoration: import-linter crashed with
`UnicodeEncodeError` on Windows whenever its output was redirected and Python fell back to cp1252.

## mypy only

The earlier draft kept Pyright (editor) and mypy (gate) side by side. Two checkers disagree, which means
code that is clean in the editor and red in `check`, or the reverse. mypy is the gate and also drives the
editor through the Mypy Type Checker extension; Pylance stays for completion with
`typeCheckingMode: off`. `python_version` and ruff's `target-version` are left unset on purpose: mypy
uses the interpreter it runs in and ruff reads `requires-python`, so the only version in the file is the
one the script fills in.

## CRAP: crap4py plus backstops

crap4py is the only Python tool that computes CRAP (`CC² × (1 − coverage)³ + CC`), the counterpart of
Crap4DotNet. It has one release and one maintainer, so it is pinned (`==0.1.1`), and two mainstream
limits back it up: ruff's `C901` (complexity 10) and coverage `fail_under = 80`. If crap4py dies, those
still hold most of the line; being MIT-licensed and small, it can also be vendored. It reads branch
coverage from LCOV, hence `branch = true` and `--cov-report=lcov:lcov.info`.

## Layers and import-linter

The user chose to scaffold all eight layer folders, each with a `_what_goes_here.md`; `utils/` has the
strictest rules because it is where code rots. import-linter turns the documented rules into a failing
check: one `layers` contract, services at the top, `repositories | clients` as independent siblings,
`utils` at the bottom so it can import nothing from the package. Deleting a layer folder means editing
the contract, which `TOOLSET.md` says.

## The sample

A sample is shipped only because it comes with the full toolchain: it must install, pass `check`
(14 tests, 100 % coverage, every CRAP score at 2 or below) and run as `python -m <package>`. It touches
`config`, `enums`, `models`, `exceptions`, `utils` and `services`; `repositories` and `clients` have no
sample because a hello-world has no data to store and no one to call.

## `files/` and tokens

Everything copyable lives in `files/`, never inline in `SKILL.md`, as in the C# skill. Because the
package name appears in folder names and imports, the files carry `{{TOKENS}}` (including the folder
`src/{{PACKAGE_NAME}}/`), and `scripts/apply_template.py` copies and substitutes them. Files needed only
on the ArcGIS path live in a second tree, `files-arcgis/`, laid over `files/` with `--arcgis`. The script fails
on any token it does not know, never overwrites, and validates names (lowercase hyphenated project
name, identifier package name that is not a keyword, Python 3.11+, the floor set by `StrEnum` in the
sample).

## Considered and left out

| Tool | Why not (yet) |
|---|---|
| Pyright | Second type checker; see "mypy only" |
| bandit | Ruff's `S` rules are the same checks |
| debugpy | Bundled with VS Code's Python Debugger extension |
| pre-commit | Undecided; would bend the one-file rule with `.pre-commit-config.yaml` |
| lockfile (pip-tools, `pip lock`) | Undecided; pip has no lockfile of its own |
| vulture | Dead-code detection; most valuable for the legacy-script work, so deferred to it |
| mutmut | Mutation testing; slow, for occasional runs later |
| CI | Depends on where the code is hosted |

## Open items

- Pre-commit and a lockfile: decide before the first real project.
- A Python counterpart to CleanCoders.Analyzers: a standalone tool built on the standard library's
  `ast` (rule codes `CCxxxx`, settings in `[tool.cleancoders]`, run as a poe task). Syntax-level rules
  such as method length, argument count and collection naming fit `ast`; type-dependent ones would need
  more.
- The multi-job layout for the ~100 legacy scripts is a separate piece of work and will reuse this
  baseline.

## Packaging and deployment

- **The deliverable is a wheel**, installed with `pip` into the Python whose `Scripts` folder is on the
  user's `PATH`. The deployment targets are management scripts run from the command line, with Python
  already installed; the commands come from `[project.scripts]`. No pipx: it isolates each tool in its
  own environment and puts launchers outside the existing `PATH`, and an isolated environment has no
  `arcpy`. A zipapp or PyInstaller is for machines without Python, which is not the case here.
- **`package` runs `check` first**, then cleans `dist/` and `build/` (setuptools keeps stale modules in
  `build/`) and builds only a wheel. The build needs network access for `setuptools`.
- **`smoke` is a script, not a shell one-liner.** Making a venv, finding its launcher folder and running
  from a temporary folder is awkward on Windows in one line. Poe passes extra arguments through to it
  (`poe smoke --python ...`). It runs the launchers, not `python -m`, because the launcher is what the
  recipient types. It uninstalls afterwards so a reused runtime-test clone stays clean.
- **Bundled data lives inside the package** and is read with `importlib.resources`. Found with a sample
  that read `data/potatoes.json` relative to the working directory: it ran from the project folder and
  failed from anywhere else, and the file was not in the wheel.
- **A shared Python is shared.** Every wheel installed into the same Python shares its packages and its
  command names. Hence the rules to keep runtime dependencies few and loose, and command names distinct.
