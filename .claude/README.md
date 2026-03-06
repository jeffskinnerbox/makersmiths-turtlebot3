
# The .claude Directory
Claude Code uses the hidden directory `.claude` in your project home directory
to manage configuration, conversation history, and custom tools.
These let you customize Claude Code's behavior and share project-specific (**NOT** global) settings with your team.
Your project-level `.claude` is separate from the global one in your home directory at `~/.claude`.

Key files & directories you can put in `.claude`:
* `CLAUDE.md` — This is the most important file and is sometimes found in the projects root directory instead of here.
  `CLAUDE.md` files are markdown files that give Claude persistent instructions for a project.
  Claude reads them at the start of every session.
  This is where you'd document your ROS 2 architecture, coding conventions, build workflows,
  and anything else Claude should always know about your project.
  You can run `/init` to have Claude analyze your codebase and generate a starter `CLAUDE.md` automatically.
* `CLAUDE.local.md` — for private per-project preferences that shouldn't be checked into version control.
  It's automatically added to `.gitignore`. This is analogous to your `settings.local.json`.
* `settings.json` — the team-shared version of the permissions/sandbox config you already have in `settings.local.json`.
  Anything here gets committed and applies to everyone on the project.
* `settings.local.json` — your personal overrides of `settings.json`. Git-ignored, personal only.
* `.claude/rules/` — a modular alternative that can be used with the monolithic `CLAUDE.md`.
  You organize instructions into multiple markdown files that Claude loads as project memory,
  and they load with the same high priority as `CLAUDE.md`.
  Great for separating concerns — e.g., a `ros2.md`, a `testing.md`, etc.
* `.claude/commands/` — custom slash commands you can invoke during a session (e.g., `/project:build`).
* `.claude/skills/` — where you store project-scoped custom skills — modular, reusable capability packages
  that Claude loads automatically when relevant to a task.

>**NOTE:** `.clauderules` is an older/alternative format that functions similarly to `CLAUDE.md`.
>The better modern approach is to keep `CLAUDE.md` lean with only universally applicable instructions,
>then use `.claude/rules/` to break domain-specific rules into focused files.

>**NOTE:** Claude is not very clear about the possibility of a `CLAUDE.md` file in your project root
>and having an additional one in `.claude/CLAUDE.md`.
>My recommendation is Don't try to maintain both.  Pick one place for your `CLAUDE.md`.

