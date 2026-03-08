
I'm currently working in claude code and have built a long thread of code, test scripts,  and documentation but I think I could do better.  I would like to set this work aside to but I may want to bring it back again.  How can I use git to help me do this?

## Commit what you have, then branch off fresh
This preserves everything in your current thread while letting you start clean.

```bash
# 1. Make sure you're in your project directory
git status

# 2. Stage and commit everything you want to set aside
git add -A
git commit -m "wip: save current approach before refactor"

# 3. Create a new branch for your fresh start (you'll now be on it)
git checkout -b fresh-start

# or, if you want to keep main clean and archive the old work:
git branch archive/old-approach    # label what you're setting aside
git checkout -b fresh-start        # work here going forward
```

Now your old code, tests, and docs are safely committed on your previous branch (or labeled with `archive/old-approach`),
and `fresh-start` is where you build the better version.

## To bring the old work back later

```bash
# Just look at it
git checkout archive/old-approach

# Cherry-pick a specific file back into your new work
git checkout fresh-start
git checkout archive/old-approach -- path/to/specific_file.py

# Or diff the two branches to compare
git diff fresh-start archive/old-approach
```

## naming conventions
few branch prefixes that keep things organized as work accumulates:

* `archive/` — things set aside, may return
* `wip/` — active work in progress
* `experiment/` — speculative, might be thrown away

This way you never lose work, Git becomes your unlimited undo across entire approaches,
and Claude Code can see any branch you check out.
