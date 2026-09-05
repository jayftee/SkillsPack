# init-csharp-project — background

This file is internal to the `SkillsPack` repo — it lives next to `SKILL.md`, outside `files/`, so it
never travels to a target project. (The equivalent doc that *does* travel with a project is
`files/TOOLSET.md` — see below.) Read this when a step in `SKILL.md` doesn't make sense on its own, or
before re-litigating a decision below — most of them were deliberate, not accidental.

## Why this exists

The static-analysis baseline this skill applies — StyleCop rules, a custom Roslyn analyzer ported from
*Clean Code* (Robert C. Martin), and the `.editorconfig`/`Directory.Build.props` wiring that makes them
agree with each other instead of fighting — originated in the `CleanCoder` repo (the
`CleanCodersStyleCopRules` / `CleanCoders.Analyzers` project). None of it is specific to that repo's own
subject matter (analyzer-writing); it's meant to be the baseline for any future .NET/C# project. This
skill is where that reusable subset lives so it can be applied to a new project without hand-copying
files or re-explaining the setup to an agent from scratch each time.

## The quadruplet of analyzers

Four analysis layers, meant to work together without contradicting each other:

1. **OOB (out-of-box) Roslyn / `NetAnalyzers` `CA` rules** — built into the .NET SDK, no package
   reference needed. Tuned via `.editorconfig` (e.g. `CA2214` explicitly turned on because it ships
   disabled by default despite being genuine Framework Design Guidelines advice; `CA1416`/`CA1515`
   suppressed at bootstrap because they need a platform/API-surface decision a brand-new project hasn't
   made yet).
2. **[`Microsoft.VisualStudio.Threading.Analyzers`](https://www.nuget.org/packages/Microsoft.VisualStudio.Threading.Analyzers)**
   — `VSTHRDxxx` rules (e.g. `VSTHRD200` "use `Async` naming convention"). Wired into
   `files/Directory.Build.props`. Resolves from nuget.org normally, no local feed needed.
3. **`StyleCop.Analyzers`** + `stylecop.json` (its settings) + `.editorconfig` (severity overrides
   where StyleCop's defaults fight modern C# conventions).
4. **`CleanCoders.Analyzers`** — the custom *Clean Code*-derived Roslyn analyzer, packaged as a NuGet
   package (not published to nuget.org — see below) + `cleancoders.json` (its rule parameters, e.g. max
   method line count) + `.editorconfig` (per-rule on/off + severity, e.g.
   `dotnet_diagnostic.CC0042.severity = warning`).

## Design decisions worth knowing before you change something

- **Delivered via this Claude Code skill (`../SKILL.md` + `../files/`), applied directly — not a
  `dotnet new` item template.** A `dotnet new` item template (something installed once per machine,
  then run inside an already-scaffolded project to layer files in) was the original plan and is
  deliberately not being pursued — the skill gets the same result without a packaging/publishing step.
  Don't re-propose the item-template path without a concrete reason the skill approach falls short.
- **No `.csproj` collision because the wiring lives in `Directory.Build.props`, not the `.csproj`
  itself.** MSBuild auto-imports the nearest `Directory.Build.props` walking up the directory tree from
  any `.csproj` beneath it — no explicit `<Import>` needed. So this skill only ever adds net-new files
  (`.editorconfig`, `Directory.Build.props`, `stylecop.json`, `cleancoders.json`, etc.) and never has to
  touch or merge whatever `dotnet new webapi`/`console`/`classlib` generates. This is also what makes
  the config-first ordering in `../SKILL.md` step 1 possible — the import happens at build time by
  directory position, not at file-creation time, so it doesn't matter whether the payload predates the
  `.csproj` it will eventually apply to.
- **`CleanCoders.Analyzers` is distributed from a local filesystem NuGet feed (`C:\_LocalNuGet`), not
  nuget.org** — it isn't ready to be published publicly. A local folder registered as a NuGet source
  works identically to a real feed through the same source-resolution pipeline (`nuget.config`), just
  private. `Microsoft.VisualStudio.Threading.Analyzers` and `StyleCop.Analyzers` need no such
  accommodation; they resolve from nuget.org as normal.
- **The issue-tracker workflow (`.scratch/<feature>/issues/*.md`, spec-to-tickets) is explicitly out of
  scope for this skill.** That's handled by separate Matt Pocock skills (`wayfinder`,
  `grill-with-docs`) — already-solved, already-portable, and orthogonal to what this skill sets up.
  Don't bundle an issue-tracker convention in here.

## Schema handling for `cleancoders.json`

`cleancoders.json` ships with **no `$schema` key** — deliberately, not an oversight. Validation happens
at build time instead: `CleanCoders.Analyzers` (0.2.1+) embeds its schema as a resource inside its own
DLL and reports three diagnostics — `CCCFG001` (value below schema minimum), `CCCFG002` (unrecognized
property), `CCCFG003` (invalid JSON) — without needing a second, hand-copied schema file that could
silently drift from the real one.

**Still open**: the schema an IDE would want for *authoring* `cleancoders.json` (autocomplete while
hand-editing it) should come from the same package rather than a hand-copied duplicate — e.g. a NuGet
content file restored alongside the `PackageReference`. That packaging mechanism doesn't exist yet.
Until it does, hand-editing `cleancoders.json` has no editor autocomplete — a known, accepted trade-off.
**Do not re-add a loose `cleancoders.schema.json` file to `files/` as a quick fix** for this — that
reintroduces the exact duplicate-copy drift risk the embedded-schema approach was built to eliminate.

If `files/Directory.Build.props`'s `CleanCoders.Analyzers` pin is ever lowered, keep it at `0.2.1` or
later — earlier versions predate this validation entirely.

## `Crap4DotNet` — a fifth thing, deliberately outside the quadruplet

[`Crap4DotNet`](https://www.nuget.org/packages/Crap4DotNet) (MIT,
https://github.com/7Factor/crap4dotnet) computes CRAP scores —
`complexity(m)² × (1 − coverage(m))³ + complexity(m)` — to surface methods that are both complex and
poorly covered. It does **not** belong to the quadruplet above and isn't wired into
`Directory.Build.props`:

- It's a **`dotnet tool`**, not a Roslyn analyzer — it plays no part in `dotnet build`. It's invoked on
  demand, against a coverage file (typically `coverlet`-generated Cobertura XML) or via `--run-tests` to
  generate one itself.
- It has **no project-level config file** — no `crap4dotnet.json` analog to `cleancoders.json`.
  Threshold (default 30), coverage path, and output path are all CLI flags, re-specified on every
  invocation. If a fixed threshold ever needs to be checked into a project, that has to live in a
  wrapper script or documented command — the tool itself won't remember it.
- `../SKILL.md` step 4 installs it as a **local** tool (`dotnet new tool-manifest -o .config` +
  `dotnet tool install --local`, creating/updating `.config/dotnet-tools.json`), not global — same
  rationale as pinning `CleanCoders.Analyzers`'s version in `Directory.Build.props`: reproducible
  per-project via `dotnet tool restore`, no reliance on whatever happens to be installed machine-wide.
  The `-o .config` is load-bearing, not stylistic: confirmed on SDK `10.0.400` that the bare
  `dotnet new tool-manifest` creates `./dotnet-tools.json` at the invocation root instead of the
  conventional `.config/dotnet-tools.json` — don't drop the explicit output path as a "simplification."
- Invoke the installed tool as `dotnet dotnet-crap ...`, not `dotnet tool run dotnet-crap ...` —
  confirmed the latter has `dotnet tool run` itself swallow a trailing `--help` and print its own
  generic help instead of forwarding it to the tool. `dotnet dotnet-crap` is what the tool's own
  install message recommends and the form confirmed to work.

## `TOOLSET.md` — the skill's own in-project documentation

`../files/TOOLSET.md` is deployed into every target project alongside the rest of the payload (step 2
of `../SKILL.md`, same as `.editorconfig`/`stylecop.json`/`cleancoders.json`). It exists because neither
this file nor `../SKILL.md` travels with the target project — only `files/` does — so without it, a
project opened later has the *files* but not the *why*. `README.md` was deliberately not used for this,
to avoid colliding with whatever `dotnet new` or the project itself puts there.

It documents, per file: what it is, what it depends on / is depended on by, and the same known gaps
called out in `../SKILL.md` — kept in sync manually; there's no automated check that they agree. If
`../SKILL.md` or `../files/*` changes in a way that changes what's true for a newly-initialized project,
`../files/TOOLSET.md` needs the same edit, or newly-deployed copies start silently misdescribing
themselves.

## Open items

- Whether to register `C:\_LocalNuGet` as a **machine-wide** NuGet source, instead of the per-project
  `nuget.config` `../SKILL.md` step 3 adds today. Not decided either way; both work.
- The `cleancoders.json` editor-authoring schema delivery mechanism (see "Schema handling" above).
- This skill's own known gaps (the scaffolded/build-verify path, the diff-and-ask merge branches,
  untuned `VSTHRD` severities, etc. — the config-first path and the `Crap4DotNet` install sequence are
  now confirmed working, see below) live in `../SKILL.md`'s "Known gaps" section, not duplicated here —
  check there for the current list.

## Re-syncing with the source repo

If `CleanCoder`'s own `.editorconfig`/`Directory.Build.props`/`stylecop.json`/`cleancoders.json` have
moved on since this skill's payload was last refreshed, diff `../files/*` against `CleanCoder`'s root
copies directly before assuming this payload is still current.
