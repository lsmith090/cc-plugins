#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "tomli-w>=1.0.0",
# ]
# ///

"""
Session Correlation Update Script - Hooks Framework

Provides atomic session correlation updates using business controllers.
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console

# Add plugin root to path for utils access
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.business_controllers import create_session_controller
from utils.project import find_project_root

console = Console()


def update_session_correlation(
    project_root: Path, session_id: str = None, correlation_id: str = None, show_current: bool = False
) -> dict:
    """Update session correlation using SessionCorrelationController"""

    try:
        controller = create_session_controller(project_root)

        if show_current:
            # Show current state with consistency check
            consistency_result = controller.check_consistency()

            console.print("\n[green]Current Session Correlation:[/green]")
            console.print(f"  Unified Session ID: {consistency_result.unified_session}")
            console.print(f"  Unified Correlation ID: {consistency_result.unified_correlation}")
            console.print(f"  Task Session ID: {consistency_result.task_session}")

            if consistency_result.consistent:
                console.print("\n✅ [green]Session correlation is consistent[/green]")
            else:
                console.print("\n⚠️  [yellow]WARNING: Session correlation inconsistency detected![/yellow]")
                for issue in consistency_result.inconsistencies:
                    console.print(f"  • {issue}")
                console.print("  Use this tool to synchronize session IDs")

            return consistency_result

        # Generate IDs if not provided
        if session_id is None or correlation_id is None:
            generated_session, generated_correlation = controller.generate_ids()
            if session_id is None:
                session_id = generated_session
                console.print(f"🔄 [yellow]Generated new session ID:[/yellow] {session_id}")
            if correlation_id is None:
                correlation_id = generated_correlation
                console.print(f"🔄 [yellow]Generated new correlation ID:[/yellow] {correlation_id}")

        # Validate provided IDs (generated IDs are always valid)
        if session_id and len(session_id) < 4:
            console.print("❌ [red]Invalid session ID:[/red] Must be at least 4 characters")
            sys.exit(1)
        if correlation_id and len(correlation_id) < 4:
            console.print("❌ [red]Invalid correlation ID:[/red] Must be at least 4 characters")
            sys.exit(1)

        # Update session correlation atomically
        result = controller.update_correlation(session_id, correlation_id)

        # FIX #4: result is a CorrelationUpdateResult dataclass, not a dict
        if result.success:
            console.print("✅ [green]Session correlation updated:[/green]")
            console.print(f"  Session ID: {result.session_id}")
            console.print(f"  Correlation ID: {result.correlation_id}")
        else:
            console.print(f"❌ [red]Failed to update correlation:[/red] {result.error}")
            sys.exit(1)

        return result

    except Exception as e:
        console.print(f"❌ [red]Error updating session correlation:[/red] {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for session correlation updates"""
    parser = argparse.ArgumentParser(
        description="Update session correlation programmatically",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run update_session_correlation.py --session-id="abc-123" --correlation-id="xyz789"
  uv run update_session_correlation.py --session-id="abc-123"  # Generate correlation ID
  uv run update_session_correlation.py  # Generate both IDs
  uv run update_session_correlation.py --show-current  # Show current state
        """,
    )

    parser.add_argument("--session-id", help="Session ID to set")
    parser.add_argument("--correlation-id", help="Correlation ID to set")
    parser.add_argument("--show-current", action="store_true", help="Show current session correlation state")

    args = parser.parse_args()

    # Find project root
    try:
        project_root = find_project_root()
    except Exception as e:
        console.print(f"❌ [red]Error finding project root:[/red] {e}")
        sys.exit(1)

    # Update session correlation
    update_session_correlation(
        project_root=project_root,
        session_id=args.session_id,
        correlation_id=args.correlation_id,
        show_current=args.show_current,
    )


if __name__ == "__main__":
    main()
