#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "toml>=0.10.0",
# ]
# ///

"""
DAIC Command - Manual DAIC Mode Toggle

Allows manual switching between discussion and implementation modes.
Can be run via Bash tool: `daic` or `daic discussion` or `daic implementation`
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
from rich.console import Console
from utils.project import find_project_root

console = Console()


def get_daic_state(project_root: Path) -> Dict[str, Any]:
    """Get current DAIC state from unified state"""
    state_dir = project_root / ".brainworm" / "state"
    unified_state_file = state_dir / "unified_session_state.json"
    
    try:
        if unified_state_file.exists():
            with open(unified_state_file, 'r') as f:
                unified_data = json.load(f)
                return {
                    "mode": unified_data.get("daic_mode", "discussion"),
                    "timestamp": unified_data.get("daic_timestamp"),
                    "previous_mode": unified_data.get("previous_daic_mode"),
                    "trigger": "unified_state"
                }
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    return {"mode": "discussion", "timestamp": None, "previous_mode": None, "trigger": None}


def set_daic_mode(project_root: Path, mode: str, trigger: str = "manual_command") -> Dict[str, Any]:
    """Set DAIC mode using DAICStateManager (unified state)"""

    # Use DAICStateManager for unified state management
    sys.path.insert(0, str(Path(__file__).parent.parent))  # Add plugin root for utils access
    from utils.daic_state_manager import DAICStateManager
    
    state_manager = DAICStateManager(project_root)
    
    # Set the mode using the unified state manager
    state_manager.set_daic_mode(mode)
    
    # Get the new state for return
    current_state = get_daic_state(project_root)
    
    return {
        "mode": mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "previous_mode": current_state.get("previous_mode"),
        "trigger": trigger
    }


def show_usage() -> None:
    """Show command usage"""
    console.print("\n[bold]DAIC Mode Control[/bold]")
    console.print("Usage:")
    console.print("  [green]daic[/green]                    - Toggle between modes")
    console.print("  [green]daic discussion[/green]        - Switch to discussion mode")  
    console.print("  [green]daic implementation[/green]    - Switch to implementation mode")
    console.print("  [green]daic status[/green]            - Show current mode")
    console.print("  [green]daic help[/green]              - Show this help")
    console.print()
    console.print("Modes:")
    console.print("  [blue]Discussion[/blue]      - Tools are blocked, focus on planning and alignment")
    console.print("  [blue]Implementation[/blue]  - Tools are enabled, execute agreed-upon changes")
    console.print()


def show_status(project_root: Path) -> None:
    """Show current DAIC status"""
    state = get_daic_state(project_root)
    mode = state.get("mode", "discussion")
    timestamp = state.get("timestamp")
    previous_mode = state.get("previous_mode")
    trigger = state.get("trigger")
    
    mode_emoji = "💭" if mode == "discussion" else "⚡"
    mode_color = "blue" if mode == "discussion" else "green"
    
    console.print(f"\n{mode_emoji} Current DAIC Mode: [{mode_color}]{mode.title()}[/{mode_color}]")
    
    if timestamp:
        console.print(f"  Last changed: {timestamp}")
    if previous_mode:
        console.print(f"  Previous mode: {previous_mode}")
    if trigger:
        console.print(f"  Trigger: {trigger}")
    
    console.print()
    
    if mode == "discussion":
        console.print("[blue]💡 In Discussion Mode:[/blue]")
        console.print("  • Edit/Write tools are blocked")
        console.print("  • Focus on planning and alignment")
        console.print("  • Use trigger phrases like 'make it so' to enable implementation")
    else:
        console.print("[green]💡 In Implementation Mode:[/green]")
        console.print("  • Edit/Write tools are enabled") 
        console.print("  • Execute only the agreed-upon changes")
        console.print("  • Run 'daic' when done to return to discussion mode")
    
    console.print()


def main() -> None:
    """DAIC command main entry point"""
    try:
        project_root = find_project_root()
        
        # Parse command line arguments
        args = sys.argv[1:] if len(sys.argv) > 1 else []
        
        if not args or args[0] in ["toggle", "switch"]:
            # Toggle mode
            current_state = get_daic_state(project_root)
            current_mode = current_state.get("mode", "discussion")
            new_mode = "implementation" if current_mode == "discussion" else "discussion"
            
            new_state = set_daic_mode(project_root, new_mode, "manual_toggle")
            
            mode_emoji = "💭" if new_mode == "discussion" else "⚡"
            mode_color = "blue" if new_mode == "discussion" else "green"
            
            console.print(f"\n{mode_emoji} DAIC Mode switched to: [{mode_color}]{new_mode.title()}[/{mode_color}]")
            
            if new_mode == "discussion":
                console.print("[blue]Tools are now blocked. Focus on discussion and planning.[/blue]")
            else:
                console.print("[green]Tools are now enabled. Implement the agreed-upon changes.[/green]")
            
            console.print()
            
        elif args[0] in ["discussion", "d"]:
            # Switch to discussion mode
            set_daic_mode(project_root, "discussion", "manual_command")
            console.print("\n💭 [blue]DAIC Mode: Discussion[/blue]")
            console.print("[blue]Tools are now blocked. Focus on discussion and planning.[/blue]\n")
            
        elif args[0] in ["implementation", "impl", "i"]:
            # Switch to implementation mode
            set_daic_mode(project_root, "implementation", "manual_command")
            console.print("\n⚡ [green]DAIC Mode: Implementation[/green]")
            console.print("[green]Tools are now enabled. Implement the agreed-upon changes.[/green]\n")
            
        elif args[0] in ["status", "s"]:
            # Show status
            show_status(project_root)
            
        elif args[0] in ["help", "h", "--help", "-h"]:
            # Show help
            show_usage()
            
        else:
            console.print(f"[red]Unknown command: {args[0]}[/red]")
            show_usage()
            sys.exit(1)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()