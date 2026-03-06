# Claude Skills
Agent Skills are modular capabilities that extend Claude's functionality.
Each skill packages instructions, metadata, and optional resources
(scripts, templates) that Claude uses automatically when relevant.
Skills are reusable, filesystem-based resources that provide
Claude with domain-specific expertise.
Unlike prompts (which are conversation-level instructions for one-off tasks),
skills load on-demand and eliminate the need to repeatedly provide the same guidance across sessions.

## What a SKILL.md file is
Each skill is a directory containing a `SKILL.md` file
(with YAML frontmatter and instructions) plus optional scripts and resources.
The Skill tool embeds an `<available_skills>` list built from the frontmatter of all skills.
When invoked, the tool response expands the context and references additional resources.
It loads only when needed, keeping the main prompt lean.

A minimal skill looks like:

```text
.claude/skills/
└── ros2-build/
    ├── SKILL.md
    └── scripts/
        └── build.sh
```

Within `SKILL.md`:

```text
---
name: ros2-build
description: ROS 2 build workflows using colcon. Use when building packages or running ros2 commands.
---
# ROS 2 Build Instructions
[your instructions here]
```

## How Claude discovers and loads them
By default, both you and Claude can invoke any skill. You can type `/skill-name` to invoke it directly,
and Claude can load it automatically when it determines the skill is relevant to your conversation.
The description field in the frontmatter is what Claude uses to decide when to activate a skill automatically.

Two frontmatter fields let you restrict invocation: `disable-model-invocation: true`
means only you can invoke it (useful for workflows with side effects like `/deploy`);
`user-invocable: false` means only Claude can invoke it
(useful for background knowledge that isn't a meaningful user command).

## Where skills live
Claude Code scans `~/.config/claude/skills/` for global skills available across all projects,
and `.claude/skills/` within a project for project-scoped skills.

## One practical caveat
Skills are also not limited to Claude Code — Claude.ai and Claude Desktop also support them,
so you can define a skill once and use it across platforms.
However, one practitioner noted that automatic triggering can be unreliable
and recommends keeping a list of your skills in `CLAUDE.md` as a workaround until the auto-discovery improves.
