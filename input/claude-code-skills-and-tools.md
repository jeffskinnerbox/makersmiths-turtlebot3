# Claude Code Skills and Tools

A complete inventory of skills and tools available in this Claude Code environment,
organized by scope.

Claude Code Prompt:
_What are all the available Claude Code skills & tools?
Organize them as project, user, and global skills & tools._

Claude Code Prompt:
_What are some good websites where Claude SKILL.md files are available to the public?
I'm looking for well designed SKILL.md file that are user tested._

---

## Project-Level Skills

Located in `.claude/skills/` within this repository. Shared via git with collaborators.

| Skill | Description | Allowed Tools |
|-------|-------------|---------------|
| `bill-of-materials-generator` | Generate workshop BOMs, parts lists, shopping lists, cost breakdowns | Read, Write, Edit, Glob, Grep, Bash |
| `explainer` | Break down and explain technical concepts in plain English | Read, Write, Edit, Glob, Grep, Bash |
| `history-and-application` | Generate historical origins, key people, evolution, and applications for a topic | Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch |
| `lesson-plan-generator` | Generate session-level lesson plans for makerspace workshops | Read, Write, Edit, Glob, Grep, Bash |
| `syllabus-generator` | Generate course syllabi and outlines for makerspace workshops | Read, Write, Edit, Glob, Grep, Bash |
| `theory-of-operation` | Generate theory-of-operation docs explaining how something works internally | Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch |


---

## User-Level Skills

Located in `~/.claude/skills/`. Available across all projects for this user.

| Skill | Description | Allowed Tools |
|-------|-------------|---------------|
| `code-doc-writer` | Generate/update docstrings, function comments, class docs, inline explanations | Read, Write, Edit, Grep, Glob |
| `code-reviewer` | Review code for quality, security vulnerabilities, best practices, maintainability | Read, Grep, Glob, Bash |
| `project-doc-writer` | Generate/update READMEs, setup guides, architecture docs, contribution guidelines | Read, Write, Edit, Bash, Grep, Glob |
| `skill-generator` | Create new Claude Code skills with proper structure and YAML frontmatter | _(unrestricted)_ |
| `test-generator` | Generate unit tests using appropriate testing frameworks | Read, Write, Edit, Bash, Grep, Glob |


---

## Global (Built-in) Skills

Provided by Claude Code itself. Not stored as files.

| Skill | Description |
|-------|-------------|
| `keybindings-help` | Customize keyboard shortcuts, rebind keys, add chord bindings, modify `~/.claude/keybindings.json` |


---

## Built-in Tools

These are core tools provided by Claude Code, always available regardless of project.

### File Operations

| Tool | Purpose |
|------|---------|
| `Read` | Read file contents (text, images, PDFs, Jupyter notebooks) |
| `Write` | Create or overwrite files |
| `Edit` | Make targeted string replacements in existing files |
| `Glob` | Find files by glob pattern (e.g., `**/*.py`) |
| `Grep` | Search file contents with regex (powered by ripgrep) |
| `NotebookEdit` | Edit cells in Jupyter notebooks (`.ipynb`) |

### Execution & System

| Tool | Purpose |
|------|---------|
| `Bash` | Run shell commands (git, npm, docker, etc.) |
| `Task` | Launch specialized subagents for complex tasks |
| `TaskStop` | Stop a running background task |
| `TaskOutput` | Retrieve output from background tasks |

### Task Management

| Tool | Purpose |
|------|---------|
| `TaskCreate` | Create a tracked task in the todo list |
| `TaskUpdate` | Update task status, dependencies, or details |
| `TaskGet` | Retrieve a task by ID |
| `TaskList` | List all tasks and their statuses |

### Web & Research

| Tool | Purpose |
|------|---------|
| `WebSearch` | Search the web for current information |
| `WebFetch` | Fetch and analyze content from a URL |

### Workflow & Planning

| Tool | Purpose |
|------|---------|
| `EnterPlanMode` | Enter plan mode to design an approach before coding |
| `ExitPlanMode` | Submit a plan for user approval |
| `AskUserQuestion` | Ask the user clarifying questions |
| `EnterWorktree` | Create an isolated git worktree for parallel work |
| `Skill` | Invoke a skill by name |

### Subagent Types (via Task tool)

| Agent Type | Purpose |
|------------|---------|
| `Bash` | Command execution specialist |
| `Explore` | Fast codebase exploration and search |
| `Plan` | Software architecture and implementation planning |
| `general-purpose` | Multi-step research and complex tasks |
| `claude-code-guide` | Answer questions about Claude Code, Agent SDK, and API |
| `statusline-setup` | Configure Claude Code status line settings |


---

## Public SKILL.md Resources

Curated list of websites where well-designed, user-tested SKILL.md files are publicly available.

### Official

| Resource | Description |
|----------|-------------|
| [anthropics/skills](https://github.com/anthropics/skills) | Anthropic's own public repo — production-quality examples across creative, technical, and enterprise domains. Includes a [skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) meta-template. |
| [Claude Code Skills Docs](https://code.claude.com/docs/en/skills) | Official docs on structure, frontmatter, and bundled resources |
| [How to Create Custom Skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) | Anthropic help center guide |

### Curated Community Collections

| Resource | Description |
|----------|-------------|
| [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | Well-maintained curated list with categories and descriptions |
| [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | Popular curated list of skills, resources, and tools |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | 300+ skills from official dev teams and community; cross-compatible with Codex, Cursor, Gemini CLI |

### Skill Libraries & Tooling

| Resource | Description |
|----------|-------------|
| [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) | Modular, domain-specific skill packages including subagents and commands |
| [alirezarezvani/claude-code-skill-factory](https://github.com/alirezarezvani/claude-code-skill-factory) | Toolkit for generating structured skill templates at scale |
| [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | Battle-tested configs from an Anthropic hackathon winner (skills, hooks, agents, MCPs) |

### Marketplace & Deep Dives

| Resource | Description |
|----------|-------------|
| [SkillsMP.com](https://skillsmp.com) | Agent Skills Marketplace supporting the open SKILL.md standard |
| [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/) | Detailed analysis of skill design patterns and best practices |


