


[Claude Code roadmap.sh](https://roadmap.sh/claude-code) - Step-by-Step guide to becoming a Claude Code expert in 2026
* [Vibe Coding](https://roadmap.sh/vibe-coding)

my-vision --> specification --> development-plan
my-bom -->
my-claude-prompts -->


my-vision (including bom or close to it) --> specification --> development-plan

1. System Requirements / Spec — what the product's software & hardware must do (often written with stakeholders/customers)
1. Architecture Document — how you'll design a system to meet those specs
* Hardware Architecture - (block diagrams, chip selection, PCB partitioning)
* Software Architecture - (firmware layers, RTOS task breakdown, driver interfaces)
* Interface Control Documents (ICDs) -  formal, structured records defining the precise, technical interfaces between system components,
    subsystems, or external systems. They document data formats, communication protocols, timing, and physical connections,
    ensuring compatibility and reducing risk during development. They are crucial for distributed development teams.
1. Detailed Design / Implementation Specs — drill-down specs for individual modules informed by the architecture

Principles:
* The architecture document should always be traceable back to the spec.
  Every major architectural decision should exist because a requirement demanded it.


----

Claude Code ....
  Methodology - high-level system of principles, rules, and postulations that guide how you approach work in a specific field. It is the "philosophy" behind your actions, explaining the why and the logic behind your chosen strategy.
  Setup Guide - a technical, step-by-step set of instructions focused on the initial installation and configuration of a product or system. Its sole purpose is to get you from "out of the box" to "fully operational" as quickly as possible.
  Cheatsheet - condensed, highly scannable reference tool that distills complex information into a quick-access format. It serves as a "just-in-time" memory trigger for specific commands, formulas, or steps, allowing you to bypass deep documentation when you're already in the flow of work.
  Workflow - the repeatable sequence of specific tasks or steps that move a project from start to finish. If methodology is the philosophy, the workflow is the conveyor belt that ensures work flows smoothly through your system.
  Playbook - collection of specific tactics, canned responses, and best practices for various scenarios. It’s a "how-to" manual designed to help teams react consistently and effectively when a specific situation (like a PR crisis or a sales lead) arises.
  Use Cases - are specific scenarios that describe how a user interacts with a system to achieve a particular goal. They serve as practical examples to demonstrate the real-world value and functionality of a product.
  Roadmap - high-level strategic document that maps out the big-picture goals and milestones of a project over a specific timeline. It acts as your "North Star," aligning stakeholders on where you’re going and when you expect to arrive without getting bogged down in the daily weeds.



# Claude Code Methodology
After observing hundreds of developers use Claude Code,
the best pattern that is clear can be summed up:
Pros treat Claude Code as a system to be engineered, not just a tool to be prompted.
The differentiators are:

* Workflow discipline over prompt engineering
* Context management as a first-class concern
* Deterministic automation (hooks, commands) over hoping Claude remembers
* Parallelization through worktrees and subagents
* Verifiable targets (tests, visual mocks) instead of vague instructions

The prompts were never the problem.
The difference between a mediocre Claude Code session
and a great one has almost nothing to do with prompt syntax.

Sources:
* [17 Best Claude Code Workflows That Separate Amateurs from Pros (Instantly Level Up)](https://medium.com/@joe.njenga/17-best-claude-code-workflows-that-separate-amateurs-from-pros-instantly-level-up-5075680d4c49)
* [AskUserQuestionTool Changed How I Use Claude Code](https://www.youtube.com/watch?v=TQ0F8RW-yjc)
* [What is Claude Code's AskUserQuestion tool? How to use it for spec-based development](https://www.atcyrus.com/stories/claude-code-ask-user-question-tool-guide)
* [Claude Code's Ask User Question Tool: First Impressions](https://torqsoftware.com/blog/2026/2026-01-14-claude-ask-user-question/)
* [Create Interactive AI Tools with Claude Code's AskUserQuestion](https://egghead.io/create-interactive-ai-tools-with-claude-codes-ask-user-question~b47wn)
## Claude Code Setup Guide
* [Claude Code for the Rest of Us: Setup Guide](https://www.whytryai.com/p/claude-code-beginner-guide)

## Claude Code Cheatsheet
* [Claude Code Cheat Sheet](https://github.com/Njengah/claude-code-cheat-sheet)
* [Claude Code Cheatsheet](https://awesomeclaude.ai/code-cheatsheet)
* [Our Claude Code Cheatsheet](https://neon.com/blog/our-claude-code-cheatsheet)
* [Claude Code cheatsheet](https://devhints.io/claude-code)
* [Claude Code Cheat Sheet for Beginners and Developers](https://www.igmguru.com/blog/claude-code-cheat-sheet)

## Claude Code Skills & MCP
* [Claude Code Beyond Basics: The Power of Skills & MCP](https://www.whytryai.com/p/claude-code-ide-skills-mcp)

## Claude Code Workflow / Methodology

```bash
# Edit your project's CLAUDE.md file
/memory   # not clear this is useful

# Open settings
/config  # not clear this is useful

# View or change tool permissions
/permissions

# Visualize current context usage as a colored grid
/context

# enter the prompt below in Plan Mode and ask claude how it intends to approach building the syllabus and that it should ask question
/plan

# paste in your prompt
```

### Do Your Research With Claude Code
Have a deep back-and-forth with Claude first.
Describe what you want to build.
Ask for system design options.
Ask questions.
Let it ask you questions.
Settle on a solution together.

Before you ask Claude to build a feature, think about the architecture.
Before refactoring, think about the end state.
Before debugging, think about what you actually know about the problem.

### Context Windows Degrade Fast
Opus 4.5 has a 200,000 token context window.
But here’s what people don’t realize: the model deteriorates way before you hit 100%.
Quality starts dropping around 20–40% context usage. Sometimes earlier.

Every message, every file Claude reads, every piece of generated code, every tool result — all of it accumulates.
Once quality starts dropping, more context makes it worse.Once quality starts dropping, more context makes it worse.

Make use of these tools:

```bash
# visualize current context usage as a colored grid
/context

# clear conversation history and free up context
/clear

# clear conversation history but keep a summary in context. Optional: /compact [instructions for summarization]
/compact
```

### Use The “Plan Before You Code” Discipline
* **Amateurs** jump straight into coding.
* **Pros** use a structured **Research → Plan → Implement → Validate → Iterate**

Claude tends to jump straight to coding a solution.
While sometimes that’s what you want,
asking Claude to research and plan first improves performance for problems requiring deeper thinking upfront.

**Pro Workflow:**
1. Use Plan Mode (Shift+Tab twice) for read-only codebase exploration before writing anything
1. Explicitly tell Claude: “Read the relevant files, but don’t write any code yet.”
1. Use thinking triggers that map to increasing levels of thinking budget: "think" → "think hard" → "think harder" → "ultrathink"
1. Ask Claude to create a plan document before implementing so you can course-correct early

```bash
# Use Plan Mode (Shift+Tab twice) for read-only codebase exploration before writing anything
# You can use backslash (\) + return to add newlines to you prompt

# clear your context before starting new project activity
/clear

# Tell Claude: “Read the relevant files, but don’t write any code or documentation yet.”
/plan

# Tell Claude: “Create a plan document before implementing any code or specification document.  think harder”
```

Iterate on this until you have a plan you like.

### Create Your Claude.md File
* **Amateurs** either skip `CLAUDE.md` or stuff it with everything.
* **Pros** keep it lean, specific, and hierarchical.

LLMs can follow approximately 150–200 instructions with reasonable consistency.
As instruction count increases, instruction-following quality decreases uniformly.
This means Claude doesn’t just ignore newer instructions, it begins to ignore all of them.

```bash
# Create a CLAUDE.md file for your project
/init

```

**Pro Workflow:**
1. Keep `CLAUDE.md` under 50 lines for hobby projects
1. Never send an LLM to do a linter’s job — use deterministic tools for code style, not instructions
1. Use the `.claude/rules/` directory for modular organization (separate files for code-style, testing, security)
1. Use `@path/to/import` syntax to reference files dynamically rather than embedding content
1. If you have extensive documentation elsewhere, don’t `@-mention` those files in your CLAUDE.md (this bloats context).
   Instead, mention the path and pitch Claude on why and when to read it:
   “For complex usage or if you encounter a `FooBarError`, see `path/to/docs.md` for advanced troubleshooting steps.”

### Be Master of the Context Window
* **Amateurs** let context bloat until Claude forgets earlier instructions.
* **Pros** treat context like a scarce resource.

A fresh Claude session typically costs a baseline ~20k tokens (10%)
with the remaining 180k for making changes — which can fill up fast.

**Pro Workflow:**
1. Run `/context` mid-session to understand your token usage
1. Avoid auto-compaction — it’s opaque, error-prone, and not well-optimized
1. Use `/clear` for simple reboots
1. For complex tasks, use the “Document & Clear” method:
   have Claude dump its plan and progress into a `.md` file,
   `/clear` the state, then start a new session by telling it to read the `.md` and continue
1. Never exceed 60% context and clear context between each phase of work
1. Disable unused MCP servers with `/mcp` before compacting to maximize available context

Split your work into 4 phases: **Research → Plan → Implement → Validate**,
(creating your `research.md`, `plan.md`, `specifications.md`, code, `test-plan.md`)
and then clear context between each phase.

### Use Test-Driven Development as a Feedback Loop
* **Amateurs** ask Claude to build features.
* **Pros** give Claude verifiable targets through tests first.

Claude performs best when it has a clear, verifiable target.
Tests provide this explicit target, allowing Claude to make changes, evaluate results, and incrementally improve.

**Pro Workflow:**
1. Leverage `CLAUDE.md` to establish project-wide TDD conventions and quality standards
1. Ask Claude to write tests based on expected input/output pairs
1. Be explicit that you’re doing test-driven development so it avoids creating mock implementations
1. Tell Claude to run tests and confirm they fail (no implementation code yet)
1. Commit the failing tests
1. Ask Claude to implement until tests pass
1. At this stage, ask Claude to verify with independent subagents that the implementation isn’t overfitting to the tests

Use hooks to automatically run test suites after any file edit.
Course correct early and often — be an active collaborator.

### Custom Slash Commands for Repeatable Workflows
* **Amateurs** type the same prompts repeatedly.
* **Pros** encode workflows as reusable commands.

**Pro Workflow:**

### Hooks for Deterministic Automation
* **Amateurs** rely on Claude to “remember” to run linters and tests.
* **Pros** use hooks to guarantee it happens.

**Pro Workflow:**

### Subagents for Context-Efficient Research
* **Amateurs** have one agent do everything.
* **Pros** delegate research to subagents to preserve the main context.

**How Subagents Help:**
A complex task requires X tokens of input context,
accumulates Y tokens of working context,
and produces a Z token answer.
Running N tasks means (X + Y + Z) × N tokens in your main window.
Subagents farm out the (X + Y) work to specialized agents,
which only return the final Z token answers,
keeping your main context clean.

**Pro Workflow:**

### MCP Server Integration for Real-World Connectivity
* **Amateurs** use Claude as an isolated coding assistant.
* **Pros** connect Claude to their entire development ecosystem.

**Pro Workflow:**

### Visual Iteration Loop
* **Amateurs** describe what they want.
* **Pros** show Claude what they want and let it iterate visually.

Like humans, Claude’s outputs tend to improve significantly with iteration.
While the first version might be good, after 2–3 iterations it will typically look much better.
I also found that specifically telling Claude to make outputs “aesthetically pleasing”
helps remind it that it’s optimizing for a human viewing experience

**Pro Workflow:**
1. Give Claude a visual mock (paste/drag-drop image or provide file path)
1. Use Puppeteer MCP to take browser screenshots
1. Ask Claude to implement, screenshot the result, and iterate until it matches

### The Extended Thinking Spectrum
* **Amateurs** use ultrathink for everything.
* **Pros** match thinking levels to task complexity.

Make sure to match thinking levels to task complexity.
Claude Code has built-in preprocessing that maps keywords to thinking budgets:


| Trigger | Token Budget | Use Case |
|:----|:-----:|:------|
| `think` | ~1,000 | Routine tasks, basic planning |
| `think hard` | ~5,000 | API integration, perfromance optimization |
| `think harder` | ~10,000 | Architecutre decisions, security audits |
| `ultrathink` | ~32,000 | Massivly complex problems |


**When to Use Each:**
* **Basic thinking use `think`:** Refactor this class, add error handling, fix simple errors
* **Enhanced thinking use `think hard`:** Design a caching strategy, plan database migration
* **Complex thinking `think harder`:** Design scalable architecture for 10M users, comprehensive security audit, migration of monolith to microservices

**Mistake to Avoid** - Using "think harder" for everything burns through your API budget and slows everything down.
Think harder is a scalpel, not a hammer.

**Pro Tip** - Toggle verbose mode with `Ctrl+O` to see Claude's thinking process displayed as gray italic text.

Claude executes with precision because all the ambiguity has been resolved upfront.
The `AskUserQuestion` tool makes this possible by front-loading all the decision-making,
resulting in a better design & code.

### Session Management Mastery
* **Amateurs** start fresh every time.
* **Pros** leverage session persistence and resumption.

**Pro Workflow:**
1. Give Claude sessions descriptive names with `/rename` to find them later
1. Use `claude --resume` a session from days ago to ask Claude to summarize how it overcame a specific error—then use that to improve your `CLAUDE.md`
1. Session history is stored in `~/.claude/projects/`. You can run meta-analysis on these logs looking for common exceptions and error patterns

**Key Commands:**
* `claude --continue` (or -c): Continue the most recent conversation
* `claude --resume` (or -r): Opens an interactive session picker
* `/resume` (inside Claude): Switch to a different conversation

**Power Move:**
Use `/rewind` or press `Esc` twice to access the checkpoint system. You can restore:
* **Conversation only:** Rewind to a user message while keeping code changes
* **Code only:** Revert file changes while keeping the conversation
* **Both:** Restore both to a prior point

#### Session Toggle: Permission Modes
1. **The Quickest Way: Session Toggle:** While inside a Claude Code session, you can cycle through permission modes using a keyboard shortcut:
    * Press `Shift + Tab`: This cycles between **Normal**, **Auto-Accept**, and **Plan** modes.
    * Look for the `⏵⏵ accept edits on` indicator at the bottom of your terminal.
  **Note:** In "Accept Edits" mode,
  Claude will automatically apply file changes but will still ask for permission before running `bash` commands for safety.
1. **The "Nuclear Option": Skip All Permissions:**
   If you are working in a safe, sandboxed environment (like a Docker container or VM)
   and want Claude to run everything—including terminal
   commands—without asking, use the following flag when starting the tool: `claude --dangerously-skip-permissions`.
   **_[!WARNING] This allows Claude to execute any shell command (like `rm -rf /`)
   and edit any file without your intervention. Only use this in isolated environments._**
1. **Persistent Configuration (Global Auto-Approval):**
   If you want to permanently change the default behavior so you don't have to toggle it every time,
   you can edit your global settings file located at `~/.claude/settings.json`.
   Add or modify the permissions block:
    * `defaultMode`: "**acceptEdits**": Claude will always start with file-editing auto-approved.
    * `allow`: This is an allowlist for specific tools or command patterns. You can allow all Read operations or specific Bash commands.

      ```json
      {
        "permissions": {
          "defaultMode": "acceptEdits",
          "allow": [
            "Bash(npm test)",
            "Bash(ls *)",
            "Read",
            "Edit"
          ]
        }
      }

    ```
1. **Selective "Always Allow":** When Claude asks for permission for a specific command (e.g., `git status`s),

   you can often select an option like "**Yes, and don't ask again for this command**".
    * This automatically adds that command pattern to your `.claude/settings.json` for that specific project.
    * You can manage these rules anytime by running the `/permissions` command within the Claude Code CLI.
1. **Sandboxing (Safer Automation):** If you want bash commands to be auto-approved safely,
   you can enable the **Sandbox** feature in your settings.
   When sandboxed, Claude runs commands in an isolated environment where it can't harm your host system.
    * In your `settings.json`, set "sandbox": `{ "enabled": true, "autoAllowBashIfSandboxed": true }`.

**Example #1:**
For TurtleBot3 and ROS 2 Jazzy, this configuration optimized for a Robotics (Python/C++) workflow.
This config prioritizes speed for building, sourcing,
and testing ROS 2 packages without the constant "Are you sure?" prompts.

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Read",
      "Edit",
      "LS",
      "Glob",
      "Bash(npm install*)",
      "Bash(npm test*)",
      "Bash(npm run lint*)",
      "Bash(npm start*)",
      "Bash(node --version)",
      "Bash(git status)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": false
  }
}
```

>**NOTE:** It is highly recommend to keep `"sandbox": {"enabled": true}`.
>If Claude decides to hallucinate a `rm -rf /` command while in "Accept Edits" mode,
the sandbox will catch it before it hits your actual machine.

**Example #2:**
Here is a "Safe List" for Git commands so Claude can commit and push your code automatically

**"Auto-Committer" Configuration:** This block allows Claude to check status, stage changes,
commit with messages, and push to your remote without asking for permission every single time.

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(git status)",
      "Bash(git add *)",
      "Bash(git commit -m *)",
      "Bash(git diff*)",
      "Bash(git branch*)",
      "Bash(git checkout -b *)",
      "Bash(git push *)",
      "Bash(git pull *)"
    ]
  }
}
```

What These Rules Do:
* `git add *`: Claude can stage all files or specific ones you’re working on.
* `git commit -m *`: This uses a wildcard so Claude can generate its own descriptive commit messages.
* `git push *`: **Caution!** This allows Claude to push to your current branch.
  If you are working on main or master, Claude could overwrite remote code automatically.
* `git checkout -b *`: Very useful if you want to tell Claude, "Fix this bug on a new branch called 'fix-sensor-data'."

If you're worried about Claude pushing directly to your production branch, you can omit the `git push *` line.
That way, Claude can do all the local work (add/commit), but you still have the final "Go" for the actual upload to GitHub or GitLab.

### Use Checkpoints for Fearless Experimentation
* **Amateurs** fear making big changes.
* **Pros** use checkpoints to experiment aggressively.

Claude Code automatically tracks all changes made by its file editing tools.
This safety net lets you pursue ambitious, wide-scale tasks knowing you can always return to a prior code state.

**Pro Workflow** 5 Recovery Patterns:
1. **Code-only restore:** Multi-file refactor breaks everything, but Claude understands what you’re trying to do
1. **Conversation-only restore:** Reset Claude’s context while keeping code changes
1. **Full restore:** Go back to a clean slate
1. **Branching exploration:** Try approach A, restore, try approach B
1. **Quick experimentation:** “Convert all routes to controller pattern” → Review → `/rewind` if you hate it

**Critical Limitation:**
Bash commands are NOT tracked.
If Claude runs `rm`, `mv`, or `cp`, those changes are permanent.
Checkpoints only capture edits made through Claude's file editing tools.

### Headless Mode for CI/CD Integration
* **Amateurs** use Claude only interactively.
* **Pros** integrate Claude into their automation pipelines.

Claude Code includes headless mode for non-interactive contexts like CI, pre-commit hooks, build scripts, and automation.

### Agent Skills for Domain Expertise
* **Amateurs** repeat the same instructions every session.
* **Pros** package expertise into reusable Skills.

**How Skills Work:**
1. At startup, Claude loads only the name and description of each available Skill
1. When your request matches a Skill’s description, Claude automatically loads and applies it
1. Skills operate through progressive disclosure — loading information only as needed

Agent Skills are organized folders of instructions, scripts, and resources that Claude can discover and load dynamically.
They extend Claude’s capabilities by packaging your expertise into expert resources.
Skills enforce a process that turns a smart assistant into a truly structured collaborator.
They channel the raw intelligence of your agents, ensuring every mission is executed with precision.

### Voice Prompting for Speed
* **Amateurs** type every prompt.
* **Pros** leverage voice for 3x faster input.

The average speech is about 3x the average typing speed.
Speaking is overpowered when it comes to productivity when working with a coding LLM.

**Pro Workflow:**
1. Speak your ideas using dictation software
1. Refine or expand with Claude
1. Review through text-to-speech

**Options:**
* **Wispr Flow:** Dictate prompts directly into Claude Code
* **Voicy:** Privacy-focused speech-to-text that works in any text field
* **VoiceMode MCP:** Brings natural voice conversations to Claude Code

### The Multi-Claude Orchestra
* **Amateurs** work sequentially.
* **Pros** orchestrate multiple Claude instances like a symphony.

The most advanced workflow involves running multiple Claude instances in parallel,
each serving a specific purpose.


---------------

## Claude's AskUserQuestion Tool
Instead of making assumptions and potentially going down the wrong path,
you can have Claude ask you directly what you want.
Claude can presenting clear options and gathering the context it needs to do the job right.

### Always Clean Up Your Mess
The most underrated productivity technique is aggressive context clearing.
Use `/clear` often—every time you start something new.
Don't let unrelated context from previous tasks pollute your current work.

### Interview First
Here is how it works.
Create a minimal specification file called `minimal-spec.md`
and ask Claude to interview you using `AskUserQuestionTool`.
Your prompt is given below:

```text
Read the very brief specification document @minimal-spec.md
and interview me in detail using the AskUserQuestionTool about all relevant issues.
This includes architecture, design options, technical implementation, UI and UX,
testing, languages, operating systems, development frameworks, trade-off considerations, etc.
but make sure the questions do not have obvious answers.

Be very in-depth and continue to interviewing me until you have the complete view of the situation,
then write specification you have identified to a file called project_specifications.md.
```

Or you might be in the middle of a projects development and your adding features.
The minimal specifications may be simple.
Do something like this:

```text
I want to add user authentication to my app.
Use AskUserQuestionTool to interview me and update @project_specifications.md.
```

### Spec Second
After gathering your answers,
Claude produces a detailed specification document
with a clear plan of exactly what will be built and how.

### Repeat, If Needed
You could repeat this process with AskUserQuestionTool to capture additional specification decision
that were not specified in the first iteration.

### Code Last
Start a new session with the specification as context.
Tell Claude the following:

```text
Read @project_specifications.md and implement the system.
```

---------------

## Best Workflow Ideas
Make sure to match thinking levels to task complexity.
Claude Code has built-in preprocessing that maps keywords to thinking budgets:


| Trigger | Token Budget | Use Case |
|:----|:-----:|:------|
| "think" | ~4,000 | Routine tasks, basic planning |
| "think hard" | ~10,000 | API integration, perfromance optimization |
| "think harder" | ~32,000 | Architecutre decisions, security audits |


**Mistake to Avoid** - Using "think harder" for everything burns through your API budget and slows everything down.
Think harder is a scalpel, not a hammer.

**Pro Tip** - Toggle verbose mode with `Ctrl+O`` to see Claude's thinking process displayed as gray italic text.

Claude executes with precision because all the ambiguity has been resolved upfront.
The `AskUserQuestion` tool makes this possible by front-loading all the decision-making,
resulting in a better design & code.

---------------

Claude Code Prompt:
_What are all the available Claude Code skills & tools?
Organize them as project, user, and global skills & tools._

Claude Code Prompt:
_What are some good websites where Claude SKILL.md files are available to the public?
I'm looking for well designed SKILL.md file that are user tested._


