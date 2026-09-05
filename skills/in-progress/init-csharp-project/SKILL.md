---
name: init-csharp-project
description: Apply this repo's baseline C# setup to a .NET project — the "quadruplet" of static analyzers (OOB Roslyn/NetAnalyzers, Microsoft.VisualStudio.Threading.Analyzers, StyleCop, CleanCoders.Analyzers) plus a docs/src/tests folder skeleton. Use when starting a new C# project, or when asked to add/apply the standard C# lint/analyzer setup to an existing one.
---

# Initialize a C# Project

## What This Sets Up

The quadruplet of analyzers, all wired centrally in `Directory.Build.props` so every project under it gets all four regardless of how the repo's own folder structure evolves:

1. **OOB Roslyn/`NetAnalyzers` (`CA` rules)** — built into the SDK; `EnableNETAnalyzers`/`AnalysisLevel`/`AnalysisMode` turned up to maximal (`AllEnabledByDefault`) rather than the SDK's narrow default subset. Deliberately noisy at first — see `CONTEXT.md` for the plan to tone it down per-rule as real projects surface false positives.
2. **`Microsoft.VisualStudio.Threading.Analyzers`** — async/threading naming and correctness (`VSTHRDxxx`, e.g. `VSTHRD200` "use `Async` naming convention").
3. **`StyleCop.Analyzers`** + `stylecop.json`.
4. **`CleanCoders.Analyzers`** + `cleancoders.json` — custom Clean-Code-derived rules, resolved from a local NuGet feed (not nuget.org).

Plus the files/folders that make it all apply automatically:

- **`.editorconfig`** — formatting/naming/diagnostic-severity rules for `CA`, `SA`, and `CC` diagnostics. **Not yet tuned for `VSTHRD`** (`Microsoft.VisualStudio.Threading.Analyzers`) — it ships with zero `dotnet_diagnostic.VSTHRD*.severity` overrides, so those rules will surface at whatever severity the analyzer defaults to until a real project run shows which ones are worth adjusting.
- **`Directory.Build.props`** — the properties above, plus `Nullable`, `ImplicitUsings`, `EnforceCodeStyleInBuild`, `GenerateDocumentationFile`, bootstrap `NoWarn`s, and all four analyzers' `PackageReference`/`AdditionalFiles` wiring.
- **`stylecop.json`**, **`cleancoders.json`** — the two analyzers' own settings files.
- **`.gitignore`** — standard .NET ignores (`bin/`, `obj/`, `.vs/`, `.idea/`, user/secret files, test results, NuGet packages).
- A local-feed **`nuget.config`** entry, if the target can't already resolve `CleanCoders.Analyzers` from `C:\_LocalNuGet`.
- A **`docs/`, `src/`, `tests/`** folder skeleton at the target root, if not already present.

This assumes `dotnet new webapi`/`console`/`classlib`/etc. (or an existing project) has already scaffolded the actual `.csproj` — this skill only adds files *around* it, never touches the `.csproj` itself.

Background on *why* these specific files/rules exist lives in [`CONTEXT.md`](./CONTEXT.md) next to this file — read it if a step below doesn't make sense, don't duplicate it here.

## Steps

### 1. Confirm the target and detect what's already there

Confirm the target directory (default: current working directory) actually has a `.sln` or at least one `.csproj` somewhere under it — if not, stop and tell the user to scaffold the project first (`dotnet new ...`).

Then check, at the target root, for an existing:

- `.editorconfig`
- `Directory.Build.props`
- `stylecop.json`
- `cleancoders.json`
- `.gitignore`
- `nuget.config`

Each of these is a single file per directory — this skill cannot layer a second copy alongside an existing one the way `Directory.Build.props` layers *up* a directory tree. Anywhere a file already exists, do not overwrite blindly; see step 2.

### 2. Copy or merge the static files

Source for all of these is [`files/`](./files/) next to this `SKILL.md` — every file there ships with this skill and gets deployed together, not picked individually.

- **No existing file**: copy straight across (`.editorconfig`, `stylecop.json`, `cleancoders.json`, `.gitignore`, and `Directory.Build.props`).
- **Existing `.editorconfig` / `stylecop.json` / `cleancoders.json`**: show the user a diff against this skill's copy and ask whether to overwrite, keep theirs, or hand-merge. Don't guess — these encode prior project-specific decisions you can't see from here.
- **Existing `Directory.Build.props`**: never overwrite. Merge in the `<PropertyGroup>` values and the `<ItemGroup>` `PackageReference`/`AdditionalFiles` entries from `files/Directory.Build.props` that the existing file doesn't already have, preserving whatever the target already defines if it conflicts.
- **Existing `.gitignore`**: never overwrite or ask for a full diff decision — append whichever lines from `files/.gitignore` are missing from the existing file, under a clearly marked `# from init-csharp-project` section header, so it's obvious later which lines came from this skill.

### 3. Make sure the packages can actually restore

`CleanCoders.Analyzers` is not on nuget.org — it's only in the local feed at `C:\_LocalNuGet`. Check whether the target already resolves it (a machine-wide NuGet source, or its own `nuget.config`). If not, add a `nuget.config` at the target root:

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <add key="LocalCleanCoders" value="C:\_LocalNuGet" />
  </packageSources>
</configuration>
```

If the target already has a `nuget.config`, add the `<add key="LocalCleanCoders" .../>` line to its existing `<packageSources>` instead of replacing the file. `Microsoft.VisualStudio.Threading.Analyzers` and `StyleCop.Analyzers` resolve from nuget.org as normal and need no extra source.

### 4. Create the folder skeleton

At the target root, create `docs/`, `src/`, and `tests/` if they don't already exist. These start empty — don't scaffold anything inside them (no placeholder `.cs` files, no test project) unless separately asked to. If the target is (or will be) a git repo and a folder is left empty, add a `.gitkeep` inside it so it survives the first commit; skip that for any of the three that already has content.

### 5. Ask about the `stylecop.json` placeholder

`stylecop.json`'s `companyName` ships as `"Acme"` — inert today because `Directory.Build.props` suppresses the file-header rules (`SA1633`/`SA1636`) that would consume it. Ask the user whether they want a real company/author name here, or are fine leaving the placeholder (harmless while those rules stay suppressed).

### 6. Verify

- [ ] `dotnet restore` succeeds (confirms `CleanCoders.Analyzers` resolved from the local feed; the other three from nuget.org)
- [ ] `dotnet build` succeeds — expect a large first-run wave of new `CA`/`IDE` warnings from `AnalysisMode=AllEnabledByDefault`; that's the intended starting state, not a bug (see `CONTEXT.md` for the plan to tone individual rules down over time)
- [ ] Deliberately violate one rule from each of the four layers and confirm the expected diagnostic fires — e.g. a method with 4+ arguments for `CC0042`, a using-directive placed inside a namespace for StyleCop, an `async void` method for `VSTHRD100`
- [ ] No `CCCFG001`/`CCCFG002`/`CCCFG003` diagnostics fire against the copied `cleancoders.json` (would mean it doesn't match the analyzer's embedded schema)
- [ ] `docs/`, `src/`, `tests/` exist at the target root
- [ ] `git status` (if the target is a git repo) shows `bin/`/`obj/` as ignored, not untracked, after a build

## Known gaps — don't paper over these without flagging them

- This skill has not been run against a real project yet. Treat every step above as a draft until it has.
- `AnalysisMode=AllEnabledByDefault` is a fresh, untested choice — expect the first real project run to surface rules worth suppressing immediately (start a running list in `CONTEXT.md` rather than silently accumulating `NoWarn`s with no record of why).
- `VSTHRD*` severities are entirely untuned in `.editorconfig` (see step above) — same expectation: the first real run is what decides which of these need a severity override, not a guess made now.
