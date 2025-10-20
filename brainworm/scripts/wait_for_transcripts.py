#!/usr/bin/env python3
"""
Wait for Transcripts Script - Brainworm Plugin

Waits for transcript files to be ready for subagent consumption.
Solves race condition where transcript_processor hook may not have finished
writing files before subagent starts reading them.

Usage:
    .brainworm/plugin-launcher scripts/wait_for_transcripts.py <subagent-type>

Example:
    .brainworm/plugin-launcher scripts/wait_for_transcripts.py logging
"""

import sys
import time
from pathlib import Path
from typing import List, Optional


def find_project_root() -> Path:
    """Find project root by looking for .brainworm directory."""
    current = Path.cwd()

    # Check current directory and parents
    for path in [current] + list(current.parents):
        brainworm_dir = path / '.brainworm'
        if brainworm_dir.exists() and brainworm_dir.is_dir():
            return path

    # Fallback to current directory
    return current

def wait_for_transcripts(
    subagent_type: str,
    project_root: Path,
    timeout_ms: int = 5000,
    initial_delay_ms: int = 50
) -> List[Path]:
    """
    Wait for transcript files to be ready in subagent directory.

    Implements exponential backoff polling to wait for the transcript_processor
    hook to finish writing transcript files. This solves the race condition where
    the hook fires on PreToolUse but files may not be written yet.

    Args:
        subagent_type: Subagent name (e.g., "logging", "context-gathering")
        project_root: Project root directory path
        timeout_ms: Maximum wait time in milliseconds (default: 5000ms = 5s)
        initial_delay_ms: Starting delay for exponential backoff (default: 50ms)

    Returns:
        List of transcript file paths when ready

    Raises:
        TimeoutError: If files not ready within timeout
        FileNotFoundError: If directory doesn't exist (hook failed)
    """
    # Track file sizes between polls to detect stability
    previous_sizes: Optional[dict] = None
    # Normalize subagent_type (strip plugin namespace prefix if present)
    # e.g., "brainworm:context-gathering" -> "context-gathering"
    subagent_dir_name = subagent_type.split(':', 1)[-1] if ':' in subagent_type else subagent_type

    # Target directory where hook writes files
    batch_dir = project_root / '.brainworm' / 'state' / subagent_dir_name

    # First check: does the directory exist at all?
    if not batch_dir.exists():
        raise FileNotFoundError(
            f"Subagent directory does not exist: {batch_dir}\n"
            f"This indicates the transcript_processor hook never ran.\n"
            f"Check .brainworm/debug_*.log for hook errors."
        )

    # Polling loop with exponential backoff
    start_time = time.time()
    delay_ms = initial_delay_ms
    attempt = 0

    while True:
        elapsed_ms = (time.time() - start_time) * 1000

        # Check timeout
        if elapsed_ms >= timeout_ms:
            raise TimeoutError(
                f"Timeout waiting for transcripts in {batch_dir}\n"
                f"Waited {elapsed_ms:.0f}ms with {attempt} attempts.\n"
                f"Files may be stuck or system is very slow.\n"
                f"Check .brainworm/logs/timing/ for hook performance data."
            )

        # Look for transcript files
        transcript_files = sorted(batch_dir.glob("current_transcript_*.json"))

        # Also check for service context file (written together with transcripts)
        service_context_file = batch_dir / "service_context.json"

        # Success condition: at least one transcript file AND service context exists
        if transcript_files and service_context_file.exists():
            # Additional check: verify file size stability
            # Track file sizes to ensure they're not still being written
            current_sizes = {}
            for f in transcript_files:
                try:
                    current_sizes[str(f)] = f.stat().st_size
                except OSError:
                    # File disappeared or became unreadable
                    break
            else:
                # Also track service context file
                try:
                    current_sizes[str(service_context_file)] = service_context_file.stat().st_size
                except OSError:
                    pass

                # Check if all files are non-empty
                all_non_empty = all(size > 0 for size in current_sizes.values())

                if not all_non_empty:
                    # Files exist but are empty, keep waiting
                    previous_sizes = current_sizes
                elif previous_sizes is None:
                    # First time seeing non-empty files, save sizes and wait one more poll
                    previous_sizes = current_sizes
                elif current_sizes == previous_sizes:
                    # File sizes haven't changed since last poll - they're stable!
                    return transcript_files
                else:
                    # File sizes changed - still being written
                    previous_sizes = current_sizes

        # Wait before next attempt with exponential backoff
        time.sleep(delay_ms / 1000.0)
        attempt += 1

        # Exponential backoff: 50ms -> 100ms -> 200ms -> 400ms -> 800ms -> 1600ms
        delay_ms = min(delay_ms * 2, 1600)  # Cap at 1.6 seconds

def main():
    """Main entry point for wait script."""
    # Parse arguments
    if len(sys.argv) < 2:
        print("Error: Subagent type required", file=sys.stderr)
        print("Usage: wait_for_transcripts.py <subagent-type>", file=sys.stderr)
        print("Example: wait_for_transcripts.py logging", file=sys.stderr)
        sys.exit(1)

    subagent_type = sys.argv[1]

    # Optional: accept timeout as second argument
    timeout_ms = 5000  # Default 5 seconds
    if len(sys.argv) >= 3:
        try:
            timeout_ms = int(sys.argv[2])
        except ValueError:
            print(f"Warning: Invalid timeout '{sys.argv[2]}', using default 5000ms", file=sys.stderr)

    try:
        # Find project root
        project_root = find_project_root()

        # Wait for transcripts
        transcript_files = wait_for_transcripts(subagent_type, project_root, timeout_ms)

        # Output paths for subagent to read
        # Each path on its own line for easy parsing
        for transcript_file in transcript_files:
            print(transcript_file)

        sys.exit(0)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)  # Exit code 2 = directory not found (hook failure)

    except TimeoutError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)  # Exit code 3 = timeout (files not ready)

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)  # Exit code 1 = general error

if __name__ == '__main__':
    main()
