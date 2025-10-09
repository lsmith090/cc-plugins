#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
# ]
# ///

"""
View Analytics Data

Simple viewer for analytics data stored in .brainworm/analytics/
"""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from utils.analytics_processor import ClaudeAnalyticsProcessor

console = Console()

def main() -> None:
    """View analytics data"""
    # Find proper .brainworm directory using submodule-aware detection
    from utils.project import find_project_root
    try:
        project_root = find_project_root()
        brainworm_dir = project_root / '.brainworm'
    except RuntimeError:
        brainworm_dir = Path.cwd() / '.brainworm'

    if not brainworm_dir.exists():
        console.print("[red]No .brainworm directory found in current project[/red]")
        return

    processor = ClaudeAnalyticsProcessor(brainworm_dir)

    # Get statistics
    stats = processor.get_statistics()
    
    # Display statistics
    stats_table = Table(title="Hook Analytics (Last 24 Hours)")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")
    
    stats_table.add_row("Total Events", str(stats['total_events']))
    stats_table.add_row("Success Rate", f"{stats['success_rate']}%")
    stats_table.add_row("Avg Duration", f"{stats['avg_duration_ms']} ms")
    stats_table.add_row("Unique Sessions", str(stats['unique_sessions']))
    stats_table.add_row("Unique Correlations", str(stats['unique_correlations']))
    
    console.print(stats_table)
    
    # Get recent events
    recent_events = processor.get_recent_events(10)
    
    if recent_events:
        console.print("\n")
        events_table = Table(title="Recent Hook Events")
        events_table.add_column("Time", style="dim")
        events_table.add_column("Hook", style="cyan")
        events_table.add_column("Type", style="yellow")
        events_table.add_column("Status", style="green")
        events_table.add_column("Duration", style="blue")
        
        for event in recent_events[:10]:
            from datetime import datetime
            # Parse timestamp using standardized approach
            timestamp_val = event['timestamp']
            try:
                if isinstance(timestamp_val, str):
                    # ISO 8601 format - parse directly
                    timestamp = datetime.fromisoformat(timestamp_val.replace('Z', '+00:00'))
                elif isinstance(timestamp_val, (int, float)):
                    # Legacy numeric format - handle different scales
                    if timestamp_val > 1e12:  # Likely milliseconds or nanoseconds
                        if timestamp_val > 1e15:  # Likely nanoseconds
                            timestamp = datetime.fromtimestamp(timestamp_val / 1_000_000_000)
                        else:  # Likely milliseconds
                            timestamp = datetime.fromtimestamp(timestamp_val / 1000)
                    else:  # Likely seconds
                        timestamp = datetime.fromtimestamp(timestamp_val)
                else:
                    timestamp = datetime.now()
            except (ValueError, OSError, TypeError):
                # Fallback for invalid timestamps
                timestamp = datetime.now()
            
            status = "✅" if event.get('success') else "❌"
            duration = f"{event.get('duration_ms', 0):.1f}ms"
            
            events_table.add_row(
                timestamp.strftime('%H:%M:%S'),
                event['hook_name'],
                event['event_type'],
                status,
                duration
            )
        
        console.print(events_table)
    else:
        console.print("\n[dim]No recent events found[/dim]")
    
    # Show analytics directory info
    analytics_dir = brainworm_dir / "analytics"
    if analytics_dir.exists():
        db_size = (analytics_dir / "hooks.db").stat().st_size if (analytics_dir / "hooks.db").exists() else 0
        log_files = list((analytics_dir / "logs").glob("*.jsonl")) if (analytics_dir / "logs").exists() else []
        
        info_panel = Panel(
            f"Database: {db_size:,} bytes\n"
            f"Log Files: {len(log_files)} files\n"
            f"Location: {analytics_dir}",
            title="Analytics Storage",
            border_style="dim"
        )
        console.print("\n", info_panel)

if __name__ == "__main__":
    main()