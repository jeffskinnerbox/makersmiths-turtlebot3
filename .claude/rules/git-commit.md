# Git Commitment Guidelines

Whenever you perform a git commit, you MUST follow the industry standard Conventional Commits specification.

1. **Format**: Use the structure: `<type>(<scope>): <description>`
   - Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert.
   - Scope: The specific module (e.g., lidar, navigation, gazebo, sbc).
2. **Subject Line**:
   - Use the imperative mood ("Add feature" not "Added feature").
   - Max 50 characters.
   - No period at the end.
3. **Body**:
   - If the change is complex, include a blank line and a bulleted list of changes.
   - Focus on the "why" behind the change, not just the "what."
4. **Constraints**:
   - NEVER use generic messages like "update files" or "fix bug."
   - If you are unsure of the scope, omit it: `feat: add laser scan filter`.
5. **Auto-Summarization**:
   - Before committing, always run `git diff --cached` to review your changes
     and ensure the commit message accurately reflects every modified line.

