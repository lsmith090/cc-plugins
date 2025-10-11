#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Business Logic Controllers for Hooks Framework

High-level controllers for common brainworm hook business operations.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import uuid
from datetime import datetime, timezone

try:
    from .daic_state_manager import DAICStateManager
    from .hook_types import (DAICMode, DAICModeOperationResult, ModeDisplayInfo, 
                           CorrelationUpdateResult, ConsistencyCheckResult, IdGenerationResult)
except ImportError:
    try:
        from daic_state_manager import DAICStateManager
        from hook_types import (DAICMode, DAICModeOperationResult, ModeDisplayInfo, 
                              CorrelationUpdateResult, ConsistencyCheckResult, IdGenerationResult)
    except ImportError:
        DAICStateManager = None
        DAICMode = None
        DAICModeOperationResult = None
        ModeDisplayInfo = None
        CorrelationUpdateResult = None
        ConsistencyCheckResult = None
        IdGenerationResult = None


class SubagentContextManager:
    """Manages subagent context flags and cleanup."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.state_dir = project_root / ".brainworm" / "state"
        self.subagent_flag = self.state_dir / "in_subagent_context.flag"
    
    def cleanup_on_task_completion(self, tool_name: str) -> bool:
        """Clean up subagent context flag when Task tool completes."""
        try:
            if tool_name == "Task" and self.subagent_flag.exists():
                self.subagent_flag.unlink()
                return True
            return False
        except Exception:
            return False
    
    def set_subagent_context(self, agent_type: str = "unknown") -> bool:
        """Set subagent context flag with metadata."""
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            with open(self.subagent_flag, 'w') as f:
                f.write(f"{agent_type}\n{datetime.now(timezone.utc).isoformat()}")
            return True
        except Exception:
            return False
    
    def clear_subagent_context(self) -> bool:
        """Clear subagent context flag."""
        try:
            if self.subagent_flag.exists():
                self.subagent_flag.unlink()
            return True
        except Exception:
            return False
    
    def is_in_subagent_context(self) -> bool:
        """Check if currently in subagent context."""
        return self.subagent_flag.exists()


class DAICModeController:
    """High-level DAIC mode operations."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.state_manager = DAICStateManager(project_root) if DAICStateManager else None
    
    def toggle_mode(self) -> DAICModeOperationResult:
        """Toggle DAIC mode between discussion and implementation.
        
        Returns:
            DAICModeOperationResult: Structured result with old/new modes
        """
        if not self.state_manager or not DAICMode or not DAICModeOperationResult:
            return DAICModeOperationResult.failed_operation(
                "MISSING_DEPENDENCIES", 
                "State manager or DAICMode not available"
            )
        
        try:
            current_mode = self.state_manager.get_daic_mode()
            new_mode = DAICMode.IMPLEMENTATION if current_mode == DAICMode.DISCUSSION else DAICMode.DISCUSSION
            success = self.state_manager.set_daic_mode(new_mode)
            
            if success:
                return DAICModeOperationResult.successful_toggle(
                    old_mode=current_mode,
                    new_mode=new_mode,
                    trigger="toggle_command"
                )
            else:
                return DAICModeOperationResult.failed_operation(
                    "SET_MODE_FAILED",
                    f"Failed to set DAIC mode to {new_mode}"
                )
        except Exception as e:
            return DAICModeOperationResult.failed_operation(
                "TOGGLE_EXCEPTION",
                str(e)
            )
    
    def set_mode(self, mode: str, trigger: str = None) -> DAICModeOperationResult:
        """Set specific DAIC mode.
        
        Returns:
            DAICModeOperationResult: Structured result with mode information
        """
        if not self.state_manager or not DAICMode or not DAICModeOperationResult:
            return DAICModeOperationResult.failed_operation(
                "MISSING_DEPENDENCIES",
                "State manager or DAICMode not available"
            )
        
        try:
            # Validate mode using DAICMode enum
            if not DAICMode.is_valid_mode(mode):
                return DAICModeOperationResult.failed_operation(
                    "INVALID_MODE",
                    f"Invalid DAIC mode: {mode}. Must be 'discussion' or 'implementation'"
                )
            
            # Get current mode before changing
            current_mode = self.state_manager.get_daic_mode()
            daic_mode = DAICMode.from_string(mode)
            success = self.state_manager.set_daic_mode(daic_mode)
            
            if success:
                return DAICModeOperationResult.successful_set(
                    mode=daic_mode,
                    trigger=trigger or "set_command"
                )
            else:
                return DAICModeOperationResult.failed_operation(
                    "SET_MODE_FAILED", 
                    f"Failed to set DAIC mode to {mode}"
                )
        except Exception as e:
            return DAICModeOperationResult.failed_operation(
                "SET_EXCEPTION",
                str(e)
            )
    
    def get_mode_with_display(self) -> ModeDisplayInfo:
        """Get current mode with display formatting."""
        if not self.state_manager or not DAICMode or not ModeDisplayInfo:
            return ModeDisplayInfo.error_display()
        
        try:
            mode = self.state_manager.get_daic_mode()
            display_info = {
                DAICMode.DISCUSSION: {"emoji": "💭", "color": "purple"},
                DAICMode.IMPLEMENTATION: {"emoji": "⚡", "color": "green"}
            }
            
            info = display_info.get(mode, {"emoji": "❓", "color": "white"})
            return ModeDisplayInfo.success_display(mode, info["emoji"], info["color"])
        except Exception:
            return ModeDisplayInfo.error_display()


class SessionCorrelationController:
    """High-level session correlation operations."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.state_manager = DAICStateManager(project_root) if DAICStateManager else None
    
    def update_correlation(self, session_id: str, correlation_id: str = None) -> CorrelationUpdateResult:
        """Update session correlation with validation.
        
        Returns:
            CorrelationUpdateResult: Update result with metadata
        """
        if not self.state_manager or not CorrelationUpdateResult:
            return CorrelationUpdateResult.failed_update("", "", "No state manager available")
        
        try:
            # Generate correlation ID if not provided
            if not correlation_id:
                correlation_id = self._generate_short_id()
            
            # Validate IDs
            if not session_id or len(session_id) < 4:
                return CorrelationUpdateResult.invalid_session_id()
            
            if not correlation_id or len(correlation_id) < 4:
                return CorrelationUpdateResult.invalid_correlation_id()
            
            # Update unified state
            success = self.state_manager.update_session_correlation(session_id, correlation_id)

            # FIX #3: Also update .correlation_state file to keep both systems in sync
            if success:
                try:
                    from .correlation_manager import CorrelationManager
                    corr_mgr = CorrelationManager(self.project_root)
                    corr_mgr._store_session_correlation(session_id, correlation_id)
                except Exception:
                    pass  # Don't fail if correlation_state update fails

                return CorrelationUpdateResult.successful_update(session_id, correlation_id)
            else:
                return CorrelationUpdateResult.failed_update(session_id, correlation_id, "Update operation failed")
            
        except Exception as e:
            return CorrelationUpdateResult.failed_update(session_id or "", correlation_id or "", str(e))
    
    def check_consistency(self) -> ConsistencyCheckResult:
        """Check session correlation consistency across state files."""
        if not self.state_manager:
            if ConsistencyCheckResult:
                return ConsistencyCheckResult.check_failed("No state manager available")
            else:
                raise RuntimeError("State manager not available and ConsistencyCheckResult not imported")

        if not ConsistencyCheckResult:
            raise RuntimeError("ConsistencyCheckResult type not imported")
        
        try:
            unified_state = self.state_manager.get_unified_state()
            task_state = self.state_manager.get_task_state()
            
            # Check for consistency
            inconsistencies = []
            
            unified_session = unified_state.get("current_session", {}).get("session_id")
            unified_correlation = unified_state.get("current_session", {}).get("correlation_id")
            task_session = task_state.get("current_session", {}).get("session_id")
            
            if unified_session and task_session and unified_session != task_session:
                inconsistencies.append("Session ID mismatch between unified and task state")
            
            if not unified_correlation:
                inconsistencies.append("Missing correlation ID in unified state")
            
            if len(inconsistencies) == 0:
                return ConsistencyCheckResult.consistent_state(
                    unified_session=unified_session,
                    unified_correlation=unified_correlation,
                    task_session=task_session
                )
            else:
                return ConsistencyCheckResult.inconsistent_state(
                    inconsistencies=inconsistencies,
                    unified_session=unified_session,
                    unified_correlation=unified_correlation,
                    task_session=task_session
                )
            
        except Exception as e:
            return ConsistencyCheckResult.check_failed(str(e))
    
    def generate_ids(self) -> IdGenerationResult:
        """Generate new session and correlation IDs."""
        if not IdGenerationResult:
            # Fallback if dataclass not available
            session_id = self._generate_short_id()
            correlation_id = self._generate_short_id()
            return (session_id, correlation_id)  # Return tuple for backward compatibility
        
        session_id = self._generate_short_id()
        correlation_id = self._generate_short_id()
        return IdGenerationResult(session_id=session_id, correlation_id=correlation_id)
    
    def _generate_short_id(self) -> str:
        """Generate short UUID for correlation tracking."""
        return str(uuid.uuid4())[:8]


class ToolResponseAnalyzer:
    """Analyze tool responses for success/failure and metadata extraction."""
    
    def determine_success(self, tool_response: Dict[str, Any]) -> bool:
        """Determine if tool execution was successful."""
        if not tool_response:
            return False
        
        # Check explicit success field
        if "success" in tool_response:
            return bool(tool_response["success"])
        
        # Check for error indicators
        if tool_response.get("is_error", False):
            return False
        
        if "error" in tool_response:
            return False
        
        # Check for common failure indicators
        failure_indicators = ["failed", "error", "exception", "timeout"]
        response_text = str(tool_response).lower()
        if any(indicator in response_text for indicator in failure_indicators):
            return False
        
        return True
    
    def extract_error_info(self, tool_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract error information from tool response."""
        error_info = {
            "has_error": False,
            "error_type": None,
            "error_message": None,
            "error_details": None
        }
        
        if not tool_response:
            return error_info
        
        # Check for explicit error fields
        if tool_response.get("is_error", False):
            error_info["has_error"] = True
            error_info["error_type"] = "explicit_error"
            error_info["error_message"] = tool_response.get("error", "Unknown error")
        
        # Check for error field
        elif "error" in tool_response:
            error_info["has_error"] = True
            error_info["error_type"] = "error_field"
            error_info["error_message"] = str(tool_response["error"])
        
        # Check for exception information
        elif "exception" in tool_response:
            error_info["has_error"] = True
            error_info["error_type"] = "exception"
            error_info["error_message"] = str(tool_response["exception"])
        
        return error_info
    
    def get_execution_metrics(self, tool_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract execution metrics from tool response."""
        metrics = {
            "execution_time": None,
            "lines_processed": None,
            "files_affected": None,
            "has_metrics": False
        }
        
        if not tool_response:
            return metrics
        
        # Look for timing information
        if "execution_time" in tool_response:
            metrics["execution_time"] = tool_response["execution_time"]
            metrics["has_metrics"] = True
        
        if "duration" in tool_response:
            metrics["execution_time"] = tool_response["duration"]
            metrics["has_metrics"] = True
        
        # Look for processing metrics
        if "lines_processed" in tool_response:
            metrics["lines_processed"] = tool_response["lines_processed"]
            metrics["has_metrics"] = True
        
        if "files_affected" in tool_response:
            metrics["files_affected"] = tool_response["files_affected"]
            metrics["has_metrics"] = True
        
        return metrics


def create_subagent_manager(project_root: Path) -> SubagentContextManager:
    """Factory function for SubagentContextManager."""
    return SubagentContextManager(project_root)


def create_daic_controller(project_root: Path) -> DAICModeController:
    """Factory function for DAICModeController."""
    return DAICModeController(project_root)


def create_session_controller(project_root: Path) -> SessionCorrelationController:
    """Factory function for SessionCorrelationController."""
    return SessionCorrelationController(project_root)


def create_tool_analyzer() -> ToolResponseAnalyzer:
    """Factory function for ToolResponseAnalyzer."""
    return ToolResponseAnalyzer()