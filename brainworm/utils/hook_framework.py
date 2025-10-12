#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
# ]
# ///

"""
Unified Hook Framework for Brainworm Claude Code Hooks

This framework eliminates 800-1000 lines of duplicated boilerplate code across
all hook implementations by providing a unified interface for hook execution.

Usage Examples:
    # Simple hook (0 boilerplate):
    HookFramework("notification").execute()
    
    # Hook with custom data extraction:
    HookFramework("session_start").with_extractor(extract_session_data).execute()
    
    # Complex hook with custom logic:
    def custom_logic(framework):
        # Custom business logic here
        pass
    HookFramework("pre_tool_use").with_custom_logic(custom_logic).execute()
"""

import json
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, Union
from rich.console import Console

# Import sophisticated infrastructure systems
try:
    from .hook_types import (
        BaseHookInput, PreToolUseInput, PostToolUseInput, UserPromptSubmitInput,
        SessionStartInput, SessionEndInput, StopInput, NotificationInput,
        PreToolUseDecisionOutput, parse_log_event, get_standard_timestamp
    )
    from .event_logger import SessionEventLogger, create_event_logger
    from .debug_logger import DebugLogger, DebugConfig, create_debug_logger
    from .config import load_config
except ImportError:
    # Fallback imports for backward compatibility
    BaseHookInput = None
    PreToolUseInput = None
    PostToolUseInput = None
    UserPromptSubmitInput = None
    SessionStartInput = None
    SessionEndInput = None
    StopInput = None
    NotificationInput = None
    PreToolUseDecisionOutput = None
    parse_log_event = None
    get_standard_timestamp = lambda: datetime.now(timezone.utc).isoformat()
    SessionEventLogger = None
    create_event_logger = None
    DebugLogger = None
    DebugConfig = None
    create_debug_logger = None
    load_config = None


class HookFramework:
    """
    Unified framework for all brainworm Claude Code hooks.
    
    Eliminates massive code duplication by providing centralized handling of:
    - Input reading and JSON parsing
    - Project root discovery
    - sys.path manipulation and imports
    - Analytics processor setup and logging
    - Rich console output and success messages
    - Error handling and graceful failures
    - Command line argument processing
    
    Reduces individual hook files from 60-80 lines to 5-10 lines.
    """
    
    def __init__(self, hook_name: str, enable_analytics: bool = True, security_critical: bool = False):
        """
        Initialize framework for a specific hook.

        Args:
            hook_name: Name of the hook (e.g., "notification", "session_start")
            enable_analytics: Whether to enable event storage
            security_critical: Whether event logging failures should cause hook failure
        """
        self.hook_name = hook_name
        self.console = Console()
        self.execution_id: str = uuid.uuid4().hex[:12]  # Unique execution identifier

        # Capture which hook script file invoked the framework
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_file = frame.f_back.f_code.co_filename
            self.hook_script = Path(caller_file).name
        else:
            self.hook_script = "unknown"

        self.raw_input_data: Dict[str, Any] = {}
        self.typed_input: Optional[Union[BaseHookInput, PreToolUseInput, PostToolUseInput, UserPromptSubmitInput]] = None
        self.project_root: Optional[Path] = None
        self.session_id: str = "unknown"
        self.custom_logic_fn: Optional[Callable] = None
        self.data_extractor_fn: Optional[Callable] = None
        self.success_handler_fn: Optional[Callable] = None
        self.decision_output: Optional[PreToolUseDecisionOutput] = None
        
        # New framework execution modes
        self.json_response: Optional[Dict[str, Any]] = None
        self.exit_code: int = 0
        self.exit_message: str = ""
        
        # Infrastructure systems
        self.enable_event_logging = enable_analytics
        self.security_critical = security_critical
        self.event_logger: Optional[SessionEventLogger] = None
        self.debug_logger: Optional[DebugLogger] = None

        self._setup_environment()
    
    def _setup_environment(self) -> None:
        """Centralize sys.path manipulation and common imports with security validation."""
        try:
            # Secure path resolution with validation
            utils_path = Path(__file__).parent.resolve()
            templates_path = Path(__file__).parent.parent.resolve()
            
            # Validate paths exist and are directories before adding to sys.path
            if utils_path.exists() and utils_path.is_dir():
                utils_str = str(utils_path)
                if utils_str not in sys.path:
                    sys.path.insert(0, utils_str)
            
            if templates_path.exists() and templates_path.is_dir():
                templates_str = str(templates_path)
                if templates_str not in sys.path:
                    sys.path.insert(0, templates_str)
                    
        except Exception as e:
            # Sanitize error message to prevent information disclosure
            print("Warning: Environment setup failed due to path validation error", file=sys.stderr)
    
    def _read_input(self) -> None:
        """Read and parse JSON input from Claude Code stdin with type-safe processing."""
        try:
            input_text = sys.stdin.read()
            self.raw_input_data = json.loads(input_text) if input_text.strip() else {}
            self.session_id = self.raw_input_data.get('session_id', 'unknown')
            
            # Type-safe input processing using sophisticated schemas
            self._parse_typed_input()
            
        except json.JSONDecodeError:
            print("Warning: Invalid JSON input format", file=sys.stderr)
            self.raw_input_data = {}
        except Exception as e:
            # Sanitize error message to prevent information disclosure
            print("Warning: Input reading failed due to processing error", file=sys.stderr)
            self.raw_input_data = {}
    
    def _parse_typed_input(self) -> None:
        """Parse input using type-safe schemas from hook_types.py."""
        if not self.raw_input_data:
            return

        try:
            # Parse based on hook type for type-safe processing
            if self.hook_name in ('pre_tool_use', 'daic_pre_tool_use') and PreToolUseInput:
                self.typed_input = PreToolUseInput.parse(self.raw_input_data)
            elif self.hook_name == 'post_tool_use' and PostToolUseInput:
                self.typed_input = PostToolUseInput.parse(self.raw_input_data)
            elif self.hook_name == 'user_prompt_submit' and UserPromptSubmitInput:
                self.typed_input = UserPromptSubmitInput.parse(self.raw_input_data)
            elif self.hook_name == 'session_start' and SessionStartInput:
                self.typed_input = SessionStartInput.parse(self.raw_input_data)
            elif self.hook_name == 'session_end' and SessionEndInput:
                self.typed_input = SessionEndInput.parse(self.raw_input_data)
            elif self.hook_name == 'stop' and StopInput:
                self.typed_input = StopInput.parse(self.raw_input_data)
            elif self.hook_name == 'notification' and NotificationInput:
                self.typed_input = NotificationInput.parse(self.raw_input_data)
            elif BaseHookInput:
                # Fallback to base input for other hooks
                self.typed_input = BaseHookInput.parse(self.raw_input_data)
        except Exception as e:
            # Log the actual error for debugging
            if '--verbose' in sys.argv:
                print(f"Warning: Type-safe parsing failed for {self.hook_name}: {type(e).__name__}: {e}", file=sys.stderr)
            else:
                print(f"Warning: Type-safe parsing failed for {self.hook_name}, using raw input", file=sys.stderr)
            # Continue with raw input
    
    def _discover_project_root(self) -> None:
        """Discover project root with fallback strategy."""
        try:
            from utils.project import find_project_root
            self.project_root = find_project_root()
        except (ImportError, RuntimeError):
            # Fallback to current directory
            self.project_root = Path.cwd()
        except Exception as e:
            # Sanitize error message to prevent information disclosure
            print("Warning: Project root discovery failed, using current directory", file=sys.stderr)
            self.project_root = Path.cwd()
        
        # Initialize sophisticated infrastructure systems now that we have project root
        self._initialize_infrastructure()
    
    def _initialize_infrastructure(self) -> None:
        """Initialize advanced analytics and logging infrastructure."""
        if not self.project_root:
            return

        try:
            # Load debug configuration and initialize debug logger
            if create_debug_logger and load_config:
                config = load_config(self.project_root)
                debug_config_data = config.get('debug', {})
                debug_config = DebugConfig.from_dict(debug_config_data) if DebugConfig else None
                self.debug_logger = create_debug_logger(
                    self.hook_name,
                    self.project_root,
                    debug_config,
                    check_verbose_flag=True
                )

            # Initialize event logger with Claude Code session correlation
            if self.enable_event_logging and create_event_logger:
                event_logging_enabled = '--analytics' in sys.argv  # TODO: Update flag name
                self.event_logger = create_event_logger(
                    self.project_root, self.hook_name,
                    enable_analytics=event_logging_enabled,  # TODO: Update parameter name
                    session_id=self.session_id
                )
        except Exception as e:
            # Sanitize error message to prevent information disclosure
            print("Warning: Infrastructure initialization failed, using fallback systems", file=sys.stderr)
    
    def _process_event_logging(self) -> bool:
        """Process event logging with session correlation."""
        if not self.event_logger:
            return True  # Skip if event logger not available

        try:
            debug_mode = self.debug_logger.is_enabled() if self.debug_logger else False

            # Use hook-specific event logging methods based on hook type
            if self.hook_name in ('pre_tool_use', 'daic_pre_tool_use'):
                success = self.event_logger.log_pre_tool_execution(self.raw_input_data, debug=debug_mode)
            elif self.hook_name == 'post_tool_use':
                success = self.event_logger.log_post_tool_execution(self.raw_input_data, debug=debug_mode)
            elif self.hook_name == 'user_prompt_submit':
                success = self.event_logger.log_user_prompt(self.raw_input_data, debug=debug_mode)
            else:
                # General event logging with session context
                success = self.event_logger.log_event_with_analytics(self.raw_input_data, debug=debug_mode)

            if self.debug_logger:
                if success:
                    self.debug_logger.debug("Event logging processed", execution_id=self.execution_id)
                else:
                    self.debug_logger.warning("Event logging failed", execution_id=self.execution_id)

            return success

        except Exception as e:
            # Sanitize error message to prevent information disclosure
            error_msg = "Warning: Event logging failed"
            if self.security_critical:
                error_msg += " - SECURITY CRITICAL FAILURE"
                print(error_msg, file=sys.stderr)
                raise RuntimeError("Security-critical event logging failure")
            else:
                error_msg += ", continuing without event logging"
                print(error_msg, file=sys.stderr)
                return False
    
    def _show_success(self) -> None:
        """Display success message with standardized formatting."""
        if self.debug_logger and self.debug_logger.is_enabled():
            if self.success_handler_fn:
                try:
                    self.success_handler_fn(self)
                except Exception as e:
                    # Sanitize error message to prevent information disclosure
                    print("Warning: Custom success handler failed, using standard message", file=sys.stderr)
                    # Fall back to standard message
                    self._standard_success_message()
            else:
                self._standard_success_message()
    
    def _standard_success_message(self) -> None:
        """Show standard success message."""
        session_short = self.session_id[:8] if len(self.session_id) >= 8 else self.session_id
        print(f"✅ {self.hook_name} completed: {session_short}", file=sys.stderr)
    
    def _handle_error(self, error: Exception) -> None:
        """Centralized error handling with consistent formatting."""
        print(f"Error in {self.hook_name} hook: {error}", file=sys.stderr)
        sys.exit(1)
    
    def with_custom_logic(self, logic_fn: Callable[['HookFramework', Any], None]) -> 'HookFramework':
        """
        Add custom business logic to be executed within the framework.
        
        BREAKING CHANGE: Custom logic functions MUST accept (framework, typed_input) parameters.
        
        Args:
            logic_fn: Function that accepts (framework, typed_input) and performs custom logic
            
        Returns:
            Self for method chaining
            
        Example:
            def pre_tool_use_logic(framework: HookFramework, typed_input: PreToolUseInput):
                tool_name = typed_input.tool_name
                if should_block_tool(typed_input):
                    framework.block_tool("DAIC violation", [f"Tool {tool_name} blocked"])
                else:
                    framework.approve_tool()
            
            HookFramework("pre_tool_use").with_custom_logic(pre_tool_use_logic).execute()
        """
        self.custom_logic_fn = logic_fn
        return self
    
    def with_extractor(self, extractor_fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> 'HookFramework':
        """
        Add custom data extractor for analytics.
        
        Args:
            extractor_fn: Function that extracts custom data from raw input
            
        Returns:
            Self for method chaining
            
        Example:
            def extract_notification_data(raw_input):
                return {'message': raw_input.get('message', 'Unknown')}
            
            HookFramework("notification").with_extractor(extract_notification_data).execute()
        """
        self.data_extractor_fn = extractor_fn
        return self
    
    def with_success_handler(self, handler_fn: Callable) -> 'HookFramework':
        """
        Add custom success message handler.
        
        Args:
            handler_fn: Function that handles success output
            
        Returns:
            Self for method chaining
        """
        self.success_handler_fn = handler_fn
        return self
    
    def set_json_response(self, response_data: Dict[str, Any]) -> 'HookFramework':
        """
        DEPRECATED: Use set_typed_response() for type-safe response handling.
        
        Args:
            response_data: Dictionary to be serialized as JSON to stdout
            
        Returns:
            Self for method chaining
        """
        self.json_response = response_data
        return self
        
    def set_typed_response(self, response_schema) -> 'HookFramework':
        """
        Set typed response using schema classes for Claude Code compliance.
        
        Args:
            response_schema: Schema object with .to_dict() method (e.g. UserPromptContextResponse)
            
        Returns:
            Self for method chaining
        """
        if not hasattr(response_schema, 'to_dict'):
            raise ValueError(f"Response schema must have .to_dict() method, got: {type(response_schema)}")
        
        self.json_response = response_schema.to_dict()
        return self
    
    # DEPRECATED METHOD REMOVED: set_exit_decision() 
    # Use approve_tool() or block_tool() for type-safe decisions
    
    def approve_tool(self, reason: Optional[str] = None) -> 'HookFramework':
        """
        Approve tool execution (for pre_tool_use hooks).
        
        Args:
            reason: Optional reason for approval
            
        Returns:
            Self for method chaining
        """
        if PreToolUseDecisionOutput:
            self.decision_output = PreToolUseDecisionOutput.approve(reason, self.session_id)
        return self
    
    def block_tool(self, reason: str, validation_issues: list = None, suppress_output: bool = False) -> 'HookFramework':
        """
        Block tool execution (for pre_tool_use hooks).
        
        Args:
            reason: Reason for blocking
            validation_issues: List of validation issues
            suppress_output: Whether to suppress Claude Code output
            
        Returns:
            Self for method chaining
        """
        if PreToolUseDecisionOutput:
            issues = validation_issues or [reason]
            self.decision_output = PreToolUseDecisionOutput.block(
                reason, issues, self.session_id, suppress_output
            )
        return self
    
    def _output_decision(self) -> None:
        """Output decision for pre_tool_use hooks using official Claude Code format."""
        if self.hook_name in ('pre_tool_use', 'daic_pre_tool_use') and self.decision_output:
            try:
                decision_dict = self.decision_output.to_dict()
                # Secure JSON output with ASCII encoding to prevent injection
                print(json.dumps(decision_dict, ensure_ascii=True, separators=(',', ':')))
            except Exception as e:
                # Sanitize error message to prevent information disclosure
                print("Warning: Decision output formatting failed", file=sys.stderr)
    
    def _output_json_response(self) -> None:
        """Output JSON response for hooks that provide context to Claude."""
        if self.json_response:
            try:
                # Use centralized debug logger for framework output (if configured)
                if self.debug_logger and self.debug_logger.debug_config.outputs.framework:
                    json_str = json.dumps(self.json_response)
                    self.debug_logger.trace(f"JSON TO STDOUT: {json_str}", execution_id=self.execution_id)

                # Secure JSON output with ASCII encoding to prevent injection
                print(json.dumps(self.json_response, ensure_ascii=True, separators=(',', ':')))
                sys.stdout.flush()  # Ensure JSON reaches Claude Code
            except Exception as e:
                # Emergency fallback - always provide some JSON
                fallback_response = {"context": ""}
                print(json.dumps(fallback_response))
                if self.debug_logger and self.debug_logger.is_enabled():
                    self.debug_logger.warning(f"JSON response formatting failed: {e}", execution_id=self.execution_id)
    
    def execute(self) -> None:
        """
        Execute the complete hook lifecycle.

        Lifecycle:
        1. Read and parse JSON input from stdin with type-safe processing
        2. Discover project root and initialize infrastructure systems
        3. Execute custom business logic (if provided)
        4. Process event logging with session correlation
        5. Output decision (for pre_tool_use hooks) or JSON response
        6. Display success message (if debug enabled)
        7. Handle errors gracefully
        """
        try:
            # 1. Read input with type-safe parsing (eliminates 10+ lines per hook)
            self._read_input()

            # 2. Discover project root and initialize infrastructure (eliminates 20+ lines per hook)
            self._discover_project_root()

            # Add execution_id and hook_script to raw_input_data for downstream systems
            self.raw_input_data['execution_id'] = self.execution_id
            self.raw_input_data['hook_script'] = self.hook_script

            if self.debug_logger:
                self.debug_logger.info(f"Hook {self.hook_name} [{self.hook_script}] executing (session: {self.session_id[:8]})", execution_id=self.execution_id)
                self.debug_logger.debug(f"Typed input available: {self.typed_input is not None and not isinstance(self.typed_input, dict)}", execution_id=self.execution_id)

            # 3. Execute custom logic if provided
            # Pass typed input if available, otherwise pass raw input for backward compatibility
            if self.custom_logic_fn:
                try:
                    if self.debug_logger:
                        self.debug_logger.debug(f"Executing custom logic for {self.hook_name}", execution_id=self.execution_id)

                    # Use typed input if available, otherwise fall back to raw input
                    input_to_pass = self.typed_input if self.typed_input else self.raw_input_data
                    self.custom_logic_fn(self, input_to_pass)

                    if self.debug_logger:
                        self.debug_logger.debug(f"Custom logic completed successfully", execution_id=self.execution_id)
                except Exception as e:
                    if self.debug_logger:
                        self.debug_logger.error(f"Custom logic failed: {type(e).__name__}: {str(e)}", execution_id=self.execution_id)
                    # Sanitize error message to prevent information disclosure
                    print(f"Error: Custom logic failed for {self.hook_name}: {str(e)}", file=sys.stderr)
                    sys.exit(1)

            # 4. Process event logging with session correlation (eliminates 40+ lines per hook)
            self._process_event_logging()

            # 5. Output decision or JSON response
            self._output_decision()
            self._output_json_response()
            
            # 7. Show success message (eliminates 5 lines per hook)
            self._show_success()
            
            # 8. Exit with specified code
            if self.exit_message:
                print(self.exit_message, file=sys.stderr)
            sys.exit(self.exit_code)
            
        except Exception as e:
            self._handle_error(e)


# Convenience functions for common data extraction patterns
def extract_file_data(raw_input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract file-related data for file operation hooks."""
    tool_input = raw_input_data.get('tool_input', {})
    extra_data = {}
    
    if file_path := tool_input.get('file_path'):
        extra_data['file_path'] = file_path
    
    return extra_data


def extract_command_data(raw_input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract command data for bash operation hooks."""
    tool_input = raw_input_data.get('tool_input', {})
    extra_data = {}
    
    if command := tool_input.get('command'):
        extra_data['command'] = command
    
    return extra_data


def extract_tool_data(raw_input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract tool execution data for tool operation hooks."""
    extra_data = {}
    
    if tool_name := raw_input_data.get('tool_name'):
        extra_data['tool_name'] = tool_name
    
    if tool_response := raw_input_data.get('tool_response'):
        # Determine success from tool response
        if isinstance(tool_response, dict):
            if tool_response.get('is_error', False):
                extra_data['tool_success'] = False
            elif 'success' in tool_response:
                extra_data['tool_success'] = tool_response['success']
            else:
                extra_data['tool_success'] = True
    
    return extra_data


def extract_prompt_data(raw_input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract basic prompt data for prompt submission hooks."""
    prompt = raw_input_data.get('prompt', '')
    
    return {
        'prompt_info': {
            'length_chars': len(prompt),
            'word_count': len(prompt.split()),
            'has_question': '?' in prompt,
            'has_code_references': bool('`' in prompt or '.py' in prompt or '.js' in prompt),
            'is_empty': len(prompt.strip()) == 0
        }
    }


def extract_session_data(raw_input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract session-related data for session management hooks."""
    return {
        'session_id': raw_input_data.get('session_id', 'unknown'),
        'user_id': raw_input_data.get('user_id', 'unknown')
    }


def extract_notification_data(raw_input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract notification data for notification hooks."""
    return {
        'message': raw_input_data.get('message', 'Unknown notification'),
        'notification_type': raw_input_data.get('type', 'generic')
    }


# Legacy compatibility function
def create_standard_raw_hook(hook_name: str, extract_extra_data_fn=None):
    """
    Legacy compatibility function - use HookFramework class instead.
    
    This function is preserved for backward compatibility but HookFramework
    provides better features and cleaner interface.
    """
    def hook_main():
        if extract_extra_data_fn:
            HookFramework(hook_name).with_extractor(extract_extra_data_fn).execute()
        else:
            HookFramework(hook_name).execute()
    
    return hook_main


if __name__ == '__main__':
    # This is a framework module, not a standalone hook
    print("Hook Framework - use HookFramework class in your hooks", file=sys.stderr)
    sys.exit(1)