#!/usr/bin/env python3
"""
Verify Duration Tracking in Brainworm Events

This script verifies that brainworm is correctly capturing and storing
duration information in hook events, and shows nautiloid how to extract it.

Usage:
    python3 verify_duration_tracking.py [project_root]

Example:
    python3 verify_duration_tracking.py /path/to/project
"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Optional


def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """Find project root by looking for .brainworm directory"""
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()
    while current != current.parent:
        if (current / ".brainworm").exists():
            return current
        current = current.parent

    return None


def verify_duration_tracking(project_root: Path) -> None:
    """Verify duration tracking in brainworm events"""

    db_path = project_root / ".brainworm" / "events" / "hooks.db"

    if not db_path.exists():
        print(f"❌ No event database found at: {db_path}")
        print("   Make sure brainworm is installed and has logged events")
        return

    print(f"✅ Found event database: {db_path}\n")

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check for post_tool_use events with timing data
    cursor.execute("""
        SELECT
            id,
            hook_name,
            session_id,
            timestamp,
            event_data
        FROM hook_events
        WHERE hook_name = 'post_tool_use'
        ORDER BY timestamp DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()

    if not rows:
        print("❌ No post_tool_use events found in database")
        print("   Try running Claude Code with brainworm active to generate events")
        conn.close()
        return

    print(f"✅ Found {len(rows)} recent post_tool_use events\n")
    print("=" * 80)
    print("Duration Tracking Verification")
    print("=" * 80)

    events_with_duration = 0
    total_duration_ms = 0.0

    for row in rows:
        event_id = row["id"]
        session_id = row["session_id"][:12] if row["session_id"] else "unknown"
        timestamp = row["timestamp"]

        # Parse event_data JSON
        event_data = json.loads(row["event_data"])

        # Extract tool name
        tool_name = event_data.get("tool_name", "unknown")

        # Extract duration from nested timing structure (CORRECT WAY)
        timing = event_data.get("timing", {})
        duration_ms = timing.get("execution_duration_ms")

        # Check for success field
        success = event_data.get("success", True)

        print(f"\nEvent #{event_id} | Session: {session_id}")
        print(f"  Tool: {tool_name}")
        print(f"  Timestamp: {timestamp}")
        print(f"  Success: {success}")

        if duration_ms is not None and duration_ms > 0:
            print(f"  ✅ Duration: {duration_ms:.2f} ms ({duration_ms/1000:.3f} seconds)")
            events_with_duration += 1
            total_duration_ms += duration_ms
        else:
            print(f"  ❌ Duration: {duration_ms} (missing or zero)")

            # Debug: Show timing structure
            if timing:
                print(f"  Timing data present: {json.dumps(timing, indent=4)}")
            else:
                print("  No timing data in event_data")

    conn.close()

    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total events analyzed: {len(rows)}")
    print(f"Events with duration: {events_with_duration}")
    print(f"Events missing duration: {len(rows) - events_with_duration}")

    if events_with_duration > 0:
        avg_duration = total_duration_ms / events_with_duration
        print("\n✅ Duration tracking is WORKING!")
        print(f"   Average duration: {avg_duration:.2f} ms ({avg_duration/1000:.3f} seconds)")
        print("\n📝 For nautiloid: Extract duration using:")
        print("   event_data['timing']['execution_duration_ms']")
    else:
        print("\n❌ No events with duration data found")
        print("   Possible issues:")
        print("   1. Timing coordination between pre/post hooks failing")
        print("   2. Timing files not being written to .brainworm/timing/")
        print("   3. Events logged before duration tracking was implemented")

        # Check timing directory
        timing_dir = project_root / ".brainworm" / "timing"
        if timing_dir.exists():
            timing_files = list(timing_dir.glob("*.json"))
            print(f"\n   Timing directory exists: {timing_dir}")
            print(f"   Timing files found: {len(timing_files)}")
        else:
            print(f"\n   ❌ Timing directory doesn't exist: {timing_dir}")


def show_extraction_examples():
    """Show code examples for nautiloid"""
    print("\n" + "=" * 80)
    print("Nautiloid Integration Examples")
    print("=" * 80)

    print("""
# CORRECT: Extract duration from nested JSON structure
def extract_duration(event_row):
    event_data = json.loads(event_row['event_data'])
    timing = event_data.get('timing', {})
    duration_ms = timing.get('execution_duration_ms', 0.0)
    return duration_ms

# Example DuckDB query (if you copy event_data to DuckDB)
SELECT
    session_id,
    json_extract(event_data, '$.tool_name') as tool_name,
    CAST(json_extract(event_data, '$.timing.execution_duration_ms') AS DOUBLE) as duration_ms,
    json_extract(event_data, '$.success') as success
FROM hook_events
WHERE hook_name = 'post_tool_use'
    AND duration_ms > 0;

# Example Python extraction in data harvester
for row in cursor.execute("SELECT * FROM hook_events WHERE hook_name = 'post_tool_use'"):
    event_data = json.loads(row['event_data'])

    # Extract fields
    tool_name = event_data.get('tool_name')
    success = event_data.get('success', True)
    duration_ms = event_data.get('timing', {}).get('execution_duration_ms', 0.0)

    # Use in analytics...
""")


def main():
    """Main entry point"""

    # Get project root from argument or find automatically
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        if not project_root.exists():
            print(f"Error: Project root not found: {project_root}")
            sys.exit(1)
    else:
        project_root = find_project_root()
        if project_root is None:
            print("Error: Could not find project root with .brainworm directory")
            print("Usage: python3 verify_duration_tracking.py [project_root]")
            sys.exit(1)

    print(f"Project root: {project_root}\n")

    verify_duration_tracking(project_root)
    show_extraction_examples()


if __name__ == "__main__":
    main()
