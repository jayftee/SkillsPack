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
- **`Crap4DotNet`** as a local `dotnet tool`, if not already installed — a CRAP-score (complexity × poor-coverage risk) reporter, separate from the quadruplet: it's a CLI tool run on demand against a coverage file, not a build-time analyzer, and has no settings file of its own (CLI flags only — see `CONTEXT.md`).
- A **`docs/`, `src/`, `tests/`** folder skeleton at the target root, if not already present.

This skill only ever adds files *around* the actual `.csproj` — it never touches the `.csproj` itself. That means it works in either order:

- **After scaffolding**: `dotnet new webapi`/`console`/`classlib`/etc. (or an existing project) has already created the `.csproj`. The full verify checklist in step 7 applies immediately.
- **Before scaffolding**: the target is an empty (or otherwise project-less) folder — you're bundling the payload first and will run `dotnet new` later, e.g. as a step that falls out of spec/issue work. This works because `Directory.Build.props`, `.editorconfig`, and `nuget.config` are all discovered by an upward directory walk from wherever a `.csproj` eventually lands, performed at build/restore time — not at file-creation time. Nothing about MSBuild/NuGet cares which came first. Step 7's restore/build checks just get deferred until a project actually exists to run them against.

Background on *why* these specific files/rules exist lives in [`CONTEXT.md`](./CONTEXT.md) next to this file — read it if a step below doesn't make sense, don't duplicate it here.

## Steps

### 1. Confirm the target and detect what's already there

Check the target directory (default: current working directory) for a `.sln`/`.slnx` or at least one `.csproj` somewhere under it. Don't stop if there isn't one — record which case you're in, since it changes step 7:

- **Scaffolded** (`.sln`/`.slnx`/`.csproj` found): the full verify checklist in step 7 applies.
- **Empty / config-only** (none found): this is a config-first run, ahead of a `dotnet new` that hasn't happened yet. Proceed through steps 2–6 as normal, but skip step 7's restore/build/diagnostic checks — there's no project yet to run them against — and tell the user those are deferred until they've scaffolded the project, at which point re-running this skill (or just `dotnet restore`/`build`) picks them back up.

Then check, at the target root, for an existing:

- `.editorconfig`
- `Directory.Build.props`
- `stylecop.json`
- `cleancoders.json`
- `.gitignore`
- `nuget.config`
- `.config/dotnet-tools.json`

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

This step is just writing/editing the config file — do it the same way whether or not a project exists yet. `nuget.config` is resolved by the same upward-directory-walk mechanism as `Directory.Build.props`, so it doesn't matter whether it predates the `.csproj` it will eventually apply to.

### 4. Install `Crap4DotNet` as a local tool — check first, don't reinstall blindly

[`Crap4DotNet`](https://www.nuget.org/packages/Crap4DotNet) computes CRAP scores (`complexity(m)² × (1 − coverage(m))³ + complexity(m)`) to flag methods that are both complex and poorly tested. Unlike the quadruplet, it's a CLI tool invoked on demand (with a coverage file, typically from `coverlet`), not a build-time analyzer, and it has no project config file of its own — see `CONTEXT.md` for why this step only manages the tool's *presence*, never its behavior.

- Check for `.config/dotnet-tools.json` at the target root (a manifest is per-directory, not per-`.csproj` — this works identically whether or not a project has been scaffolded yet, same as step 3).
  - **Missing**: run `dotnet new tool-manifest` to create it.
  - **Exists**: read it before touching anything.
- Check whether `Crap4DotNet` is already listed under `"tools"` in that manifest.
  - **Already present**: leave it alone — don't overwrite, don't bump the version without being asked. It's already installed for this project.
  - **Not present**: run `dotnet tool install --local Crap4DotNet --version 0.1.1` (0.1.1 is latest on nuget.org as of this writing — check for a newer version before installing into a brand-new project rather than assuming this pin is still current, the same way `Directory.Build.props`'s `CleanCoders.Analyzers` pin gets bumped).

### 5. Create the folder skeleton

At the target root, create `docs/`, `src/`, and `tests/` if they don't already exist. These start empty — don't scaffold anything inside them (no placeholder `.cs` files, no test project) unless separately asked to. If the target is (or will be) a git repo and a folder is left empty, add a `.gitkeep` inside it so it survives the first commit; skip that for any of the three that already has content.

### 6. Ask about the `stylecop.json` placeholder

`stylecop.json`'s `companyName` ships as `"Acme"` — inert today because `Directory.Build.props` suppresses the file-header rules (`SA1633`/`SA1636`) that would consume it. Ask the user whether they want a real company/author name here, or are fine leaving the placeholder (harmless while those rules stay suppressed).

### 7. Verify

Runs in full only for a **scaffolded** target (step 1). For a **config-only** run, do just the last three checks now — the rest need a real `.csproj` to run against — and tell the user the first four are deferred until they scaffold the project:

- [ ] *(scaffolded only)* `dotnet restore` succeeds (confirms `CleanCoders.Analyzers` resolved from the local feed; the other three from nuget.org)
- [ ] *(scaffolded only)* `dotnet build` succeeds — expect a large first-run wave of new `CA`/`IDE` warnings from `AnalysisMode=AllEnabledByDefault`; that's the intended starting state, not a bug (see `CONTEXT.md` for the plan to tone individual rules down over time)
- [ ] *(scaffolded only)* Deliberately violate one rule from each of the four layers and confirm the expected diagnostic fires — e.g. a method with 4+ arguments for `CC0042`, a using-directive placed inside a namespace for StyleCop, an `async void` method for `VSTHRD100`
- [ ] *(scaffolded only)* No `CCCFG001`/`CCCFG002`/`CCCFG003` diagnostics fire against the copied `cleancoders.json` (would mean it doesn't match the analyzer's embedded schema)
- [ ] `docs/`, `src/`, `tests/` exist at the target root
- [ ] `git status` (if the target is a git repo) shows `bin/`/`obj/` as ignored, not untracked, after a build — meaningful immediately if there's already a project checked in; otherwise this just confirms the ignore rules are in place for later
- [ ] `dotnet tool restore` succeeds and `dotnet tool run dotnet-crap --help` (or `dotnet dotnet-crap --help`) resolves — confirms `Crap4DotNet` is actually usable from the manifest, not just listed in it

## Known gaps — don't paper over these without flagging them

- This skill has not been run against a real project yet, in either order. Treat every step above as a draft until it has.
- The config-first path (step 1) is new and unverified: nobody has yet confirmed end-to-end that a `Directory.Build.props`/`.editorconfig`/`nuget.config` dropped into an empty folder is actually picked up once `dotnet new` scaffolds a project underneath it. The MSBuild/NuGet upward-directory-walk mechanism this relies on is well-documented behavior, not a guess — but this skill's own first config-first run is still the thing that proves it in practice.
- `AnalysisMode=AllEnabledByDefault` is a fresh, untested choice — expect the first real project run to surface rules worth suppressing immediately (start a running list in `CONTEXT.md` rather than silently accumulating `NoWarn`s with no record of why).
- `VSTHRD*` severities are entirely untuned in `.editorconfig` (see step above) — same expectation: the first real run is what decides which of these need a severity override, not a guess made now.
- Step 4 (`Crap4DotNet`) is new and unverified: nobody has yet confirmed the manifest-create → install → `dotnet tool restore` sequence end-to-end on a real target, in either the scaffolded or config-first case, or that `dotnet tool run dotnet-crap` is actually the right invocation once installed locally.
