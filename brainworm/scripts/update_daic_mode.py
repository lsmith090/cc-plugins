#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "toml>=0.10.0",
# ]
# ///

"""
DAIC Mode Update Tool - Hooks Framework Implementation

Provides safe, atomic DAIC mode updates using Hooks Framework utilities.
Ensures consistency across all state files and proper workflow transitions.

Usage:
    uv run update_daic_mode.py --mode="implementation"
    uv run update_daic_mode.py --mode="discussion" 
    uv run update_daic_mode.py --toggle
"""

import sys
import argparse
from pathlib import Path
from rich.console import Console

# Add path to utils modules in hooks directory when deployed as script
sys.path.append(str(Path(__file__).parent.parent / 'hooks'))
from utils.project import find_project_root
from utils.business_controllers import create_daic_controller
from utils.hook_types import DAICMode

console = Console()

def main() -> None:
    """Main entry point for DAIC mode updates using Hooks Framework."""
    parser = argparse.ArgumentParser(
        description="Update DAIC mode programmatically",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run update_daic_mode.py --mode="discussion"
  uv run update_daic_mode.py --mode="implementation"
  uv run update_daic_mode.py --toggle
  uv run update_daic_mode.py  # Show current mode
        """
    )
    
    parser.add_argument("--mode", choices=[str(DAICMode.DISCUSSION), str(DAICMode.IMPLEMENTATION)], 
                       help="DAIC mode to set")
    parser.add_argument("--toggle", action="store_true", 
                       help="Toggle between discussion and implementation")
    
    args = parser.parse_args()
    
    # Find project root
    try:
        project_root = find_project_root()
    except Exception as e:
        console.print(f"❌ [red]Error finding project root:[/red] {e}")
        sys.exit(1)
    
    # Create DAIC controller using Hooks Framework
    daic_controller = create_daic_controller(project_root)
    
    try:
        if args.toggle:
            # Toggle current mode
            result = daic_controller.toggle_mode()
            if result.success:
                mode_display = daic_controller.get_mode_with_display()
                console.print(f"✅ {mode_display.emoji} [green]DAIC mode toggled from {result.old_mode} to:[/green] [{mode_display.color}]{result.new_mode}[/{mode_display.color}]")
            else:
                console.print(f"❌ [red]Failed to toggle DAIC mode:[/red] {result.error_message}")
                sys.exit(1)
                
        elif args.mode:
            # Set specific mode
            result = daic_controller.set_mode(args.mode, trigger="user_command")
            if result.success:
                mode_display = daic_controller.get_mode_with_display()
                console.print(f"✅ {mode_display.emoji} [green]DAIC mode set to:[/green] [{mode_display.color}]{result.new_mode}[/{mode_display.color}]")
            else:
                console.print(f"❌ [red]Failed to set DAIC mode to {args.mode}:[/red] {result.error_message}")
                sys.exit(1)
                
        else:
            # Show current mode
            mode_display = daic_controller.get_mode_with_display()
            if mode_display.success:
                console.print(f"\n{mode_display.emoji} [green]Current DAIC Mode:[/green] [{mode_display.color}]{mode_display.mode}[/{mode_display.color}]")
            else:
                console.print(f"❌ [red]Failed to get current DAIC mode[/red]")
                sys.exit(1)
        
    except Exception as e:
        console.print(f"❌ [red]Error updating DAIC mode:[/red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()