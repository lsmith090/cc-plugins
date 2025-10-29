"""
GitHub Integration for Brainworm Tasks

Provides GitHub CLI integration for:
- Repository detection
- Issue linking and creation
- Session summary posting
- Context fetching

All operations use gh CLI and degrade gracefully if unavailable.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()


def check_gh_available() -> bool:
    """
    Check if gh CLI is installed and authenticated.

    Returns:
        bool: True if gh is available and authenticated, False otherwise
    """
    try:
        # Check if gh is installed
        result = subprocess.run(["gh", "--version"], capture_output=True, timeout=5)
        if result.returncode != 0:
            return False

        # Check if authenticated
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, timeout=5)
        return result.returncode == 0

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def detect_github_repo(project_root: Path, submodule: Optional[str] = None) -> Optional[str]:
    """
    Detect GitHub repository for project or submodule.

    Uses gh CLI first (handles auth and multi-remote correctly),
    falls back to parsing git remote.

    Args:
        project_root: Project root path
        submodule: Submodule name (if detecting repo for submodule)

    Returns:
        Repository in "owner/repo" format, or None if not GitHub or error
    """
    # Determine working directory
    if submodule:
        from .git_submodule_manager import SubmoduleManager

        sm = SubmoduleManager(project_root)
        cwd = sm.get_submodule_path(submodule)
        if not cwd:
            return None
    else:
        cwd = project_root

    # Try gh CLI first (preferred)
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: parse git remote
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"], cwd=cwd, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            remote_url = result.stdout.strip()

            # Parse GitHub URLs
            # SSH: git@github.com:owner/repo.git
            # HTTPS: https://github.com/owner/repo.git
            patterns = [r"git@github\.com:([^/]+)/(.+?)(?:\.git)?$", r"https://github\.com/([^/]+)/(.+?)(?:\.git)?$"]

            for pattern in patterns:
                match = re.match(pattern, remote_url)
                if match:
                    owner, repo = match.groups()
                    return f"{owner}/{repo}"

    except subprocess.TimeoutExpired:
        pass

    return None


def link_issue_to_task(task_file: Path, issue_number: int, repo: str) -> bool:
    """
    Add GitHub issue metadata to task file frontmatter.

    Updates the YAML frontmatter in the task README with:
    - github_issue: issue number
    - github_repo: owner/repo format

    Args:
        task_file: Path to task README.md
        issue_number: GitHub issue number
        repo: Repository in "owner/repo" format

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not task_file.exists():
            console.print(f"[red]Task file not found: {task_file}[/red]")
            return False

        content = task_file.read_text()

        # Parse frontmatter (YAML between --- markers)
        lines = content.split("\n")
        if not (lines and lines[0] == "---"):
            console.print("[red]Invalid task file: no frontmatter found[/red]")
            return False

        # Find end of frontmatter
        end_idx = None
        for i in range(1, len(lines)):
            if lines[i] == "---":
                end_idx = i
                break

        if end_idx is None:
            console.print("[red]Invalid task file: frontmatter not closed[/red]")
            return False

        # Update or add github fields
        frontmatter_lines = lines[1:end_idx]
        updated_frontmatter = []
        github_issue_set = False
        github_repo_set = False

        for line in frontmatter_lines:
            if line.startswith("github_issue:"):
                updated_frontmatter.append(f"github_issue: {issue_number}")
                github_issue_set = True
            elif line.startswith("github_repo:"):
                updated_frontmatter.append(f"github_repo: {repo}")
                github_repo_set = True
            else:
                updated_frontmatter.append(line)

        # Add fields if they didn't exist
        if not github_issue_set:
            updated_frontmatter.append(f"github_issue: {issue_number}")
        if not github_repo_set:
            updated_frontmatter.append(f"github_repo: {repo}")

        # Reconstruct file
        new_content = "\n".join(["---", *updated_frontmatter, "---", *lines[end_idx + 1 :]])

        # Atomic write
        task_file.write_text(new_content)
        return True

    except Exception as e:
        console.print(f"[red]Error updating task file: {e}[/red]")
        return False


def create_github_issue(repo: str, title: str, body: str, labels: Optional[List[str]] = None) -> Optional[int]:
    """
    Create GitHub issue and return issue number.

    Args:
        repo: Repository in "owner/repo" format
        title: Issue title
        body: Issue body/description
        labels: Optional list of label names

    Returns:
        int: Issue number if successful, None otherwise
    """
    try:
        cmd = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body]

        if labels:
            cmd.extend(["--label", ",".join(labels)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            # Parse issue URL from output
            # Output format: "https://github.com/owner/repo/issues/123"
            match = re.search(r"/issues/(\d+)", result.stdout)
            if match:
                return int(match.group(1))

        console.print(f"[yellow]Failed to create issue: {result.stderr}[/yellow]")
        return None

    except subprocess.TimeoutExpired:
        console.print("[yellow]Timeout creating GitHub issue[/yellow]")
        return None
    except Exception as e:
        console.print(f"[yellow]Error creating issue: {e}[/yellow]")
        return None


def fetch_issue_context(repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
    """
    Fetch issue details from GitHub.

    Args:
        repo: Repository in "owner/repo" format
        issue_number: Issue number

    Returns:
        Dict with issue details (title, body, state, labels), or None on error
    """
    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_number), "--repo", repo, "--json", "title,body,state,labels"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            return json.loads(result.stdout)

        return None

    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        console.print(f"[yellow]Error fetching issue context: {e}[/yellow]")
        return None


def post_issue_comment(repo: str, issue_number: int, comment: str) -> bool:
    """
    Post comment to GitHub issue.

    Args:
        repo: Repository in "owner/repo" format
        issue_number: Issue number
        comment: Comment text (markdown supported)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            ["gh", "issue", "comment", str(issue_number), "--repo", repo, "--body", comment],
            capture_output=True,
            text=True,
            timeout=15,
        )

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        console.print("[yellow]Timeout posting issue comment[/yellow]")
        return False
    except Exception as e:
        console.print(f"[yellow]Error posting comment: {e}[/yellow]")
        return False


def extract_issue_number_from_task_name(task_name: str) -> Optional[int]:
    """
    Extract issue number from task name if present.

    Looks for patterns like:
    - implement-feature-#123
    - fix-bug-#456
    - task-name-#789

    Args:
        task_name: Task name

    Returns:
        int: Issue number if found, None otherwise
    """
    match = re.search(r"#(\d+)", task_name)
    if match:
        return int(match.group(1))
    return None


def find_session_memory(project_root: Path, session_id: str) -> Optional[Path]:
    """
    Find memory file for given session_id.

    Searches .brainworm/memory/*.md files for matching session ID.

    Args:
        project_root: Project root path
        session_id: Session ID to find (8-char or full UUID)

    Returns:
        Path to memory file if found, None otherwise
    """
    memory_dir = project_root / ".brainworm" / "memory"

    if not memory_dir.exists():
        return None

    # Get session prefix (first 8 chars for matching)
    session_short = session_id[:8] if len(session_id) >= 8 else session_id

    # Search all markdown files in memory directory
    for memory_file in memory_dir.glob("*.md"):
        try:
            content = memory_file.read_text()
            # Look for session ID pattern: **Session ID**: {session_id}
            if re.search(rf"\*\*Session ID\*\*:\s*{re.escape(session_short)}", content):
                return memory_file
        except Exception:
            continue

    return None


def parse_memory_for_summary(memory_file: Path) -> Dict[str, str]:
    """
    Extract key sections from memory file for GitHub summary.

    Parses markdown sections:
    - Development Insights
    - Code Areas Active
    - Next Development Directions

    Args:
        memory_file: Path to memory markdown file

    Returns:
        Dict with extracted sections (keys: insights, code_areas, next_steps)
    """
    try:
        content = memory_file.read_text()
        sections = {"insights": "", "code_areas": "", "next_steps": ""}

        # Parse markdown by sections
        lines = content.split("\n")
        current_section = None
        section_content = []

        for line in lines:
            # Detect section headers
            if line.startswith("## Development Insights"):
                if current_section and section_content:
                    sections[current_section] = "\n".join(section_content).strip()
                current_section = "insights"
                section_content = []
            elif line.startswith("## Code Areas Active"):
                if current_section and section_content:
                    sections[current_section] = "\n".join(section_content).strip()
                current_section = "code_areas"
                section_content = []
            elif line.startswith("## Next Development Directions"):
                if current_section and section_content:
                    sections[current_section] = "\n".join(section_content).strip()
                current_section = "next_steps"
                section_content = []
            elif line.startswith("##"):
                # Different section, stop collecting
                if current_section and section_content:
                    sections[current_section] = "\n".join(section_content).strip()
                current_section = None
                section_content = []
            elif current_section:
                # Collect content for current section
                section_content.append(line)

        # Capture last section
        if current_section and section_content:
            sections[current_section] = "\n".join(section_content).strip()

        return sections

    except Exception as e:
        console.print(f"[yellow]Error parsing memory file: {e}[/yellow]")
        return {"insights": "", "code_areas": "", "next_steps": ""}


def generate_github_summary_from_memory(memory_file: Path, session_id: str, task_name: str, branch: str) -> str:
    """
    Generate formatted GitHub comment from memory file.

    Args:
        memory_file: Path to session memory file
        session_id: Session ID
        task_name: Current task name
        branch: Current branch

    Returns:
        str: Formatted markdown summary for GitHub
    """
    session_short = session_id[:8] if len(session_id) >= 8 else session_id
    sections = parse_memory_for_summary(memory_file)

    # Build summary
    summary_parts = [f"**Session `{session_short}` Summary**", "", f"Task: `{task_name}`", f"Branch: `{branch}`", ""]

    # Add Development Insights if present
    if sections["insights"]:
        summary_parts.extend(["## Development Insights", sections["insights"], ""])

    # Add Code Areas if present
    if sections["code_areas"]:
        summary_parts.extend(["## Code Changes", sections["code_areas"], ""])

    # Add Next Steps if present
    if sections["next_steps"]:
        summary_parts.extend(["## Next Steps", sections["next_steps"], ""])

    # Footer
    summary_parts.extend(
        [
            "---",
            f"Session ID: `{session_id}`",
            f"Memory: `{memory_file.name}`",
            "",
            "🪱 Generated with brainworm task management",
        ]
    )

    return "\n".join(summary_parts)
