# GitHub Integration Reference

This document provides technical details about brainworm's GitHub integration for task management.

## Overview

The brainworm task system integrates with GitHub Issues to enable seamless tracking of development work. Tasks can be linked to existing issues or create new ones automatically.

## Configuration

GitHub integration is controlled by `.brainworm/config.toml`:

```toml
[github]
enabled = true
create_issue_on_task = false  # Auto-create issues for new tasks
```

## Prerequisites

1. **GitHub CLI (`gh`)**: Must be installed and authenticated
   ```bash
   gh auth status
   ```

2. **Git repository**: Project must be a git repository with GitHub remote

3. **Permissions**: User must have write access to repository for issue creation

## Auto-Linking via Task Names

The most natural integration pattern is embedding issue numbers in task names:

```bash
./tasks create fix-authentication-#42
./tasks create add-logging-#123
./tasks create refactor-api-#456
```

**How it works**:
- Pattern: `r"#(\d+)"` extracts issue numbers from task names
- First occurrence is used if multiple numbers present
- Issue number validated against GitHub (checks if issue exists)
- Stored in task frontmatter: `github_issue: 42`

## Explicit Issue Linking

Link to any issue number explicitly:

```bash
./tasks create implement-feature --link-issue=123
```

This overrides any auto-detected issue number from the task name.

## Creating New Issues

Create a GitHub issue automatically when creating a task:

```bash
./tasks create implement-login --create-issue
```

**What happens**:
1. Task directory created as normal
2. `gh issue create` invoked with:
   - Title: Task name (human-readable format)
   - Body: "Task created via brainworm"
3. Issue URL returned: `https://github.com/owner/repo/issues/N`
4. Issue number extracted from URL
5. Task frontmatter updated with issue number and repo

**Configuration**: Set `create_issue_on_task = true` in config to make this the default behavior.

## Repository Detection

The system automatically detects the GitHub repository:

**Method 1: gh CLI**
```bash
gh repo view --json nameWithOwner
```

Returns: `{"nameWithOwner": "owner/repo"}`

**Method 2: Git remote parsing** (fallback)
```bash
git remote get-url origin
```

Patterns matched:
- SSH: `git@github.com:owner/repo.git`
- HTTPS: `https://github.com/owner/repo.git`
- HTTPS (no .git): `https://github.com/owner/repo`

**Submodule handling**: For submodule tasks, detection runs in submodule directory

## Frontmatter Storage

Issue information is stored in task README frontmatter:

```yaml
---
task: fix-authentication-bug
github_issue: 42
github_repo: lsmith090/my-project
---
```

**Atomic updates**: Frontmatter is parsed, updated, and rewritten atomically to prevent corruption.

## Session Summaries

When tasks complete, brainworm can post session summaries to linked issues:

```bash
./tasks summarize
```

**What's included**:
- Session memory from `.brainworm/memory/`
- Work log entries from task README
- Key decisions and discoveries
- Implementation details

This creates a permanent record on the GitHub issue of what was accomplished.

## Issue Context Fetching

When starting a task linked to an issue, you can fetch issue context:

```bash
gh issue view <issue-number> --repo <owner/repo>
```

The context-gathering agent can read this to understand:
- Issue description and goals
- Comments and discussion
- Labels and assignments
- Related PRs

## Multi-Service Projects

In multi-service (monorepo) projects:
- Repository detection runs in submodule context if task is submodule-scoped
- Each service can link to issues in different repos
- Task frontmatter stores the specific repo for each task

## Error Handling

**Issue doesn't exist**:
- Error message: "Issue #N not found in owner/repo"
- Task creation continues without link
- User can manually add link later

**No GitHub access**:
- Error message: "GitHub CLI not authenticated"
- Task creation continues without GitHub integration
- All local task features still work

**Issue creation fails**:
- Error logged to `.brainworm/logs/debug.jsonl`
- Task creation completes without issue link
- User can create issue manually later

## Best Practices

1. **Use auto-linking**: Embed issue numbers in task names for seamless tracking

2. **Link before you start**: When starting work on an issue, create the task with the link immediately

3. **Summarize when done**: Use `./tasks summarize` to post completion summary to issue

4. **Check permissions**: Verify `gh auth status` before creating issues

5. **Consistent naming**: Use descriptive task names that make sense as issue titles

## Security Considerations

- **Authentication**: Uses gh CLI's authentication, never stores credentials
- **Permissions**: Respects GitHub repository permissions
- **Rate limits**: Issue operations count against GitHub API rate limits
- **Private repos**: Fully supported if user has access

## Implementation Details

**Source files**:
- `brainworm/utils/github_manager.py` - Core GitHub operations
- `brainworm/scripts/create_task.py` - Task creation with GitHub integration
- `brainworm/scripts/list_tasks.py` - Session summarization

**Key functions**:
- `detect_github_repo(project_root, submodule)` - Repository detection
- `extract_issue_number_from_task_name(task_name)` - Auto-linking
- `link_issue_to_task(task_readme, issue_number, repo)` - Frontmatter updates
- `create_github_issue(title, body, repo)` - Issue creation
- `generate_session_summary(task_readme)` - Summary generation

## Troubleshooting

**"GitHub CLI not found"**:
- Install: `brew install gh` (macOS) or equivalent
- Verify: `which gh`

**"Not authenticated"**:
- Run: `gh auth login`
- Follow prompts for authentication

**"Issue not found"**:
- Verify issue exists in repository
- Check issue number is correct
- Confirm you have read access to repository

**"Cannot create issue"**:
- Verify write access to repository
- Check repository settings allow issues
- Confirm you're authenticated

## Future Enhancements

Potential future features:
- Automatic PR creation when task completes
- Issue status synchronization (update issue when task progresses)
- Label management (apply labels based on task type)
- Assignment automation (assign issue to authenticated user)
- Milestone linking (associate tasks with milestones)
