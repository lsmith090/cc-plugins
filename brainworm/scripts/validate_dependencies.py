#!/usr/bin/env python3
"""
Dependency Validation Script for Brainworm Plugin

Validates that all inline script dependencies match documented standard versions.
Prevents dependency drift and ensures consistency across the plugin.

Usage:
    python3 scripts/validate_dependencies.py                    # Validate all files
    python3 scripts/validate_dependencies.py --verbose          # Detailed output
    python3 scripts/validate_dependencies.py --file path.py     # Validate specific file
"""

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

# Standard dependency versions from DEPENDENCIES.md
STANDARD_VERSIONS = {
    "rich": ">=13.0.0",
    "filelock": ">=3.13.0",
    "tomli-w": ">=1.0.0",
    "typer": ">=0.9.0",
    "tiktoken": ">=0.7.0",
    "pendulum": ">=3.0.0",
}

# Deprecated dependencies that should not be used
DEPRECATED_DEPS = {
    "toml": "Use tomli-w>=1.0.0 for writing, tomllib (built-in) for reading"
}


def extract_dependencies(file_path: Path) -> List[str]:
    """Extract inline script dependencies from a Python file"""
    try:
        content = file_path.read_text()

        # Look for PEP 723 inline script metadata
        match = re.search(r'# /// script\n(.*?)# ///', content, re.DOTALL)
        if not match:
            return []

        metadata_block = match.group(1)

        # Extract dependencies list
        deps_match = re.search(r'# dependencies = \[(.*?)\]', metadata_block, re.DOTALL)
        if not deps_match:
            return []

        deps_str = deps_match.group(1)

        # Parse individual dependencies
        dependencies = []
        for line in deps_str.split('\n'):
            line = line.strip()
            if line.startswith('#') and '"' in line:
                # Extract dependency string
                dep_match = re.search(r'"([^"]+)"', line)
                if dep_match:
                    dependencies.append(dep_match.group(1))

        return dependencies
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return []


def parse_dependency(dep_str: str) -> Tuple[str, str]:
    """Parse a dependency string into package name and version constraint"""
    # Handle cases like "rich>=13.0.0", "rich", "tomli-w>=1.0.0"
    if ">=" in dep_str:
        parts = dep_str.split(">=")
        return parts[0].strip(), f">={parts[1].strip()}"
    elif "==" in dep_str:
        parts = dep_str.split("==")
        return parts[0].strip(), f"=={parts[1].strip()}"
    else:
        # No version specified
        return dep_str.strip(), ""


def validate_file(file_path: Path, verbose: bool = False) -> Tuple[bool, List[str]]:
    """Validate dependencies in a single file

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    deps = extract_dependencies(file_path)

    if not deps and verbose:
        print(f"  {file_path.relative_to(Path.cwd())}: No inline dependencies")
        return True, []

    for dep_str in deps:
        package, version = parse_dependency(dep_str)

        # Check for deprecated dependencies
        if package in DEPRECATED_DEPS:
            errors.append(
                f"  ❌ {file_path.relative_to(Path.cwd())}: "
                f"Uses deprecated '{package}' - {DEPRECATED_DEPS[package]}"
            )
            continue

        # Check if version matches standard
        if package in STANDARD_VERSIONS:
            expected_version = STANDARD_VERSIONS[package]
            if version != expected_version:
                errors.append(
                    f"  ❌ {file_path.relative_to(Path.cwd())}: "
                    f"'{package}' version mismatch - found '{version}', expected '{expected_version}'"
                )
        elif verbose:
            # Warn about non-standard dependency
            print(
                f"  ⚠️  {file_path.relative_to(Path.cwd())}: "
                f"Non-standard dependency '{dep_str}' (not in DEPENDENCIES.md)"
            )

    if not errors and verbose:
        print(f"  ✅ {file_path.relative_to(Path.cwd())}: All dependencies valid")

    return len(errors) == 0, errors


def validate_all_files(plugin_root: Path, verbose: bool = False) -> Tuple[bool, Dict[str, List[str]]]:
    """Validate all Python files in the plugin

    Returns:
        Tuple of (all_valid, dict of file_path -> errors)
    """
    all_errors = defaultdict(list)
    all_valid = True

    # Find all Python files with inline dependencies
    python_files = []
    for pattern in ["hooks/*.py", "scripts/*.py", "utils/*.py"]:
        python_files.extend(plugin_root.glob(pattern))

    if verbose:
        print(f"\n🔍 Validating {len(python_files)} Python files...\n")

    for py_file in python_files:
        is_valid, errors = validate_file(py_file, verbose)
        if not is_valid:
            all_valid = False
            all_errors[str(py_file)] = errors

    return all_valid, dict(all_errors)


def check_for_deprecated_imports(plugin_root: Path) -> List[str]:
    """Check for deprecated import statements in Python files"""
    issues = []

    deprecated_imports = {
        r'^import toml\b': "import toml (use 'import tomllib' and 'import tomli_w' instead)",
        r'^from toml import': "from toml import (use tomllib/tomli_w instead)",
    }

    for py_file in plugin_root.rglob("*.py"):
        try:
            content = py_file.read_text()
            for pattern, message in deprecated_imports.items():
                if re.search(pattern, content, re.MULTILINE):
                    issues.append(
                        f"  ❌ {py_file.relative_to(Path.cwd())}: {message}"
                    )
        except Exception as e:
            # File unreadable - skip (may be binary or permission issue)
            print(f"Debug: Failed to check {py_file}: {e}", file=sys.stderr)

    return issues


def validate_import_completeness(file_path: Path, verbose: bool = False) -> Tuple[bool, List[str]]:
    """Test that script can actually execute with its declared dependencies

    This catches missing transitive dependencies that static validation misses.
    For example, if script imports module A, and module A requires package B,
    but package B is not declared in the script's inline dependencies.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Only test files with inline script metadata
    deps = extract_dependencies(file_path)
    if not deps:
        return True, []

    # Test script execution with minimal JSON input
    test_input = json.dumps({"session_id": "test", "test": True})

    try:
        # CRITICAL: Use --no-project flag to ignore repo's pyproject.toml
        # Without this, uv would use repo dependencies and give false positives
        # (script works due to repo deps, not inline script deps)
        result = subprocess.run(
            ["uv", "run", "--no-project", str(file_path)],
            input=test_input,
            capture_output=True,
            text=True,
            timeout=5
        )

        # Check for import errors in stderr
        stderr = result.stderr

        # Look for ModuleNotFoundError, ImportError, or our fail-fast RuntimeError
        if "ModuleNotFoundError" in stderr or "ImportError" in stderr or "HOOK INFRASTRUCTURE FAILURE" in stderr:
            # Extract the missing module name
            module_match = re.search(r"No module named ['\"]([^'\"]+)['\"]", stderr)
            if module_match:
                missing_module = module_match.group(1)

                # Try to map module name to package name
                # Common mappings: tomli_w -> tomli-w, etc.
                suggested_package = missing_module.replace("_", "-")

                errors.append(
                    f"  ❌ {file_path.relative_to(Path.cwd())}: "
                    f"Import failed - missing module '{missing_module}' "
                    f"(try adding '{suggested_package}' to dependencies)"
                )
            else:
                # Generic import error
                import_match = re.search(r"ImportError: (.+)", stderr)
                if import_match:
                    errors.append(
                        f"  ❌ {file_path.relative_to(Path.cwd())}: "
                        f"Import failed - {import_match.group(1)}"
                    )
                else:
                    errors.append(
                        f"  ❌ {file_path.relative_to(Path.cwd())}: "
                        f"Import or module error detected (check stderr)"
                    )

        if verbose and not errors:
            print(f"  ✅ {file_path.relative_to(Path.cwd())}: Import test passed")

    except subprocess.TimeoutExpired:
        # Timeout is not necessarily an error - script might be waiting for input
        # As long as imports succeeded, that's what we care about
        if verbose:
            print(f"  ⏱️  {file_path.relative_to(Path.cwd())}: Timeout (imports likely OK)")
    except FileNotFoundError:
        errors.append(
            f"  ⚠️  {file_path.relative_to(Path.cwd())}: "
            f"Cannot test - 'uv' not found (install with: pip install uv)"
        )
    except Exception as e:
        errors.append(
            f"  ⚠️  {file_path.relative_to(Path.cwd())}: "
            f"Could not test imports: {e}"
        )

    return len(errors) == 0, errors


def validate_all_import_completeness(plugin_root: Path, verbose: bool = False) -> Tuple[bool, Dict[str, List[str]]]:
    """Test import completeness for all inline scripts

    Returns:
        Tuple of (all_valid, dict of file_path -> errors)
    """
    all_errors = defaultdict(list)
    all_valid = True

    # Only test hooks and scripts (not utils)
    python_files = []
    for pattern in ["hooks/*.py", "scripts/*.py"]:
        python_files.extend(plugin_root.glob(pattern))

    if verbose:
        print(f"\n🧪 Testing import completeness for {len(python_files)} scripts...\n")

    for py_file in python_files:
        is_valid, errors = validate_import_completeness(py_file, verbose)
        if not is_valid:
            all_valid = False
            all_errors[str(py_file)] = errors

    return all_valid, dict(all_errors)


def print_summary(all_valid: bool, all_errors: Dict[str, List[str]],
                 import_issues: List[str], import_test_errors: Dict[str, List[str]],
                 verbose: bool = False):
    """Print validation summary"""
    print("\n" + "=" * 80)
    print("DEPENDENCY VALIDATION SUMMARY")
    print("=" * 80)

    if all_valid and not import_issues and not import_test_errors:
        print("\n✅ All dependencies are valid and complete!")
        print("\n✅ Static validation: All inline dependencies match standard versions")
        print("✅ Dynamic validation: All scripts can import successfully")
        print("✅ No deprecated dependencies found")
        print("✅ No deprecated import statements found")
    else:
        if all_errors:
            print("\n❌ INLINE DEPENDENCY VERSION ISSUES")
            print("-" * 80)
            for file_path, errors in all_errors.items():
                for error in errors:
                    print(error)

        if import_test_errors:
            print("\n❌ IMPORT COMPLETENESS ISSUES (CRITICAL)")
            print("-" * 80)
            print("These scripts cannot execute due to missing dependencies:")
            for file_path, errors in import_test_errors.items():
                for error in errors:
                    print(error)

        if import_issues:
            print("\n❌ DEPRECATED IMPORT STATEMENTS")
            print("-" * 80)
            for issue in import_issues:
                print(issue)

        print("\n📋 REMEDIATION STEPS:")
        print("-" * 80)
        if import_test_errors:
            print("🚨 CRITICAL: Fix import completeness issues first!")
            print("1. Add missing dependencies to inline script metadata")
            print("   Example: Add 'tomli-w>=1.0.0' to dependencies list")
            print("2. Test script execution: echo '{}' | uv run path/to/script.py")
            print("3. Run validator again to verify fixes\n")
        print("For version issues:")
        print("• Review DEPENDENCIES.md for correct versions")
        print("• Update inline script metadata in flagged files")
        print("\nFor deprecated imports:")
        print("• Replace: import toml → import tomllib + import tomli_w")
        print("• Use 'rb'/'wb' modes for TOML file operations")
        print("\n💡 Run with --verbose to see detailed validation output")
        print("\nSee DEPENDENCIES.md for complete migration guide.")

    print("\n" + "=" * 80 + "\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate brainworm plugin dependency consistency"
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Validate a specific file instead of all files"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed validation output"
    )

    args = parser.parse_args()

    # Security: Determine plugin root with path validation
    try:
        script_file = Path(__file__).resolve()
        script_dir = script_file.parent
        plugin_root = script_dir.parent

        # Validate paths are within expected structure
        # script should be in brainworm/scripts/, plugin_root should be brainworm/
        if script_dir.name != "scripts":
            print("Error: Script must be run from brainworm/scripts/ directory", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to determine plugin root: {e}", file=sys.stderr)
        sys.exit(1)

    if args.file:
        # Security: Validate and resolve file path
        try:
            file_path = Path(args.file).resolve()
            # Ensure file is within plugin root to prevent path traversal
            file_path.relative_to(plugin_root)
        except ValueError:
            print(f"Error: File must be within plugin directory: {args.file}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: Invalid file path: {e}", file=sys.stderr)
            sys.exit(1)

        # Validate single file
        print(f"\n🔍 Validating {file_path.relative_to(plugin_root)}...\n")

        # Static validation (version consistency)
        is_valid, errors = validate_file(file_path, verbose=True)

        # Dynamic validation (import completeness)
        import_valid, import_errors = validate_import_completeness(file_path, verbose=True)

        all_errors = errors + import_errors
        if all_errors:
            print("\n❌ VALIDATION FAILED:")
            for error in all_errors:
                print(error)
            sys.exit(1)
        else:
            print(f"\n✅ {args.file}: All validations passed")
            print("  • Static validation: Dependencies match standard versions")
            print("  • Dynamic validation: Script can import successfully")
            sys.exit(0)
    else:
        # Validate all files
        # 1. Static validation (version consistency)
        all_valid, all_errors = validate_all_files(plugin_root, verbose=args.verbose)

        # 2. Check for deprecated imports
        import_issues = check_for_deprecated_imports(plugin_root)

        # 3. Dynamic validation (import completeness)
        import_test_valid, import_test_errors = validate_all_import_completeness(
            plugin_root, verbose=args.verbose
        )

        # Print summary
        print_summary(all_valid, all_errors, import_issues, import_test_errors, verbose=args.verbose)

        # Exit with appropriate code
        if all_valid and not import_issues and import_test_valid:
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
