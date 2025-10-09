#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Analysis and Validation Utilities for Hooks Framework

Utilities for tool response analysis, state validation, and consistency checking.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
import json
import os

try:
    from .daic_state_manager import DAICStateManager
except ImportError:
    try:
        from daic_state_manager import DAICStateManager
    except ImportError:
        DAICStateManager = None


class StateConsistencyChecker:
    """Validate state consistency across brainworm files."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.state_dir = project_root / ".brainworm" / "state"
        self.state_manager = DAICStateManager(project_root) if DAICStateManager else None
    
    def check_session_consistency(self) -> Dict[str, Any]:
        """Check consistency of session-related state across files."""
        result = {
            "consistent": True,
            "issues": [],
            "details": {},
            "recommendations": []
        }
        
        try:
            if not self.state_manager:
                result["consistent"] = False
                result["issues"].append("State manager not available")
                return result
            
            # Get state from different sources
            unified_state = self.state_manager.get_unified_state()
            task_state = self.state_manager.get_task_state()
            
            result["details"]["unified_state"] = unified_state
            result["details"]["task_state"] = task_state
            
            # Check session ID consistency
            self._check_session_ids(unified_state, task_state, result)
            
            # Check correlation ID consistency
            self._check_correlation_ids(unified_state, task_state, result)
            
            # Check DAIC mode consistency
            self._check_daic_mode_consistency(unified_state, result)
            
            # Check file timestamps
            self._check_file_timestamps(result)
            
        except Exception as e:
            result["consistent"] = False
            result["issues"].append(f"Consistency check failed: {str(e)}")
        
        return result
    
    def _check_session_ids(self, unified_state: Dict, task_state: Dict, result: Dict) -> None:
        """Check session ID consistency."""
        unified_session = unified_state.get("current_session", {}).get("session_id")
        task_session = task_state.get("current_session", {}).get("session_id")
        
        if unified_session and task_session:
            if unified_session != task_session:
                result["consistent"] = False
                result["issues"].append("Session ID mismatch between unified and task state")
                result["recommendations"].append("Run session correlation update to sync IDs")
        elif unified_session and not task_session:
            result["issues"].append("Task state missing session ID")
            result["recommendations"].append("Update task state with current session ID")
        elif not unified_session and task_session:
            result["issues"].append("Unified state missing session ID")
            result["recommendations"].append("Update unified state with current session ID")
    
    def _check_correlation_ids(self, unified_state: Dict, task_state: Dict, result: Dict) -> None:
        """Check correlation ID consistency."""
        unified_correlation = unified_state.get("current_session", {}).get("correlation_id")
        
        if not unified_correlation:
            result["issues"].append("Missing correlation ID in unified state")
            result["recommendations"].append("Generate and set correlation ID")
    
    def _check_daic_mode_consistency(self, unified_state: Dict, result: Dict) -> None:
        """Check DAIC mode state consistency."""
        daic_mode = unified_state.get("daic", {}).get("current_mode")
        
        if not daic_mode:
            result["issues"].append("Missing DAIC mode in unified state")
            result["recommendations"].append("Set default DAIC mode")
        elif daic_mode not in ["discussion", "implementation"]:
            result["consistent"] = False
            result["issues"].append(f"Invalid DAIC mode: {daic_mode}")
            result["recommendations"].append("Reset DAIC mode to valid value")
    
    def _check_file_timestamps(self, result: Dict) -> None:
        """Check state file timestamps for staleness."""
        state_files = [
            self.state_dir / "unified_session_state.json",
            self.state_dir / "daic-mode.json"
        ]
        
        for state_file in state_files:
            if state_file.exists():
                try:
                    stat_result = state_file.stat()
                    age_hours = (os.path.getctime(state_file.name) - stat_result.st_mtime) / 3600
                    
                    if age_hours > 24:  # More than 24 hours old
                        result["issues"].append(f"Stale state file: {state_file.name}")
                        result["recommendations"].append(f"Refresh state file: {state_file.name}")
                        
                except Exception:
                    result["issues"].append(f"Cannot access state file: {state_file.name}")
    
    def identify_inconsistencies(self, unified_state: Dict, task_state: Dict) -> List[Dict[str, Any]]:
        """Identify specific inconsistencies between state files."""
        inconsistencies = []
        
        # Session ID inconsistencies
        unified_session = unified_state.get("current_session", {}).get("session_id")
        task_session = task_state.get("current_session", {}).get("session_id")
        
        if unified_session != task_session:
            inconsistencies.append({
                "type": "session_id_mismatch",
                "description": "Session IDs don't match between unified and task state",
                "unified_value": unified_session,
                "task_value": task_session,
                "severity": "high"
            })
        
        # Current task inconsistencies
        unified_task = unified_state.get("current_task")
        task_task = task_state.get("current_task")
        
        if unified_task != task_task:
            inconsistencies.append({
                "type": "current_task_mismatch", 
                "description": "Current task values don't match",
                "unified_value": unified_task,
                "task_value": task_task,
                "severity": "medium"
            })
        
        return inconsistencies
    
    def suggest_fixes(self, inconsistencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest fixes for identified inconsistencies."""
        fixes = []
        
        for inconsistency in inconsistencies:
            if inconsistency["type"] == "session_id_mismatch":
                fixes.append({
                    "inconsistency_type": inconsistency["type"],
                    "fix_description": "Sync session IDs using correlation update",
                    "command": "tasks session",
                    "priority": "high"
                })
            
            elif inconsistency["type"] == "current_task_mismatch":
                fixes.append({
                    "inconsistency_type": inconsistency["type"],
                    "fix_description": "Update task state to match unified state",
                    "command": "./tasks status",
                    "priority": "medium"
                })
        
        return fixes


class FilePathExtractor:
    """Extract and analyze file paths from tool inputs and responses."""
    
    def extract_from_tool_input(self, tool_input: Dict[str, Any]) -> List[str]:
        """Extract file paths from tool input."""
        paths = []
        
        if not tool_input:
            return paths
        
        # Direct file_path field
        if "file_path" in tool_input:
            paths.append(str(tool_input["file_path"]))
        
        # Multiple files (in edits array)
        if "edits" in tool_input and isinstance(tool_input["edits"], list):
            for edit in tool_input["edits"]:
                if isinstance(edit, dict) and "file_path" in edit:
                    paths.append(str(edit["file_path"]))
        
        # Command-based file references
        if "command" in tool_input:
            command = str(tool_input["command"])
            # Simple heuristic for file paths in commands
            words = command.split()
            for word in words:
                if "/" in word and not word.startswith("-"):
                    paths.append(word)
        
        return list(set(paths))  # Remove duplicates
    
    def extract_from_tool_response(self, tool_response: Dict[str, Any]) -> List[str]:
        """Extract file paths from tool response."""
        paths = []
        
        if not tool_response:
            return paths
        
        # Response-specific paths
        if "filePath" in tool_response:
            paths.append(str(tool_response["filePath"]))
        
        if "file_path" in tool_response:
            paths.append(str(tool_response["file_path"]))
        
        # Structured patch information
        if "structuredPatch" in tool_response:
            patch = tool_response["structuredPatch"]
            if isinstance(patch, list):
                for item in patch:
                    if isinstance(item, dict) and "file" in item:
                        paths.append(str(item["file"]))
        
        return list(set(paths))
    
    def categorize_paths(self, paths: List[str]) -> Dict[str, List[str]]:
        """Categorize file paths by type."""
        categories = {
            "documentation": [],
            "code": [],
            "configuration": [],
            "test": [],
            "other": []
        }
        
        for path in paths:
            path_lower = path.lower()
            
            if any(doc in path_lower for doc in [".md", "readme", "docs/", "documentation/"]):
                categories["documentation"].append(path)
            elif any(code in path_lower for code in [".py", ".js", ".ts", ".java", ".cpp", ".go"]):
                categories["code"].append(path)
            elif any(config in path_lower for config in [".json", ".toml", ".yaml", ".yml", "config"]):
                categories["configuration"].append(path)
            elif any(test in path_lower for test in ["test", "spec", "__tests__"]):
                categories["test"].append(path)
            else:
                categories["other"].append(path)
        
        return categories


class CommandExtractor:
    """Extract and analyze commands from tool inputs."""
    
    def extract_command_info(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Extract command information from tool input."""
        command_info = {
            "has_command": False,
            "command": None,
            "command_type": None,
            "is_safe": True,
            "risk_factors": []
        }
        
        if not tool_input or "command" not in tool_input:
            return command_info
        
        command = str(tool_input["command"]).strip()
        command_info["has_command"] = True
        command_info["command"] = command
        
        # Analyze command type
        command_info["command_type"] = self._classify_command(command)
        
        # Analyze safety
        safety_analysis = self._analyze_command_safety(command)
        command_info["is_safe"] = safety_analysis["is_safe"]
        command_info["risk_factors"] = safety_analysis["risk_factors"]
        
        return command_info
    
    def _classify_command(self, command: str) -> str:
        """Classify command by type."""
        command_lower = command.lower().strip()
        
        if command_lower.startswith(("git ", "git\t")):
            return "git"
        elif command_lower.startswith(("npm ", "yarn ", "pip ", "uv ")):
            return "package_manager"
        elif command_lower.startswith(("ls", "cat", "head", "tail", "grep", "find")):
            return "read_only"
        elif command_lower.startswith(("rm", "mv", "cp", "mkdir", "touch")):
            return "file_system"
        elif command_lower.startswith(("curl", "wget", "ping")):
            return "network"
        else:
            return "other"
    
    def _analyze_command_safety(self, command: str) -> Dict[str, Any]:
        """Analyze command for potential risks."""
        safety = {
            "is_safe": True,
            "risk_factors": []
        }
        
        command_lower = command.lower()
        
        # Check for dangerous operations
        dangerous_patterns = [
            ("rm -rf", "Recursive force delete"),
            ("sudo ", "Elevated privileges"),
            ("chmod +x", "Making files executable"),
            ("eval", "Code evaluation"),
            ("exec", "Command execution"),
            ("> /dev/", "System device access")
        ]
        
        for pattern, description in dangerous_patterns:
            if pattern in command_lower:
                safety["is_safe"] = False
                safety["risk_factors"].append(description)
        
        return safety


def create_consistency_checker(project_root: Path) -> StateConsistencyChecker:
    """Factory function for StateConsistencyChecker."""
    return StateConsistencyChecker(project_root)


def create_file_path_extractor() -> FilePathExtractor:
    """Factory function for FilePathExtractor."""
    return FilePathExtractor()


def create_command_extractor() -> CommandExtractor:
    """Factory function for CommandExtractor."""
    return CommandExtractor()