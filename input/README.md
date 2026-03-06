# Input Files
Everything I envision for this project starts with the documentation you find in `input/`.
This directory contain the high level project description and prompts I used with Claude Code.
With the assistance of these document, Claude Code created all the code and documentation
you see in this GitHub site.

My starting point when working with Claude Code is to create a document that captures my vision for the project.
A project can be almost anything:
writing a document, building a tree house, creating a vacation plan, trouble shouting LAN networking problem,
and of course doing what Claude is best known for, building a software project.
The vision is precise in that it reference all those things that I think are must have,
or guidelines it must follow.

## My Methodology
You'll find two key documents:
* `my-vision.md` - A description of what I would like Claude Code to create for me.
  This is written in my own words, no special language or format to follow.
  I focused on giving Claude Code a clear statement on what I wanted created,
  but written as if I was instructing a knowledgable developer on what I want them to build for me.

* `my-claude-prompts.md` - These are the prompts I used with Claude Code so it could create the
  skill (e.g. `SKILL.md` files) it needs to do the project,
  and prompts to create key documents (`specification.md` and `development-plan.md`) it needed for the project.

I used a simple methodology to tease out Claude Code's help on this project,
and that is illustrated below:

```text
   SKILL.md           my-vision.md --> specification.md --> development-plan.md
      ^                    ^                 ^                     ^
      |                    |                 |                     |
      v                    v                 v                     |
  1st Claude           2nd Claude        3rd Claude         "Execute the 1st
  Code Prompt          Code Prompt       Code Prompt        step of the plan."
```

In the `my-claude-prompts.md` document, I executed the "1st Claude Code Prompt".
This created for me a very critical `SKILL.md` file.
I did this first, because I needed to empower Claude Code with this skill for subsequent steps.
The "2nd Claude Code Prompt" was used to create the `specification.md`  document,
and the "3rd Claude Code Prompt" was used to create the `development-plan.md` document.
The final prompt was trivial after the `development-plan.md` is finished;
start executing the development plan you created.

There is a little more to my methodology in that
you'll see some arrows going in two directions in the diagram above.
This denotes the fact that I iterated several time on the documents being created.
I iterated until I felt the quality and specificity of the documents where on target
before moving on to create the next document.

Also, a key observation here is important.
Claude Code doesn't require me to create a `SKILL.md` file on how to write a specifications and development plan documents.
These skills, like many others, are built in capability of Claude Code.

