#!/usr/bin/env python3
"""
Hook Dependency Validation Tests

Validates that PEP 723 inline script dependencies are complete and correct.
This prevents runtime ImportErrors by ensuring all imports have corresponding
dependency declarations.

Test Coverage:
- All imports have declared dependencies
- No unused dependencies (warnings only)
- Hooks can execute with uv run --isolated
- No system packages leak into hook execution
"""

import ast
import re
import subprocess
import json
from pathlib import Path
from typing import Set, Dict, List
import pytest


class DependencyValidator:
    """Validates PEP 723 inline dependencies match actual imports"""

    # Mapping of import names to package names
    IMPORT_TO_PACKAGE = {
        'rich': 'rich',
        'tomli_w': 'tomli-w',
        'filelock': 'filelock',
        'typer': 'typer',
        # Add more mappings as needed
    }

    # Packages that may be used indirectly (transitive dependencies)
    ALLOWED_TRANSITIVE = {'tomli-w'}  # Used by hook_framework

    @staticmethod
    def extract_inline_dependencies(script_path: Path) -> Set[str]:
        """
        Extract dependencies from PEP 723 script metadata.

        Args:
            script_path: Path to Python script with inline metadata

        Returns:
            Set of package names declared in dependencies
        """
        content = script_path.read_text()

        # Parse PEP 723 metadata block
        metadata_pattern = r'# /// script\n(.*?)# ///'
        match = re.search(metadata_pattern, content, re.DOTALL)

        if not match:
            return set()

        metadata_block = match.group(1)

        # Extract package names from dependencies list
        # Handles formats like: "rich>=13.0.0", "tomli-w>=1.0.0"
        dep_pattern = r'"([a-zA-Z0-9_-]+)(?:[><=!~].*?)?"'
        return set(re.findall(dep_pattern, metadata_block))

    @staticmethod
    def extract_imports(script_path: Path) -> Set[str]:
        """
        Extract all import statements from Python file using AST.

        Args:
            script_path: Path to Python script

        Returns:
            Set of top-level package names imported
        """
        content = script_path.read_text()

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {script_path}: {e}")

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get top-level package name
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])

        return imports

    @staticmethod
    def get_stdlib_modules() -> Set[str]:
        """
        Get set of Python 3.12+ standard library modules.

        Returns:
            Set of stdlib module names
        """
        return {
            'sys', 'os', 'json', 'pathlib', 'typing', 're', 'datetime',
            'collections', 'itertools', 'functools', 'subprocess', 'io',
            'tempfile', 'shutil', 'logging', 'unittest', 'sqlite3',
            'contextlib', 'dataclasses', 'enum', 'time', 'uuid', 'hashlib',
            'argparse', 'traceback', 'importlib', 'inspect', 'ast',
            'warnings', 'weakref', 'copy', 'pickle', 'base64', 'hmac',
            'secrets', 'string', 'textwrap', 'unicodedata', 'html',
            'xml', 'email', 'http', 'urllib', 'socket', 'select',
            'asyncio', 'concurrent', 'threading', 'multiprocessing',
            'queue', 'signal', 'abc', 'types', 'operator', 'builtins',
            # Add more as needed
        }

    @classmethod
    def get_brainworm_internal_modules(cls) -> Set[str]:
        """
        Get set of brainworm internal module names.

        These are local imports that don't require package declarations.

        Returns:
            Set of internal module names
        """
        return {
            'utils', 'hooks', 'scripts', 'agents', 'protocols',
            'brainworm'  # For brainworm.utils.* imports
        }


@pytest.fixture
def brainworm_hooks_dir() -> Path:
    """Get path to brainworm hooks directory"""
    # Navigate from tests/brainworm/integration/ to brainworm/hooks/
    test_file = Path(__file__)
    repo_root = test_file.parent.parent.parent.parent
    hooks_dir = repo_root / "brainworm" / "hooks"

    if not hooks_dir.exists():
        pytest.skip(f"Hooks directory not found: {hooks_dir}")

    return hooks_dir


@pytest.fixture
def hook_scripts(brainworm_hooks_dir) -> List[Path]:
    """Get all hook scripts with inline metadata"""
    scripts = []
    for script in brainworm_hooks_dir.glob("*.py"):
        content = script.read_text()
        if content.startswith("#!/usr/bin/env") and "# /// script" in content:
            scripts.append(script)

    return scripts


@pytest.mark.integration
class TestHookDependencies:
    """Validate hook script dependencies are complete and correct"""

    def test_all_imports_have_declared_dependencies(self, hook_scripts):
        """
        Verify all third-party imports are declared in dependencies.

        This catches missing dependency declarations that would cause
        ImportError in production.
        """
        validator = DependencyValidator()
        stdlib = validator.get_stdlib_modules()
        internal = validator.get_brainworm_internal_modules()

        failures = []

        for script in hook_scripts:
            imports = validator.extract_imports(script)
            declared = validator.extract_inline_dependencies(script)

            # Filter to third-party imports only
            third_party = {
                imp for imp in imports
                if imp not in stdlib and imp not in internal
            }

            # Check each third-party import has a declared dependency
            for imp in third_party:
                package = validator.IMPORT_TO_PACKAGE.get(imp, imp)

                if package not in declared:
                    failures.append(
                        f"{script.name}: imports '{imp}' (package '{package}') "
                        f"but doesn't declare it in dependencies.\n"
                        f"  Declared: {sorted(declared)}\n"
                        f"  Third-party imports: {sorted(third_party)}"
                    )

        if failures:
            pytest.fail(
                "\n\nMissing dependency declarations found:\n\n" +
                "\n\n".join(failures) +
                "\n\nAdd missing dependencies to the # /// script block."
            )

    def test_no_unused_dependencies(self, hook_scripts):
        """
        Warn about declared dependencies that aren't imported.

        This is informational only - some dependencies may be transitive
        or used indirectly.
        """
        validator = DependencyValidator()

        warnings = []

        for script in hook_scripts:
            imports = validator.extract_imports(script)
            declared = validator.extract_inline_dependencies(script)

            for dep in declared:
                if dep in validator.ALLOWED_TRANSITIVE:
                    continue

                # Convert package name to import name
                import_name = dep.replace('-', '_')

                if import_name not in imports:
                    warnings.append(
                        f"{script.name}: declares dependency '{dep}' "
                        f"but doesn't import it"
                    )

        if warnings:
            # This is a warning, not a failure
            print("\n\nWarning: Potentially unused dependencies:\n")
            for warning in warnings:
                print(f"  - {warning}")


@pytest.mark.integration
class TestHookExecution:
    """Test hooks can actually execute with declared dependencies"""

    def test_hooks_have_inline_metadata(self, brainworm_hooks_dir):
        """Verify all hooks have PEP 723 inline metadata"""
        hooks_without_metadata = []

        for script in brainworm_hooks_dir.glob("*.py"):
            if script.name.startswith("_"):
                continue  # Skip __init__.py, etc.

            content = script.read_text()
            if "# /// script" not in content:
                hooks_without_metadata.append(script.name)

        if hooks_without_metadata:
            pytest.fail(
                f"Hooks missing PEP 723 metadata: {hooks_without_metadata}\n"
                f"Add # /// script block with dependencies"
            )

    def test_hook_executes_with_uv_run(self, brainworm_hooks_dir, tmp_path):
        """
        Verify pre_tool_use hook executes successfully with uv run.

        This tests that the hook can actually run with its declared
        dependencies, catching missing transitive dependencies.
        """
        hook_script = brainworm_hooks_dir / "pre_tool_use.py"

        if not hook_script.exists():
            pytest.skip("pre_tool_use.py not found")

        # Create minimal .brainworm structure
        brainworm_dir = tmp_path / ".brainworm"
        brainworm_dir.mkdir()
        (brainworm_dir / "state").mkdir()
        (brainworm_dir / "config.toml").write_text(
            "[daic]\nenabled = false\n"
        )

        # Create minimal state file
        state_file = brainworm_dir / "state" / "unified_session_state.json"
        state_file.write_text(json.dumps({
            "daic_mode": "implementation",
            "session_id": "test-session",
            "plugin_root": str(brainworm_hooks_dir.parent)
        }))

        # Create minimal test input
        test_input = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/test/file.py"},
            "project_root": str(tmp_path),
            "session_id": "test-session",
            "correlation_id": "test-corr-001"
        }

        # Execute with uv run
        result = subprocess.run(
            ["uv", "run", str(hook_script)],
            input=json.dumps(test_input).encode(),
            capture_output=True,
            timeout=10,
            cwd=tmp_path
        )

        # Check for import errors specifically
        stderr = result.stderr.decode()

        # Should not have module/import errors
        assert "ModuleNotFoundError" not in stderr, (
            f"Missing dependency in {hook_script.name}:\n{stderr}"
        )
        assert "ImportError" not in stderr, (
            f"Import error in {hook_script.name}:\n{stderr}"
        )
        assert "cannot import name" not in stderr, (
            f"Import error in {hook_script.name}:\n{stderr}"
        )

        # Hook should execute without crashing (return code 0 or 1 is OK)
        # 1 might occur if validation fails, but shouldn't be import error
        if result.returncode not in [0, 1]:
            pytest.fail(
                f"Hook failed with unexpected error (code {result.returncode}):\n"
                f"stdout: {result.stdout.decode()}\n"
                f"stderr: {stderr}"
            )

    @pytest.mark.parametrize("hook_name", [
        "pre_tool_use.py",
        "post_tool_use.py",
        "session_start.py",
        "user_prompt_submit.py",
        "session_end.py",
        "stop.py",
        "notification.py"
    ])
    def test_all_hooks_can_import(self, brainworm_hooks_dir, tmp_path, hook_name):
        """
        Test all major hooks can execute without import errors.

        This is a smoke test to catch basic import issues across
        all hook types.
        """
        hook_script = brainworm_hooks_dir / hook_name

        if not hook_script.exists():
            pytest.skip(f"{hook_name} not found")

        # Create minimal project structure
        brainworm_dir = tmp_path / ".brainworm"
        brainworm_dir.mkdir()
        (brainworm_dir / "state").mkdir()
        (brainworm_dir / "config.toml").write_text("[daic]\nenabled = false\n")
        (brainworm_dir / "state" / "unified_session_state.json").write_text(
            json.dumps({"plugin_root": str(brainworm_hooks_dir.parent)})
        )

        # Execute with minimal input (will likely fail, but shouldn't have import errors)
        result = subprocess.run(
            ["uv", "run", str(hook_script)],
            input=b"{}",
            capture_output=True,
            timeout=10,
            cwd=tmp_path
        )

        stderr = result.stderr.decode()

        # Should not have import errors
        assert "ModuleNotFoundError" not in stderr, (
            f"{hook_name} has missing dependency:\n{stderr}"
        )
        assert "cannot import name" not in stderr, (
            f"{hook_name} has import error:\n{stderr}"
        )


@pytest.mark.integration
@pytest.mark.slow
class TestHookIsolation:
    """Verify hooks work in isolated environments without system packages"""

    def test_hook_in_clean_environment(self, brainworm_hooks_dir, tmp_path):
        """
        Execute hook in isolated uv environment.

        This ensures hooks don't accidentally depend on system-installed
        packages that aren't in their dependency declarations.
        """
        hook_script = brainworm_hooks_dir / "pre_tool_use.py"

        if not hook_script.exists():
            pytest.skip("pre_tool_use.py not found")

        # Create minimal project structure
        project = tmp_path / "isolated_project"
        project.mkdir()
        brainworm = project / ".brainworm"
        brainworm.mkdir()
        (brainworm / "state").mkdir()
        (brainworm / "config.toml").write_text("[daic]\nenabled = false\n")
        (brainworm / "state" / "unified_session_state.json").write_text(
            json.dumps({"plugin_root": str(brainworm_hooks_dir.parent)})
        )

        test_input = {
            "tool_name": "Read",
            "tool_input": {},
            "project_root": str(project),
            "session_id": "test",
            "correlation_id": "test"
        }

        # Execute with --isolated flag to ensure clean environment
        result = subprocess.run(
            ["uv", "run", "--isolated", str(hook_script)],
            input=json.dumps(test_input).encode(),
            capture_output=True,
            cwd=project,
            timeout=15  # Isolated mode may be slower
        )

        # Should work with only declared dependencies
        stderr = result.stderr.decode()
        assert "ModuleNotFoundError" not in stderr, (
            f"Hook depends on system package not in dependencies:\n{stderr}"
        )
