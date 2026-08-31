# SkillsPack

**Status:** personal, pre-release. Nothing here is a plugin yet. Every skill lives under `skills/in-progress/` and is used locally — linked into one project at a time — while it earns enough real use to be trusted.

## What this is

A personal collection of [Claude Code Skills](https://code.claude.com/docs/en/skills.md) for initializing coding project folders with a consistent, opinionated baseline — static analysis config, linters, formatting rules — without hand-copying files or re-explaining the setup to an agent from scratch every time.

Each skill targets one language/ecosystem, because "initialize a project folder" means something different in each one:

- **C#** (`init-csharp-project`) — wires `.editorconfig`, `Directory.Build.props`, StyleCop, and a custom Clean-Code-derived Roslyn analyzer (`CleanCoders.Analyzers`) via MSBuild/NuGet conventions.
- **Python** (`init-python-project`, planned) — `.editorconfig`, `ruff`, and `pyproject.toml` conventions.

This started as a plan to ship the C# config as a `dotnet new` item template distributed through a local NuGet feed. That's C#-specific plumbing (MSBuild, `PackageReference`, `nuget.config`) that doesn't generalize to Python, which has its own idiomatic tooling. A Claude Code Skill is the layer that *does* generalize: a skill is just instructions plus bundled files that Claude executes with its own file tools, so "initialize a C# folder" and "initialize a Python folder" can be two skills sharing one distribution mechanism, each with its own payload underneath. The NuGet item template idea isn't dead — the C# skill could still shell out to it once it exists — but it's no longer required to get value today; the skill can copy/merge the payload files directly.

## Structure

```
skills/
├── in-progress/              <- everything starts here
│   └── <skill-name>/
│       ├── SKILL.md            <- the skill itself: name/description frontmatter + steps
│       ├── CONTEXT.md          <- (optional) background/decisions specific to this skill
│       └── files/              <- the actual payload copied/merged into a target project
└── <topic>/                   <- e.g. project-init/ — where a skill moves once it's trusted
    └── <skill-name>/
        ├── SKILL.md
        └── files/
```

Two kinds of bucket, one meaning each:

- **`skills/in-progress/`** — unvalidated. A skill lives here from the moment it's drafted until it's been run against a handful of real projects and holds up. It can change shape, break, or disappear without notice — that's the point of the bucket, not a bug in it.
- **A topic bucket** (e.g. `skills/project-init/`) — a skill moves here only once it's actually been trusted with real projects. There's no separate "promoted" holding pen in between: graduating a skill just means moving its folder from `in-progress/` to the topic bucket it belongs to. Modeled on [Matt Pocock's skills repo](https://github.com/mattpocock/skills), which splits `skills/engineering/` and `skills/productivity/` the same way, with `skills/in-progress/` and `skills/misc/` holding what isn't shipped.

This repo has no `.claude-plugin/plugin.json` yet — that's the eventual step once there's something worth shipping to a wider audience. When it happens, `plugin.json`'s `skills` array will list only what's sitting in the topic buckets at that time, the way Matt's does.

## Current skills

| Skill | Bucket | Status |
|---|---|---|
| [`init-csharp-project`](./skills/in-progress/init-csharp-project/) | `in-progress` | Payload present (`.editorconfig`, `Directory.Build.props`, `stylecop.json`, `cleancoders.json` under `files/`); `SKILL.md` not written yet — see its [`CONTEXT.md`](./skills/in-progress/init-csharp-project/CONTEXT.md) for the design history behind the payload |
| `init-python-project` | `in-progress` | Not started — folder scaffolded only, no payload or `SKILL.md` yet |

## Using a skill from this repo

None of this is a plugin, so there's no marketplace install. A skill only does anything once Claude Code can find its `SKILL.md` from wherever you're actually working. Claude Code looks for skills in two places:

- **Per-project**: `<your-project>\.claude\skills\<skill-name>\SKILL.md`
- **For yourself, everywhere**: `~\.claude\skills\<skill-name>\SKILL.md`

Rather than copying a skill's folder into every project you use it in (and drifting out of sync with the copy here), link to it — Claude Code follows symlinks and reads `SKILL.md` from the target:

```powershell
# from inside the target project
New-Item -ItemType SymbolicLink -Path ".claude\skills\init-csharp-project" -Target "E:\SkillsPack\skills\in-progress\init-csharp-project"
```

(Creating a symlink on Windows normally needs Developer Mode turned on, or an elevated shell — see **Settings > Privacy & security > For developers** if `New-Item` refuses.)

Once linked:

- **User-invoked**: type `/init-csharp-project` in that project's Claude Code session.
- **Model-invoked**: Claude can also reach for the skill on its own if the task matches its `description` frontmatter, unless the skill sets `disable-model-invocation: true`.

A newly-created top-level `.claude\skills\` folder needs a Claude Code restart to be picked up; adding further skills under one that already exists does not.

**Skills in `skills/in-progress/`** work exactly the same way — nothing at the Claude Code level distinguishes "in progress" from "graduated." The bucket is a signal to *you* about how much to trust it, not a mechanism Claude Code enforces. Point the symlink at whichever path is currently true, and expect an `in-progress` skill to be less stable.

**Skills that have graduated** to a topic bucket are used identically — same symlink, just pointed at `skills\project-init\<skill-name>` (or whichever topic bucket applies) instead of `skills\in-progress\<skill-name>`. The only difference is confidence: something in a topic bucket has already proven itself against real projects.

## Next steps

1. Write `skills/in-progress/init-csharp-project/SKILL.md` — detect what's already in the target project, copy/merge the four files in `files/`, wire the `Directory.Build.props`/`.csproj` references, verify.
2. Build out `init-python-project`'s payload and `SKILL.md`.
3. Once both have survived real use on real projects, move them into a topic bucket.
