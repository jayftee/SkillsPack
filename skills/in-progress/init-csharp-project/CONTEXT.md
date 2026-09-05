# init-csharp-project — background

**Relocated 2026-08-31** from `E:\SkillsPack\README.md` (then this repo's only file, written when it was a single-purpose nuget-template staging folder called `BaseCSharpConfig`). The repo pivoted to a multi-language Claude Code skills pack — see the root [README.md](../../../README.md) for the current structure. Everything below is preserved as-is: it's the design history and open questions behind this skill's payload (`files/`), useful context for writing `SKILL.md`, but it predates the skill/pack framing and should be read as historical record, not as current instructions for the repo as a whole.

**Status as of 2026-08-29: raw file payload only. Not yet a working `dotnet new` template — see "What's deferred" below before doing anything else here.**

## Why this folder exists

`E:\CleanCoder` (the CleanCodersStyleCopRules / CleanCoders.Analyzers project) built up a specific set of static analysis configuration — StyleCop rules, a custom Roslyn analyzer ported from *Clean Code* (Robert C. Martin), and the `.editorconfig`/`Directory.Build.props` wiring that makes them all agree with each other instead of fighting. That configuration isn't specific to the CleanCoder project's own subject matter (analyzer-writing) — it's meant to be the baseline for **any** future .NET/C# project the same person (Jeff) starts, at home or at the office.

This folder is where that reusable subset gets extracted to, so it can eventually be packaged and consumed by brand-new projects without copy-pasting files by hand each time or re-explaining the setup to an AI agent from scratch. The end goal (not yet built — see below) is a `dotnet new` **item template**: something you install once per machine, then run inside any newly-scaffolded project (`dotnet new webapi`, `console`, `classlib`, whatever) to drop this configuration in on top.

**Read this file first if you (or an AI agent) are opening this folder cold, with no memory of the conversation that created it.** That conversation happened in Claude Code inside the `E:\CleanCoder` project; nothing from it is available here automatically. This file is the deliberate replacement for that: the working principle established in that conversation was "reusable configuration belongs in versioned files, not in an AI's memory," and this README is that principle applied to itself — it's written so a fresh session can pick up the thread from the file alone.

## The "Quadruplet" of analyzers

The reusable configuration covers four analysis layers that are meant to work together without contradicting each other:

1. **OOB (out-of-box) Roslyn / `NetAnalyzers` `CA` rules** — built into the .NET SDK itself, no package reference needed. Tuned via `.editorconfig` (e.g. `CA2214` explicitly turned on because it ships disabled by default despite being genuine Framework Design Guidelines advice; `CA1416`/`CA1515` explicitly suppressed *at bootstrap* because they need a platform/API-surface decision a brand-new project hasn't made yet).
2. **"Microsoft async analyzer"** — **resolved 2026-08-31**: it is a fourth, separate package after all — [`Microsoft.VisualStudio.Threading.Analyzers`](https://www.nuget.org/packages/Microsoft.VisualStudio.Threading.Analyzers) (`VSTHRDxxx` rules, e.g. `VSTHRD200` "use `Async` naming convention"). Wired into `files/Directory.Build.props` pinned at `18.7.23` (confirmed current stable, not prerelease, as of that date). Resolves from nuget.org normally, no local feed needed. *(Originally logged here as an open question — no separate package had been found in the `CleanCoder` repo at the time, and the working assumption was that it was just OOB async `CA` rules. That assumption was wrong.)*
3. **StyleCop** — `StyleCop.Analyzers` NuGet package + `stylecop.json` (its settings) + `.editorconfig` (severity overrides where StyleCop's defaults fight modern C# conventions — see `docs/Trinity.md` in `CleanCoder`, not duplicated here, described below).
4. **CleanCoders.Analyzers** — the custom *Clean Code*-derived Roslyn analyzer built in the `CleanCoder` repo, packaged as a NuGet package (not yet published to nuget.org — see Distribution below) + `cleancoders.json` (its rule parameters, e.g. max method line count) + `.editorconfig` (per-rule on/off + severity, e.g. `dotnet_diagnostic.CC0042.severity = warning`).

## Design decisions already made (in the source conversation)

These were deliberated and settled before this folder was created — don't re-litigate them without a reason:

- **Mechanism: a `dotnet new` *item* template, not a *project* template.** A project template (like `dotnet new webapi`) creates a whole new project from nothing. An item template adds files into an *already-scaffolded* project directory without creating the project itself. The intended workflow is `dotnet new webapi -n MyApi` (or `console`, `classlib`, whatever — using Microsoft's own, always-current templates) **first**, then `cd MyApi && dotnet new cleancoders-config` (working name) to layer this config on top **second**.
- **Why there's no file collision doing it that way:** the StyleCop/CleanCoders.Analyzers `PackageReference`s and their `AdditionalFiles` wiring live in `Directory.Build.props`, not in the `.csproj` itself. MSBuild auto-imports the nearest `Directory.Build.props` walking up the directory tree from any `.csproj` beneath it — no explicit `<Import>` needed. So the item template only ever needs to add net-new files (`.editorconfig`, `Directory.Build.props`, `stylecop.json`, `cleancoders.json` + schema) — none of which `dotnet new webapi`/`console`/`classlib` create — and it never has to touch or merge the `.csproj` those commands generate.
- **Distribution: a local filesystem NuGet feed, not nuget.org.** Jeff isn't ready to publish `CleanCoders.Analyzers` (or this template) publicly. `dotnet new install <PackageId>` and `PackageReference` both resolve through the same NuGet source-resolution pipeline, which reads `nuget.config` — so a local folder registered as a source works identically to a real feed, just private. That local feed was originally `E:\Local_NuGet`; **as of this session it was moved/is being moved to `C:\_LocalNuGet`**, specifically so it works unmodified on office machines that may not have a `D:`/`E:` drive at all. `E:\CleanCoder`'s own `nuget.config`, `CONTEXT.md`, and `src/CleanCoders.Demo/README.md`/`.csproj` comments were updated in this same session to point at `C:\_LocalNuGet` instead of `E:\Local_NuGet` — confirmed working via `dotnet restore`. Both `E:\Local_NuGet\CleanCoders.Analyzers.0.1.0.nupkg` and `C:\_LocalNuGet\CleanCoders.Analyzers.0.1.0.nupkg` currently exist side by side; the old `E:\Local_NuGet` copy was deliberately **not** deleted this session (nobody asked for that) — if you're reading this later, decide whether it's safe to remove.
- **Location: a brand-new, separate git repo — not a folder inside `CleanCoder`.** Rationale given: `CleanCoder` is the analyzer's *own* source repo; the scaffolding template is a distinct, generic concern that happens to consume the analyzer as a package, not part of the analyzer's own codebase. `E:\BaseCSharpConfig` is that new repo's intended location. **This folder has not been `git init`'d yet** — that was left for later on purpose, not forgotten.
- **`cleancoders.schema.json` will be delivered by the `CleanCoders.Analyzers` NuGet package itself, not hand-copied into this template.** Originally this folder carried a loose copy of the schema so `cleancoders.json`'s `$schema` key would resolve for IDE autocomplete. That was removed after realizing it recreated the exact "two copies that can silently drift" risk this whole exercise is trying to avoid (see "Schema handling" below for the full reasoning and the actual plan).
- **What this folder does *not* need to scaffold:** the issue-tracker workflow (`.scratch/<feature>/issues/*.md`, checklist + Status + Comments) that `CleanCoder` uses to drive Claude Code through tickets is set up manually by Jeff using a separate Matt Pocock Claude Code skill pack (`/wayfinder`, `/grill-with-docs` to turn ideas into specs/issues first). That's an already-solved, already-portable part of his workflow and is explicitly out of scope for this template — don't try to bundle `docs/agents/issue-tracker.md` or a `.scratch/` convention in here.

## What's actually in this folder right now

Four files, copied **verbatim** from `E:\CleanCoder` on 2026-08-29 — no content changes (except `cleancoders.json`, see note below):

| File | Source of truth in `CleanCoder` | Purpose |
|---|---|---|
| `.editorconfig` | `E:\CleanCoder\.editorconfig` | Formatting/naming/diagnostic-severity rules for OOB `CA`, StyleCop `SA`, and `CC` (CleanCoders.Analyzers) diagnostics. Its own comments already anticipate this exact reuse (see the "Per-project-type accommodations" section near the bottom, which explicitly says a future project should be able to drop this file in unmodified). |
| `Directory.Build.props` | `E:\CleanCoder\Directory.Build.props` | Repo-root MSBuild properties auto-imported by every project beneath it. Sets `Nullable`, `ImplicitUsings`, `EnforceCodeStyleInBuild`, `GenerateDocumentationFile`, bootstrap `NoWarn`s, and wires `StyleCop.Analyzers` + `stylecop.json`. |
| `stylecop.json` | `E:\CleanCoder\stylecop.json` | StyleCop's own settings (using-directive placement outside namespace, no Hungarian prefixes, etc.). |
| `cleancoders.json` | `E:\CleanCoder\cleancoders.json` | Rule Parameters for CleanCoders.Analyzers (max method lines, max method arguments, etc.). **Differs from the source copy**: the `"$schema": "./cleancoders.schema.json"` key was removed here — see "Schema handling" below. |

**No `cleancoders.schema.json` in this folder — deliberately, not an oversight.** See "Schema handling" below before adding one back.

## Known gaps / things NOT to assume are finished

- **`Directory.Build.props` here only wires StyleCop — it does *not* reference `CleanCoders.Analyzers` at all.** In `CleanCoder` itself, the `CleanCoders.Analyzers` `PackageReference` + `cleancoders.json` `AdditionalFiles` wiring is currently done *per-project* (in `src/CleanCoders.Demo/CleanCoders.Demo.csproj`), not centrally, because that repo needs to toggle between a `PackageReference` path and a `ProjectReference` path (`UsePackagedAnalyzer`) to test the analyzer against its own source. **A consumer template should not replicate that toggle** — it should unconditionally add something like:
  ```xml
  <ItemGroup>
    <PackageReference Include="CleanCoders.Analyzers" Version="0.2.1" />
    <AdditionalFiles Include="$(MSBuildThisFileDirectory)cleancoders.json" Link="cleancoders.json" />
  </ItemGroup>
  ```
  to this folder's `Directory.Build.props`, parallel to the existing `StyleCop.Analyzers` block. **This has not been done yet.** Until it is, this folder covers 3 of the 4 quadruplet layers end-to-end (OOB, StyleCop) plus the *files* for the 4th (CleanCoders.Analyzers) without the *wiring*.
- **`.editorconfig` and `stylecop.json`'s comments reference `docs/Trinity.md` and `ADR-0001` — neither is duplicated into this folder, on purpose.** Those live only in `E:\CleanCoder\docs\Trinity.md` and `E:\CleanCoder\docs\adr\0001-rule-metadata-single-source-of-truth.md`. `Trinity.md` in particular is a dated verification log (it documents empirically testing specific StyleCop rules against the exact installed `StyleCop.Analyzers 1.2.0.556` version) — copying it here would go stale the moment either repo's analyzer versions diverge. If you need the "why" behind a suppression, go read it at the source.
- **`stylecop.json`'s `companyName` is `"Acme"` — a bootstrap placeholder**, currently inert because `CleanCoder`'s `Directory.Build.props` suppresses `SA1633`/`SA1636` (file header rules) repo-wide, so nothing actually consumes this value today. Decide a real value (or confirm the placeholder is fine) before this template gets used somewhere that turns file headers back on.
- **Only one CleanCoders.Analyzers rule is actually "live"**: `.editorconfig` enables just `dotnet_diagnostic.CC0042.severity = warning` (`MethodHasTooManyArgument`). More rules are still being ported from the legacy StyleCop add-in (`E:\CleanCoder\.scratch\cleancoders-analyzer-port\issues\`) — as each one ships, its severity line needs adding here too. This copy will silently fall behind `CleanCoder`'s `.editorconfig` as more rules get ported; there's no automatic re-sync.
- **This folder is not `git init`'d.**
- **No `.template.config/template.json` manifest exists yet** — as-is, `dotnet new install` on this folder would do nothing useful. This folder is the template's *content*, not yet the template itself.

## Schema handling — enforcement is now shipped (`CleanCoders.Analyzers` 0.2.1); editor-authoring delivery is still open

`cleancoders.json`'s `$schema` key was IDE authoring convenience only (autocomplete/inline validation in VS Code/Rider/Visual Studio while hand-editing the file) — confirmed by checking `CleanCoders.Analyzers`'s source before this work started: nothing in it referenced "schema" at all. The settings reader parsed `cleancoders.json` with its own hand-written defaulting/malformed-JSON logic, completely independent of `cleancoders.schema.json`.

That raised the question of whether a schema file sitting as a plain, user-editable file in every scaffolded project was a good idea at all. The answer: **no — make the analyzer itself validate `cleancoders.json` against the schema at build time**, with the schema **embedded as a resource inside `CleanCoders.Analyzers.dll`**. **This is now implemented and shipped as `CleanCoders.Analyzers` 0.2.1** (ticket `.scratch/nuget-packaging/issues/03-schema-embedding-and-validation.md` in `E:\CleanCoder`, done 2026-08-29):

- `CleanCoders.Analyzers.csproj` embeds the single repo-root `cleancoders.schema.json` (`<EmbeddedResource Include="..\..\cleancoders.schema.json" LogicalName="cleancoders.schema.json" />` — no second hand-made copy).
- A new internal `CleanCodersSchemaValidator` loads it via `Assembly.GetManifestResourceStream(...)` and checks a config file's `settings` object against it, generically (no hardcoded property names) reading each property's schema node for its `minimum` bound and checking for unrecognized properties.
- **No new dependency was added** (`JsonSchema.Net` was considered and dropped): once type-mismatches are recognized as already causing the existing `JsonException` fallback to fire (a string where an int belongs already made the file "malformed" before this ticket), the only genuinely uncovered gaps were numeric `minimum` bounds and `additionalProperties: false` — both simple enough to check by hand directly against the embedded schema's own JSON, with zero new bundled DLLs.
- A new `CleanCodersConfigurationAnalyzer` (not a Rule — no `CC####`/`FDG####` id, per `CONTEXT.md`'s own vocabulary) reports three diagnostics once per compilation: `CCCFG001` (value below schema minimum), `CCCFG002` (unrecognized property), `CCCFG003` (file isn't valid JSON at all). **Deliberately diagnostic-only, not value-substituting**: a violation is reported, but `CleanCodersSettingsReader`'s actual resolved values are completely unchanged from before this ticket — kept that way specifically to avoid any regression risk to already-tested behavior.
- Verified against a real NuGet-restored consumer (not just the in-repo test suite): packed, pushed to `C:\_LocalNuGet`, and a throwaway project restoring `CleanCoders.Analyzers` purely via `PackageReference` was built against deliberately bad `cleancoders.json` content — all diagnostics fired correctly with the expected messages.
- A `/code-review` pass right after the first implementation caught two real bugs before this shipped as final: case-sensitive property lookups disagreeing with the settings reader's own case-*insensitive* parsing (false "unknown property" reports, or worse, a capitalized top-level `Settings` key silently skipping validation of an entire file), and a missing check for the schema's `maximum` bound (only `minimum` was checked). Both fixed and re-verified the same way, which is why this shipped as `0.2.1` rather than the originally-pushed `0.2.0` — that version was already pushed to the feed before review, and was left in place rather than overwritten.

**Still open, not part of this shipped work**: the schema an IDE points at for *authoring* (autocomplete while hand-editing `cleancoders.json`) should come from the same package, not a hand-copied duplicate — e.g. a NuGet content file restored alongside the `PackageReference`, sourced from that same embedded resource. **That packaging mechanism still hasn't been designed.** Until it is, `cleancoders.json` in this template still has **no `$schema` key** — a known, accepted, temporary loss of editor autocomplete, preferred over shipping a duplicate already known to go stale. This was filed as an explicit follow-up in ticket `03`'s own task list rather than done as part of it.

**Do not re-add a loose `cleancoders.schema.json` to this folder as a quick fix** without first checking whether that follow-up has landed — that would reintroduce the exact duplicate-copy problem this work eliminated on the enforcement side.

If/when this folder's `Directory.Build.props` gets the `CleanCoders.Analyzers` `PackageReference` wired in (see deferred item 2 below), reference **`0.2.1` or later**, not `0.1.0` — `0.1.0` predates this validation entirely.

## What's deferred to the next session (explicitly — this is the actual next-step list)

**2026-08-31 pivot: this repo is no longer building toward the `dotnet new` item template as the primary delivery mechanism.** Items 1 and 4–9 below were written for that path specifically and are now optional/deferred indefinitely — see the root [README.md](../../../../README.md) for why (this became a multi-language Claude Code skills pack instead; C#'s payload now ships as `../SKILL.md` + `../files/`, applied directly, no packaging step required). Items 2 and 3 have since been done, just via the skill's payload file rather than a published template.

1. ~~`git init` this folder~~ — superseded; this repo is `E:\SkillsPack` now, not a single-purpose C# staging folder, and its own git status is a pack-level decision, not this skill's.
2. ~~Add the `CleanCoders.Analyzers` `PackageReference` + `cleancoders.json` `AdditionalFiles` block to `Directory.Build.props`.~~ **Done 2026-08-31** — in `../files/Directory.Build.props`.
3. ~~Resolve the "Microsoft async analyzer" open question.~~ **Done 2026-08-31** — see the Quadruplet section above; it's `Microsoft.VisualStudio.Threading.Analyzers`, now wired into `../files/Directory.Build.props` too.
4. Decide the template's short name, NuGet `PackageId`, and version. **Deferred indefinitely** — only relevant if the `dotnet new` item-template path is picked back up.
5. Add `.template.config/template.json`, marking it an **item** template. **Deferred indefinitely**, same reason.
6. `dotnet pack` it and `dotnet nuget push --source C:\_LocalNuGet`. **Deferred indefinitely**, same reason.
7. `dotnet new install <PackageId>` and test it end-to-end. **Deferred indefinitely**, same reason — `../SKILL.md`'s own verify checklist is the current equivalent.
8. Decide whether to also register `C:\_LocalNuGet` as a **machine-wide** NuGet source — discussed as an option, not decided. Still relevant either way (the skill's payload references this feed directly).
9. Decide the fate of the leftover `E:\Local_NuGet\CleanCoders.Analyzers.0.1.0.nupkg` copy. Still open, low stakes.
10. ~~In `CleanCoders.Analyzers` itself: embed `cleancoders.schema.json` as a resource in the DLL and wire real validation in.~~ **Done — shipped as `CleanCoders.Analyzers` 0.2.1.** See "Schema handling" above.
11. Design and implement how the analyzer package delivers that same schema to a consumer's editor without a hand-copied, driftable duplicate — then decide whether to re-add a `$schema` key to `cleancoders.json`. **Still open.** (`../files/cleancoders.json` has since had its `$schema` key removed, consistent with the "no loose duplicate" side of this decision.)

## Target end-to-end workflow — superseded by the skill

The `dotnet new cleancoders-config` workflow below was the original plan for this section and is kept only as historical record; it depends on the deferred item-template work above. **The current workflow is `../SKILL.md`**, run from inside Claude Code — it also now creates `docs/`, `src/`, `tests/` itself (see `../SKILL.md` step 4), which this original sketch had marked as a manual step. **Updated 2026-09-05**: `../SKILL.md` no longer requires an already-scaffolded project — step 1 now supports running config-first against an empty folder too (payload dropped in before `dotnet new`, verification deferred until a `.csproj` exists), matching a workflow where `dotnet new` itself falls out of spec/issue work (e.g. `wayfinder`/`grill-with-docs`) done after the skill's folder/config setup, not before it.

```powershell
mkdir MyNewProject; cd MyNewProject; git init
dotnet new webapi -n MyNewProject          # or console / classlib / whatever the project actually needs
dotnet new cleancoders-config              # layers .editorconfig, Directory.Build.props, stylecop.json, cleancoders.json in
mkdir src, tests                           # now templated instead — see ../SKILL.md step 4
# open Claude Code here; use /wayfinder or /grill-with-docs to turn ideas into .scratch/<feature>/issues/*.md,
# then drive implementation ticket-by-ticket, same pattern as E:\CleanCoder itself.
```

## Re-syncing with the source repo

If you're picking this up much later and want to check whether `CleanCoder`'s own config has moved on since 2026-08-29, diff this folder's five files against `E:\CleanCoder`'s root `.editorconfig`, `Directory.Build.props`, `stylecop.json`, `cleancoders.json`, `cleancoders.schema.json` directly — don't trust this copy to still be current without checking.
