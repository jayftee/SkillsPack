# Merging into an existing project

Reached from step 4 of `SKILL.md` for every file the script reported as `exists`. The script never
overwrites, so each of those files still holds the project's own version. Resolve them one at a time;
the template's version is in `files/` (with `{{TOKENS}}` still in it: substitute the values agreed in
step 2 when copying anything across).

## `pyproject.toml`: merge, never replace

The project's identity stays the project's: keep `[build-system]`, `[project]` (name, version,
`dependencies`, `requires-python`, authors, scripts) exactly as they are, unless the user asks
otherwise. Add what the template has and the file lacks:

| Table | How to merge |
|---|---|
| `[dependency-groups] dev` | Add each missing tool. Keep any tool already listed at the project's own version. If the project lists dev tools under `[project.optional-dependencies] dev` instead, ask whether to move them into the group. |
| `[tool.poe]`, `[tool.poe.tasks]` | Add missing tasks. If a task name already exists with a different command, show both and ask. |
| `[tool.ruff*]`, `[tool.mypy]`, `[tool.pytest.ini_options]`, `[tool.coverage.*]` | Add missing tables whole. For a table that exists, add missing keys and keep the project's values where both define one; list every conflict to the user. |
| `[tool.importlinter]` | Add only if the project uses the template's layer folders. Otherwise ask: the contract would fail on a different layout. |
| `[tool.setuptools.*]` | Keep the project's packaging configuration; add `package-data` for `py.typed` only if it has no conflicting entry. |

After merging, `tomllib` must parse the file: `<venv-python> -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"`.

## `.gitignore`: append

Append each line from the template that the file lacks, under a `# from init-python-project` header.
If the existing file ignores `.vscode/` wholesale, replace that line with the template's `.vscode/*`
plus its three `!.vscode/...` exceptions, and tell the user.

## `.vscode/settings.json`, `.vscode/tasks.json`, `.vscode/extensions.json`: merge keys

- `settings.json`: add missing keys. Where the project already sets a key the template also sets
  (formatter, type checking mode, interpreter path), show both values and ask.
- `tasks.json`: add the template's tasks whose `label` is not already used; for a clashing label, ask.
  Only one task can be the default build task.
- `extensions.json`: add missing recommendations.

## `.editorconfig`, `.gitattributes`, `TOOLSET.md`: diff and ask

Show the difference and ask whether to keep the project's file, take the template's, or merge by hand.
An existing `TOOLSET.md` usually means this skill ran here before: if it only describes the same
payload, refresh it; if it has gathered project-specific notes, merge instead.

## Source and test files

A file under `src/` or `tests/` that already exists belongs to the project: keep it. If the project
has its own package under another name, ask whether to add the sample at all; the layer folders and
their `_what_goes_here.md` files can be added without the sample code.

## Runtime dependencies in `requirements.txt`

If the project keeps runtime dependencies in `requirements.txt`, offer to move them into
`[project].dependencies`, so that `pyproject.toml` stays the single list. Do it only with the user's
agreement; some deployment scripts read `requirements.txt` directly.
