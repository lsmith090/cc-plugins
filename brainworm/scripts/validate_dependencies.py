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

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict

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
        except Exception:
            pass

    return issues


def print_summary(all_valid: bool, all_errors: Dict[str, List[str]],
                 import_issues: List[str], verbose: bool = False):
    """Print validation summary"""
    print("\n" + "=" * 80)
    print("DEPENDENCY VALIDATION SUMMARY")
    print("=" * 80)

    if all_valid and not import_issues:
        print("\n✅ All dependencies are valid and consistent!")
        print("\nAll inline script dependencies match documented standard versions.")
        print("No deprecated dependencies found.")
        print("No deprecated import statements found.")
    else:
        if all_errors:
            print("\n❌ INLINE DEPENDENCY ISSUES")
            print("-" * 80)
            for file_path, errors in all_errors.items():
                for error in errors:
                    print(error)

        if import_issues:
            print("\n❌ DEPRECATED IMPORT STATEMENTS")
            print("-" * 80)
            for issue in import_issues:
                print(issue)

        print("\n📋 REMEDIATION STEPS:")
        print("-" * 80)
        print("1. Review DEPENDENCIES.md for correct versions")
        print("2. Update inline script metadata in flagged files")
        print("3. Replace deprecated imports:")
        print("   - import toml → import tomllib + import tomli_w")
        print("   - Use 'rb'/'wb' modes for TOML file operations")
        print("4. Run this script again to verify fixes")
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

    # Determine plugin root
    script_dir = Path(__file__).parent
    plugin_root = script_dir.parent

    if args.file:
        # Validate single file
        print(f"\n🔍 Validating {args.file}...\n")
        is_valid, errors = validate_file(args.file, verbose=True)

        if errors:
            for error in errors:
                print(error)
            sys.exit(1)
        else:
            print(f"\n✅ {args.file}: All dependencies valid")
            sys.exit(0)
    else:
        # Validate all files
        all_valid, all_errors = validate_all_files(plugin_root, verbose=args.verbose)

        # Check for deprecated imports
        import_issues = check_for_deprecated_imports(plugin_root)

        # Print summary
        print_summary(all_valid, all_errors, import_issues, verbose=args.verbose)

        # Exit with appropriate code
        if all_valid and not import_issues:
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
