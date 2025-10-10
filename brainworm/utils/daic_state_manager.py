#!/usr/bin/env python3
"""
DAIC State Manager - Unified State Management with Transcript Processing Integration

Combines DAIC workflow enforcement with brainworm's analytics correlation system and intelligent
context delivery capabilities. Manages workflow state, analytics correlation, and transcript
processing coordination.

Key Capabilities:
- DAIC mode management (discussion/implementation) with subagent awareness
- Session and correlation ID tracking for analytics integration
- Flag-based coordination with transcript processing system
- Unified state management across hooks and analytics modules
- Configuration management for DAIC triggers and analytics settings

Integration Points:
- Works with transcript_processor.py for subagent context delivery
- Coordinates with flag system for cross-hook communication
- Supports context warning system with threshold management
- Provides unified state interface for all brainworm components
"""

import json
import toml
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union

# Import file management infrastructure
try:
    from .file_manager import AtomicFileWriter
except ImportError:
    AtomicFileWriter = None

# Import type definitions
from .hook_types import DeveloperInfo, DAICMode, UserConfig, DAICConfig, ToolBlockingResult


class DAICStateManager:
    """Unified state manager combining DAIC workflow with analytics correlation"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        # Use .brainworm for all brainworm functionality
        self.state_dir = self.project_root / ".brainworm" / "state"
        self.analytics_dir = self.project_root / ".brainworm" / "analytics"
        
        # State files
        self.unified_state_file = self.state_dir / "unified_session_state.json"
        
        # Config files  
        self.config_file = self.project_root / ".brainworm" / "config.toml"
        self.user_config_file = self.project_root / ".brainworm" / "user-config.json"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict[str, Any]:
        """Load brainworm configuration using shared canonical config"""
        try:
            # Import config loader from same directory (we're already in utils/)
            from .config import load_config
            
            # Use shared loader with verbose support
            verbose = '--verbose' in sys.argv
            return load_config(self.project_root, verbose=verbose)
        except ImportError:
            # Fallback if shared config not available
            if self.config_file.exists():
                return toml.load(self.config_file)
            return {"daic": {"enabled": True}}
    
    def load_daic_config(self) -> DAICConfig:
        """Load DAIC configuration as typed dataclass"""
        config = self.load_config()
        daic_data = config.get("daic", {})
        return DAICConfig.from_dict(daic_data)
    
    def load_user_config(self) -> UserConfig:
        """Load user preferences configuration with defaults"""
        if self.user_config_file.exists():
            try:
                with open(self.user_config_file, 'r') as f:
                    config_data = json.load(f)
                    return UserConfig.from_dict(config_data)
            except (json.JSONDecodeError, FileNotFoundError):
                return UserConfig()  # Returns default config
        return UserConfig()  # Returns default config
    
    def save_user_config(self, config: UserConfig):
        """Save user configuration with timestamp update"""
        config_dict = config.to_dict()
        config_dict["updated"] = datetime.now(timezone.utc).isoformat()
        
        if AtomicFileWriter:
            with AtomicFileWriter(self.user_config_file) as f:
                json.dump(config_dict, f, indent=2)
        else:
            # Fallback to manual atomic write
            with open(self.user_config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
    
    def get_developer_info(self) -> DeveloperInfo:
        """Get developer information from user config or git"""
        user_config = self.load_user_config()
        
        # If set to auto, try to get from git config
        if user_config.developer.git_identity_source == "auto":
            try:
                import subprocess
                name = subprocess.check_output(["git", "config", "user.name"], 
                                             cwd=self.project_root, text=True).strip()
                email = subprocess.check_output(["git", "config", "user.email"], 
                                              cwd=self.project_root, text=True).strip()
                if name and email:
                    return DeveloperInfo(name=name, email=email, source="git")
            except subprocess.CalledProcessError:
                pass
        
        return DeveloperInfo(
            name=user_config.developer.name,
            email=user_config.developer.email,
            source="config"
        )
    
    def get_daic_mode(self) -> DAICMode:
        """Get current DAIC mode (DAICMode enum)"""
        unified_state = self.get_unified_state()
        mode_str = unified_state.get("daic_mode", str(DAICMode.DISCUSSION))
        try:
            return DAICMode.from_string(mode_str)
        except ValueError:
            # Fallback to discussion mode if invalid
            return DAICMode.DISCUSSION
    
    def is_discussion_mode(self) -> bool:
        """Check if currently in discussion mode (blocks tools)"""
        return self.get_daic_mode() == DAICMode.DISCUSSION
    
    def set_daic_mode(self, mode: Union[str, DAICMode]) -> bool:
        """Set DAIC mode - accepts string or DAICMode enum"""
        # Convert input to DAICMode enum
        try:
            if isinstance(mode, DAICMode):
                daic_mode = mode
            else:
                daic_mode = DAICMode.from_string(mode)
        except ValueError:
            return False
        
        try:
            # Get previous mode from unified state
            unified_state = self.get_unified_state()
            previous_mode_str = unified_state.get("daic_mode")
            
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Update unified state only (single source of truth)
            self._update_unified_state({
                "daic_mode": str(daic_mode), 
                "daic_timestamp": timestamp,
                "previous_daic_mode": previous_mode_str
            })
            
            # Log transition for analytics
            self.log_daic_transition(previous_mode_str, str(daic_mode))
            
            return True
        except Exception:
            return False
    
    def toggle_daic_mode(self) -> str:
        """Toggle between discussion and implementation modes"""
        current_mode = self.get_daic_mode()
        new_mode = DAICMode.IMPLEMENTATION if current_mode == DAICMode.DISCUSSION else DAICMode.DISCUSSION
        success = self.set_daic_mode(new_mode)
        return str(new_mode) if success else str(current_mode)
    
    def get_task_state(self) -> Dict[str, Any]:
        """Get current task state from unified state (single source of truth)"""
        unified_state = self.get_unified_state()

        return {
            "task": unified_state.get("current_task"),
            "branch": unified_state.get("current_branch"),
            "submodule": unified_state.get("task_submodule"),
            "submodule_path": unified_state.get("task_submodule_path"),
            "services": unified_state.get("task_services", []),
            "active_submodule_branches": unified_state.get("active_submodule_branches", {}),
            "updated": unified_state.get("last_updated", "")[:10] if unified_state.get("last_updated") else None,  # YYYY-MM-DD format
            "correlation_id": unified_state.get("correlation_id"),
            "session_id": unified_state.get("session_id"),
            "success_prediction": unified_state.get("success_prediction")
        }
    
    def set_task_state(self, task: str, branch: str, services: List[str],
                      correlation_id: Optional[str] = None, session_id: Optional[str] = None,
                      submodule: Optional[str] = None,
                      active_submodule_branches: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Set current task state using unified state (single source of truth).

        Args:
            task: Task identifier
            branch: Git branch name (main repo's current branch)
            services: List of affected services/modules
            correlation_id: Analytics correlation ID
            session_id: Session ID
            submodule: Target submodule name (None for main repo) - legacy single submodule support
            active_submodule_branches: Mapping of submodule name to branch name for multi-service tasks
        """
        # Get developer info
        developer_info = self.get_developer_info()

        # Calculate submodule path if submodule specified
        submodule_path = None
        if submodule:
            submodule_path = str(self.project_root / submodule)

        # Update unified state only
        self._update_unified_state({
            "current_task": task,
            "current_branch": branch,
            "task_services": services,
            "task_correlation_id": correlation_id,
            "session_id": session_id,
            "correlation_id": correlation_id,
            "task_submodule": submodule,
            "task_submodule_path": submodule_path,
            "active_submodule_branches": active_submodule_branches or {},
            "main_repo_branch_created": submodule is None and not active_submodule_branches,
            "success_prediction": None,  # Will be populated by ML models
            "developer_name": developer_info.name,
            "developer_email": developer_info.email
        })

        # Return task state format
        return {
            "task": task,
            "branch": branch,
            "submodule": submodule,
            "submodule_path": submodule_path,
            "services": services,
            "active_submodule_branches": active_submodule_branches or {},
            "updated": datetime.now().strftime("%Y-%m-%d"),
            "correlation_id": correlation_id,
            "session_id": session_id,
            "success_prediction": None
        }
    
    def get_unified_state(self) -> Dict[str, Any]:
        """Get complete unified session state"""
        default_unified = {
            "daic_mode": str(DAICMode.DISCUSSION),
            "daic_timestamp": None,
            "current_task": None,
            "current_branch": None,
            "task_submodule": None,
            "task_submodule_path": None,
            "task_services": [],
            "active_submodule_branches": {},
            "main_repo_branch_created": False,
            "session_id": None,
            "correlation_id": None,
            "task_correlation_id": None,
            "success_prediction": None,
            "workflow_confidence": None,
            "last_updated": None
        }
        
        # Check if unified state file exists
        try:
            if self.unified_state_file.exists():
                with open(self.unified_state_file, 'r') as f:
                    state = json.load(f)
                    return {**default_unified, **state}
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Return default state if no unified state exists
        default_unified["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._save_unified_state(default_unified)
        return default_unified
    
    
    def _update_unified_state(self, updates: Dict[str, Any]):
        """Update specific fields in unified state"""
        current_state = self.get_unified_state()
        current_state.update(updates)
        current_state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._save_unified_state(current_state)
    
    def _save_unified_state(self, state: Dict[str, Any]):
        """Save unified state to file with atomic operation and validation"""
        # Validate state before saving
        if not self._validate_state(state):
            raise ValueError("Invalid state data - cannot save")
        
        # Use atomic write operation to prevent corruption
        if AtomicFileWriter:
            with AtomicFileWriter(self.unified_state_file) as f:
                json.dump(state, f, indent=2)
        else:
            # Fallback to manual atomic write
            temp_file = self.unified_state_file.with_suffix('.tmp')
            try:
                # Write to temporary file first
                with open(temp_file, 'w') as f:
                    json.dump(state, f, indent=2)
                
                # Atomic rename to final location
                temp_file.replace(self.unified_state_file)
            except Exception as e:
                # Clean up temporary file on error
                if temp_file.exists():
                    temp_file.unlink()
                raise e
    
    def _validate_state(self, state: Dict[str, Any]) -> bool:
        """Validate unified state data for consistency"""
        required_fields = [
            "daic_mode", "last_updated"
        ]
        
        # Check required fields exist and are not None
        for field in required_fields:
            if field not in state:
                print(f"Warning: Missing required field '{field}' in state")
                return False
            if state[field] is None:
                print(f"Warning: Required field '{field}' cannot be None")
                return False
        
        # Validate DAIC mode
        daic_mode = state.get("daic_mode")
        if not DAICMode.is_valid_mode(daic_mode):
            print(f"Warning: Invalid DAIC mode '{daic_mode}'")
            return False
        
        # Validate task services is list
        if "task_services" in state and not isinstance(state["task_services"], list):
            print(f"Warning: task_services must be a list, got {type(state['task_services'])}")
            return False
            
        # Optional fields that should not be empty strings if present
        optional_string_fields = ["session_id", "correlation_id"]
        for field in optional_string_fields:
            if field in state and state[field] is not None and state[field] == "":
                print(f"Warning: Field '{field}' should not be empty string")
                return False
            
        return True
    
    def update_session_correlation(self, session_id: str, correlation_id: str):
        """Update session correlation data"""
        self._update_unified_state({
            "session_id": session_id,
            "correlation_id": correlation_id
        })
    
    def should_block_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> ToolBlockingResult:
        """
        Determine if a tool should be blocked based on DAIC state and configuration
        Returns ToolBlockingResult with blocking decision and reason
        """
        daic_config = self.load_daic_config()
        
        if not daic_config.enabled:
            return ToolBlockingResult.allow_tool("DAIC enforcement disabled")
        
        is_discussion = self.is_discussion_mode()
        
        # Block configured tools in discussion mode
        if is_discussion and tool_name in daic_config.blocked_tools:
            return ToolBlockingResult.discussion_mode_block(tool_name)
        
        # Handle Bash commands specially
        if tool_name == "Bash":
            command = tool_input.get("command", "").strip()
            
            # Block daic command in discussion mode  
            if is_discussion and 'daic' in command:
                return ToolBlockingResult.command_block(
                    command, 
                    "The 'daic' command is not allowed in discussion mode. You're already in discussion mode."
                )
            
            # Check if command is read-only
            if is_discussion and not self._is_read_only_bash_command(command, daic_config):
                return ToolBlockingResult.command_block(command)
        
        return ToolBlockingResult.allow_tool()
    
    def _is_read_only_bash_command(self, command: str, daic_config: DAICConfig) -> bool:
        """Check if a bash command is read-only and safe in discussion mode"""
        import re
        
        # Get all read-only commands from the typed config
        read_only_commands = daic_config.read_only_bash_commands
        all_read_only_commands = (
            read_only_commands.basic +
            read_only_commands.git +
            read_only_commands.docker +
            read_only_commands.package_managers +
            read_only_commands.network +
            read_only_commands.text_processing
        )
        
        # Check for write patterns first
        write_patterns = [
            r'>\s*[^>]',  # Output redirection
            r'>>',         # Append redirection
            r'\btee\b',    # tee command
            r'\bmv\b',     # move/rename
            r'\bcp\b',     # copy
            r'\brm\b',     # remove
            r'\bmkdir\b',  # make directory
            r'\btouch\b',  # create/update file
            r'\bsed\s+(?!-n)',  # sed without -n flag
            r'\bnpm\s+install',  # npm install
            r'\bpip\s+install',  # pip install
        ]
        
        # If command has write patterns, it's not read-only
        if any(re.search(pattern, command) for pattern in write_patterns):
            return False
        
        # Check if ALL commands in chain are read-only
        command_parts = re.split(r'(?:&&|\|\||;|\|)', command)
        for part in command_parts:
            part = part.strip()
            if not part:
                continue
            
            # Check against configured read-only commands
            is_part_read_only = any(
                part.startswith(prefix) 
                for prefix in all_read_only_commands
            )
            
            if not is_part_read_only:
                return False
        
        return True
    
    def log_daic_transition(self, from_mode: str, to_mode: str, trigger: str = None):
        """Log DAIC mode transitions for analytics"""
        transition_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from_mode": from_mode,
            "to_mode": to_mode,
            "trigger": trigger,
            "session_id": self.get_unified_state().get("session_id"),
            "correlation_id": self.get_unified_state().get("correlation_id")
        }
        
        # Log to analytics if processor available
        try:
            from analytics_processor import ClaudeAnalyticsProcessor
            processor = ClaudeAnalyticsProcessor(self.project_root / ".brainworm")
            processor.log_event({
                "hook_name": "daic_transition",
                "event_type": "workflow_transition",
                **transition_event
            })
        except ImportError:
            # If analytics processor not available, just update state
            pass
