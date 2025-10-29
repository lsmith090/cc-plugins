"""
Unit tests for GitHub integration utilities.

Tests core functions for GitHub CLI integration including:
- Issue number extraction from task names
- Task file frontmatter updates
- GitHub repository detection
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the functions we're testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "brainworm"))

from utils.github_integration import (
    detect_github_repo,
    extract_issue_number_from_task_name,
    link_issue_to_task,
)


class TestExtractIssueNumber:
    """Tests for extract_issue_number_from_task_name()"""

    def test_extract_single_issue_number(self):
        """Should extract issue number from task name with #123 pattern"""
        assert extract_issue_number_from_task_name("fix-bug-#123") == 123
        assert extract_issue_number_from_task_name("implement-feature-#456") == 456
        assert extract_issue_number_from_task_name("refactor-code-#789") == 789

    def test_extract_no_issue_number(self):
        """Should return None when no issue number present"""
        assert extract_issue_number_from_task_name("no-issue-here") is None
        assert extract_issue_number_from_task_name("implement-feature") is None
        assert extract_issue_number_from_task_name("fix-bug") is None

    def test_extract_first_issue_number_from_multiple(self):
        """Should extract first issue number when multiple present"""
        assert extract_issue_number_from_task_name("task-#123-and-#456") == 123
        assert extract_issue_number_from_task_name("merge-#999-into-#888") == 999

    def test_extract_issue_at_different_positions(self):
        """Should extract issue number regardless of position"""
        assert extract_issue_number_from_task_name("#123-at-start") == 123
        assert extract_issue_number_from_task_name("at-end-#456") == 456
        assert extract_issue_number_from_task_name("in-#789-middle") == 789


class TestLinkIssueToTask:
    """Tests for link_issue_to_task()"""

    def test_link_issue_updates_existing_fields(self):
        """Should update existing github_issue and github_repo fields"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
task: test-task
branch: main
github_issue: null
github_repo: null
---

# Task Content
""")
            task_file = Path(f.name)

        try:
            result = link_issue_to_task(task_file, 123, "owner/repo")
            assert result is True

            content = task_file.read_text()
            assert "github_issue: 123" in content
            assert "github_repo: owner/repo" in content
            assert "# Task Content" in content  # Preserves body
        finally:
            task_file.unlink()

    def test_link_issue_adds_missing_fields(self):
        """Should add github fields if not present in frontmatter"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
task: test-task
branch: main
---

# Task Content
""")
            task_file = Path(f.name)

        try:
            result = link_issue_to_task(task_file, 456, "user/project")
            assert result is True

            content = task_file.read_text()
            assert "github_issue: 456" in content
            assert "github_repo: user/project" in content
        finally:
            task_file.unlink()

    def test_link_issue_preserves_other_frontmatter(self):
        """Should preserve all other frontmatter fields"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
task: test-task
branch: feature/test
status: pending
created: 2025-10-29
github_issue: null
github_repo: null
---

# Task
""")
            task_file = Path(f.name)

        try:
            result = link_issue_to_task(task_file, 789, "org/repo")
            assert result is True

            content = task_file.read_text()
            # Check preserved fields
            assert "task: test-task" in content
            assert "branch: feature/test" in content
            assert "status: pending" in content
            assert "created: 2025-10-29" in content
            # Check updated fields
            assert "github_issue: 789" in content
            assert "github_repo: org/repo" in content
        finally:
            task_file.unlink()

    def test_link_issue_handles_malformed_frontmatter_gracefully(self):
        """Should return False for malformed frontmatter"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# No frontmatter here")
            task_file = Path(f.name)

        try:
            result = link_issue_to_task(task_file, 123, "owner/repo")
            assert result is False
        finally:
            task_file.unlink()

    def test_link_issue_handles_nonexistent_file(self):
        """Should return False for nonexistent file"""
        nonexistent = Path("/tmp/nonexistent_task_file.md")
        result = link_issue_to_task(nonexistent, 123, "owner/repo")
        assert result is False


class TestDetectGithubRepo:
    """Tests for detect_github_repo()"""

    @patch('subprocess.run')
    def test_detect_repo_ssh_format(self, mock_run):
        """Should parse SSH format git remote"""
        def run_side_effect(*args, **kwargs):
            """Mock both gh CLI (fails) and git remote (succeeds with SSH)"""
            cmd = args[0]
            mock_result = MagicMock()
            if cmd[0] == 'gh':
                # gh CLI not available
                mock_result.returncode = 1
                mock_result.stdout = ""
            elif cmd[0] == 'git' and 'remote' in cmd:
                # git remote returns SSH URL
                mock_result.returncode = 0
                mock_result.stdout = "git@github.com:owner/repo.git\n"
            else:
                mock_result.returncode = 1
                mock_result.stdout = ""
            return mock_result

        mock_run.side_effect = run_side_effect

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            result = detect_github_repo(project_root)
            assert result == "owner/repo"

    @patch('subprocess.run')
    def test_detect_repo_https_format(self, mock_run):
        """Should parse HTTPS format git remote"""
        def run_side_effect(*args, **kwargs):
            """Mock both gh CLI (fails) and git remote (succeeds with HTTPS)"""
            cmd = args[0]
            mock_result = MagicMock()
            if cmd[0] == 'gh':
                mock_result.returncode = 1
                mock_result.stdout = ""
            elif cmd[0] == 'git' and 'remote' in cmd:
                mock_result.returncode = 0
                mock_result.stdout = "https://github.com/user/project.git\n"
            else:
                mock_result.returncode = 1
                mock_result.stdout = ""
            return mock_result

        mock_run.side_effect = run_side_effect

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            result = detect_github_repo(project_root)
            assert result == "user/project"

    @patch('subprocess.run')
    def test_detect_repo_without_git_extension(self, mock_run):
        """Should handle URLs without .git extension"""
        def run_side_effect(*args, **kwargs):
            """Mock both gh CLI (fails) and git remote (succeeds without .git)"""
            cmd = args[0]
            mock_result = MagicMock()
            if cmd[0] == 'gh':
                mock_result.returncode = 1
                mock_result.stdout = ""
            elif cmd[0] == 'git' and 'remote' in cmd:
                mock_result.returncode = 0
                mock_result.stdout = "https://github.com/org/repo\n"
            else:
                mock_result.returncode = 1
                mock_result.stdout = ""
            return mock_result

        mock_run.side_effect = run_side_effect

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            result = detect_github_repo(project_root)
            assert result == "org/repo"

    @patch('subprocess.run')
    def test_detect_repo_non_github_remote(self, mock_run):
        """Should return None for non-GitHub remotes"""
        def run_side_effect(*args, **kwargs):
            """Mock both gh CLI (fails) and git remote (GitLab URL)"""
            cmd = args[0]
            mock_result = MagicMock()
            if cmd[0] == 'gh':
                mock_result.returncode = 1
                mock_result.stdout = ""
            elif cmd[0] == 'git' and 'remote' in cmd:
                mock_result.returncode = 0
                mock_result.stdout = "https://gitlab.com/user/project.git\n"
            else:
                mock_result.returncode = 1
                mock_result.stdout = ""
            return mock_result

        mock_run.side_effect = run_side_effect

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            result = detect_github_repo(project_root)
            assert result is None

    @patch('subprocess.run')
    def test_detect_repo_git_command_failure(self, mock_run):
        """Should return None when git command fails"""
        def run_side_effect(*args, **kwargs):
            """Mock both gh CLI and git remote failing"""
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            return mock_result

        mock_run.side_effect = run_side_effect

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            result = detect_github_repo(project_root)
            assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
