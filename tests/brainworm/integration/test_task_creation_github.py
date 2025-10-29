"""
Integration tests for task creation with GitHub integration.

Tests the end-to-end workflow of creating tasks with GitHub issue linking.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add brainworm to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "brainworm"))


class TestTaskCreationWithGitHub:
    """Integration tests for task creation with GitHub flags"""

    def test_pattern_matching_extracts_issue_number(self):
        """Should extract issue number from task name pattern"""
        from utils.github_integration import extract_issue_number_from_task_name

        # Test various patterns
        assert extract_issue_number_from_task_name("fix-bug-#123") == 123
        assert extract_issue_number_from_task_name("implement-feature-#456") == 456
        assert extract_issue_number_from_task_name("task-#789-with-suffix") == 789
        assert extract_issue_number_from_task_name("no-issue-here") is None

    @patch('subprocess.run')
    def test_task_creation_updates_frontmatter(self, mock_run):
        """Should update task frontmatter with GitHub metadata when linking"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Setup task structure
            (project_root / ".brainworm" / "tasks" / "test-task").mkdir(parents=True)
            task_file = project_root / ".brainworm" / "tasks" / "test-task" / "README.md"

            # Create task file with frontmatter
            task_file.write_text("""---
task: test-task
branch: main
github_issue: null
github_repo: null
---

# Test Task
""")

            # Test link_issue_to_task
            from utils.github_integration import link_issue_to_task

            success = link_issue_to_task(task_file, 123, "owner/repo")
            assert success is True

            # Verify frontmatter was updated
            content = task_file.read_text()
            assert "github_issue: 123" in content
            assert "github_repo: owner/repo" in content
            assert "# Test Task" in content  # Body preserved


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
