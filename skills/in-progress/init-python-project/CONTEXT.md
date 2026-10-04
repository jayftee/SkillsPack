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

## Always a project `.venv`, even for ArcGIS

The commands live in poethepoet. Poe runs a task's tools from an environment only when it finds a
`./.venv` or `./venv` in the project; with any other interpreter it falls back to `PATH`. Observed:
launched from an environment outside the project, it ran a global ruff 0.15 instead of the project's
0.16 and could not find mypy at all.

The first design installed the dev tools straight into an ArcGIS Pro clone, which also meant
pip-installing a dozen packages into the environment `arcpy` depends on. The replacement creates `.venv` from the clone's `python.exe`
with `--system-site-packages`: `arcpy` and the clone's packages stay importable, the dev tools land in
`.venv` only, and the clone is never touched. Every project now has the same shape; the only choice is
the base interpreter. `pip-audit --local` keeps the clone's packages out of the vulnerability report.

First real run, ArcGIS Pro 3.7.2 (clone on Python 3.13.13), surfaced three things:

- **Every task is `python -m <tool>`.** pip skipped installing pytest into `.venv` because the clone
  already had 9.1.1, so `.venv\Scripts` had no `pytest.exe` and poe ran some other pytest from PATH,
  one without pytest-cov. Poe resolves `python` to the `.venv`'s interpreter, which then finds each tool
  in `.venv` or in the clone. import-linter is the exception: `python -m importlinter.cli` prints nothing
  and exits 0 (no `__main__` guard), a silent pass, so `imports` is a poe `script` task calling
  `importlinter.cli:lint_imports_command`; it was checked to fail on a real violation.
- **Esri's arcpy stubs are broken** (`arcpy/typing/gp.pyi`, an overload with no body). mypy stops at
  the first syntax error in any stub it reads, and neither `follow_imports = "skip"` nor `"silent"`,
  per module or global, stops it reading that file. A local stub in `typings/` (on `mypy_path`, ahead
  of installed packages) does. It ships in `files-arcgis/`, copied only with `--arcgis`.
- **arcpy licensing is intermittent**: `import arcpy` alternated between working and
  `The Product License has not been initialized`, directly from the clone, so it is not caused by the
  `.venv`. The clone also ships with a conflict of its own (`lifelines` wants `pandas<3`, the clone has
  3.0.3) that `pip check` reports in `.venv` too.

## pip + venv, dependency groups

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
| lockfile (pip-tools, `pip lock`) | Undecided; pip + venv has no lockfile of its own |
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
