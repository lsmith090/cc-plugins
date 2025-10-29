#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Centralized Debug Logging System for Brainworm
Provides unified, configuration-driven debug output control.
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Debug level hierarchy (lower number = higher priority)
DEBUG_LEVELS = {
    "ERROR": 0,  # Only errors
    "WARNING": 1,  # Errors + warnings
    "INFO": 2,  # Normal operations
    "DEBUG": 3,  # Detailed debugging
    "TRACE": 4,  # Everything including internal state
}


@dataclass
class DebugOutputs:
    """Configuration for debug output destinations."""

    stderr: bool = True
    stderr_format: str = "text"
    file: bool = False
    file_format: str = "json"
    framework: bool = False
    framework_format: str = "json"

    @classmethod
    def from_dict(cls, data: dict) -> "DebugOutputs":
        """Create from dictionary."""
        return cls(
            stderr=data.get("stderr", True),
            stderr_format=data.get("stderr_format", "text"),
            file=data.get("file", False),
            file_format=data.get("file_format", "json"),
            framework=data.get("framework", False),
            framework_format=data.get("framework_format", "json"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "stderr": self.stderr,
            "stderr_format": self.stderr_format,
            "file": self.file,
            "file_format": self.file_format,
            "framework": self.framework,
            "framework_format": self.framework_format,
        }


@dataclass
class DebugConfig:
    """Configuration for debug logging behavior."""

    enabled: bool = False
    level: str = "INFO"
    format: str = "text"
    outputs: DebugOutputs = field(default_factory=DebugOutputs)

    @classmethod
    def from_dict(cls, data: dict) -> "DebugConfig":
        """Create from dictionary (loaded from config.toml)."""
        outputs_data = data.get("outputs", {})
        outputs = DebugOutputs.from_dict(outputs_data)
        return cls(
            enabled=data.get("enabled", False),
            level=data.get("level", "INFO").upper(),
            format=data.get("format", "text"),
            outputs=outputs,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {"enabled": self.enabled, "level": self.level, "format": self.format, "outputs": self.outputs.to_dict()}


class DebugLogger:
    """
    Centralized debug logger for brainworm hooks and utilities.

    Provides configuration-driven debug output with level control,
    CLI flag override support, and multiple output destinations.
    """

    def __init__(
        self,
        hook_name: str,
        project_root: Optional[Path] = None,
        debug_config: Optional[DebugConfig] = None,
        verbose_override: bool = False,
    ):
        """
        Initialize debug logger.

        Args:
            hook_name: Name of the hook or component using the logger
            project_root: Project root directory (for file logging)
            debug_config: Debug configuration from config.toml
            verbose_override: Whether --verbose CLI flag was detected
        """
        self.hook_name = hook_name
        self.project_root = project_root
        self.verbose_override = verbose_override

        # Apply CLI override if present
        if verbose_override and debug_config:
            self.debug_config = DebugConfig(enabled=True, level="DEBUG", outputs=debug_config.outputs)
        elif debug_config:
            self.debug_config = debug_config
        else:
            # Fallback to disabled debug
            self.debug_config = DebugConfig(enabled=False)

    def is_enabled(self) -> bool:
        """Check if debug output is enabled."""
        return self.verbose_override or self.debug_config.enabled

    def should_output_level(self, level: str) -> bool:
        """
        Check if a debug level should be output.

        Args:
            level: Debug level (ERROR, WARNING, INFO, DEBUG, TRACE)

        Returns:
            True if this level should be output
        """
        if not self.is_enabled():
            return False

        current_level = DEBUG_LEVELS.get(self.debug_config.level, 2)
        requested_level = DEBUG_LEVELS.get(level.upper(), 2)
        return requested_level <= current_level

    def _format_message(self, message: str, level: str, execution_id: Optional[str], format_type: str) -> str:
        """
        Format a message according to the specified format type.

        Args:
            message: The log message
            level: Debug level (ERROR, WARNING, INFO, DEBUG, TRACE)
            execution_id: Optional unique execution identifier
            format_type: Format type ("text" or "json")

        Returns:
            Formatted message string
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        if format_type == "json":
            log_entry = {
                "timestamp": timestamp,
                "level": level.upper(),
                "hook_name": self.hook_name,
                "message": message,
            }
            if execution_id:
                log_entry["execution_id"] = execution_id
            if self.project_root:
                log_entry["project_root"] = str(self.project_root)
            return json.dumps(log_entry, ensure_ascii=False)
        else:  # text format
            exec_id_str = f" [exec:{execution_id}]" if execution_id else ""
            return f"[{timestamp}] [{level.upper()}]{exec_id_str} {self.hook_name}: {message}"

    def log(self, message: str, level: str = "INFO", execution_id: Optional[str] = None) -> None:
        """
        Log a debug message according to configuration.

        Args:
            message: Message to log
            level: Debug level (ERROR, WARNING, INFO, DEBUG, TRACE)
            execution_id: Optional unique execution identifier
        """
        if not self.should_output_level(level):
            return

        # Output to stderr if configured
        if self.debug_config.outputs.stderr:
            stderr_format = self.debug_config.outputs.stderr_format
            formatted = self._format_message(message, level, execution_id, stderr_format)
            print(formatted, file=sys.stderr)

        # Output to file if configured and project root available
        if self.debug_config.outputs.file and self.project_root:
            file_format = self.debug_config.outputs.file_format
            formatted = self._format_message(message, level, execution_id, file_format)
            self._write_to_file(formatted, file_format)

        # Output to framework debug log if configured
        if self.debug_config.outputs.framework and self.project_root:
            framework_format = self.debug_config.outputs.framework_format
            formatted = self._format_message(message, level, execution_id, framework_format)
            self._write_to_framework_log(formatted, framework_format)

    def _write_to_file(self, formatted_message: str, format_type: str) -> None:
        """
        Write debug message to debug log file.

        Args:
            formatted_message: Formatted log message
            format_type: Format type ("text" or "json") - determines file extension
        """
        try:
            # Choose file extension based on format
            if format_type == "json":
                debug_file = self.project_root / ".brainworm" / "logs" / "debug.jsonl"
            else:
                debug_file = self.project_root / ".brainworm" / "logs" / "debug.log"

            debug_file.parent.mkdir(parents=True, exist_ok=True)
            with open(debug_file, "a", encoding="utf-8") as f:
                f.write(formatted_message + "\n")
                f.flush()
        except Exception as e:
            # Don't fail hook on debug logging errors, but report to stderr as last resort
            print(f"Debug logger failed: {e}", file=sys.stderr)

    def _write_to_framework_log(self, formatted_message: str, format_type: str) -> None:
        """
        Write debug message to framework debug log.

        Args:
            formatted_message: Formatted log message
            format_type: Format type ("text" or "json") - determines file extension
        """
        try:
            # Choose file extension based on format
            if format_type == "json":
                framework_log = self.project_root / ".brainworm" / "logs" / "debug_framework_output.jsonl"
            else:
                framework_log = self.project_root / ".brainworm" / "logs" / "debug_framework_output.log"

            framework_log.parent.mkdir(parents=True, exist_ok=True)
            with open(framework_log, "a", encoding="utf-8") as f:
                f.write(formatted_message + "\n")
                f.flush()
        except Exception as e:
            # Don't fail hook on debug logging errors, but report to stderr as last resort
            print(f"Framework debug logger failed: {e}", file=sys.stderr)

    def error(self, message: str, execution_id: Optional[str] = None) -> None:
        """Log an error message."""
        self.log(message, level="ERROR", execution_id=execution_id)

    def warning(self, message: str, execution_id: Optional[str] = None) -> None:
        """Log a warning message."""
        self.log(message, level="WARNING", execution_id=execution_id)

    def info(self, message: str, execution_id: Optional[str] = None) -> None:
        """Log an info message."""
        self.log(message, level="INFO", execution_id=execution_id)

    def debug(self, message: str, execution_id: Optional[str] = None) -> None:
        """Log a debug message."""
        self.log(message, level="DEBUG", execution_id=execution_id)

    def trace(self, message: str, execution_id: Optional[str] = None) -> None:
        """Log a trace message."""
        self.log(message, level="TRACE", execution_id=execution_id)


def get_default_debug_config() -> DebugConfig:
    """Get default debug configuration."""
    return DebugConfig(
        enabled=False,
        level="INFO",
        format="text",
        outputs=DebugOutputs(
            stderr=True, stderr_format="text", file=False, file_format="json", framework=False, framework_format="json"
        ),
    )


def create_debug_logger(
    hook_name: str,
    project_root: Optional[Path] = None,
    debug_config: Optional[DebugConfig] = None,
    check_verbose_flag: bool = True,
) -> DebugLogger:
    """
    Factory function to create a debug logger.

    Args:
        hook_name: Name of the hook or component
        project_root: Project root directory
        debug_config: Debug configuration from config.toml
        check_verbose_flag: Whether to check for --verbose in sys.argv

    Returns:
        DebugLogger instance
    """
    verbose_override = check_verbose_flag and "--verbose" in sys.argv

    if debug_config is None:
        debug_config = get_default_debug_config()

    return DebugLogger(
        hook_name=hook_name, project_root=project_root, debug_config=debug_config, verbose_override=verbose_override
    )


if __name__ == "__main__":
    # Test the debug logger
    print("Testing centralized debug logger...\n", file=sys.stderr)

    # Test with different configurations
    test_configs = [
        ("Disabled", DebugConfig(enabled=False, level="INFO")),
        ("Enabled INFO", DebugConfig(enabled=True, level="INFO")),
        ("Enabled DEBUG", DebugConfig(enabled=True, level="DEBUG")),
        ("Enabled TRACE", DebugConfig(enabled=True, level="TRACE")),
    ]

    for config_name, config in test_configs:
        print(f"\n=== Testing {config_name} ===", file=sys.stderr)
        logger = DebugLogger("test_hook", debug_config=config)

        logger.error("This is an error")
        logger.warning("This is a warning")
        logger.info("This is info")
        logger.debug("This is debug")
        logger.trace("This is trace")

    print("\n=== Testing --verbose Override ===", file=sys.stderr)
    logger = DebugLogger("test_hook", debug_config=DebugConfig(enabled=False), verbose_override=True)
    logger.info("This should appear even though config is disabled")
    logger.debug("This should also appear")

    print("\n=== Testing JSON Format ===", file=sys.stderr)
    json_outputs = DebugOutputs(stderr=True, stderr_format="json", file=False, framework=False)
    json_config = DebugConfig(enabled=True, level="INFO", format="json", outputs=json_outputs)
    json_logger = DebugLogger("test_hook", debug_config=json_config)
    json_logger.info("This is JSON formatted output", execution_id="test-123")
    json_logger.error("This is a JSON error")

    print("\n=== Testing Mixed Formats ===", file=sys.stderr)
    print("(stderr=text, file=json, framework=json)", file=sys.stderr)
    mixed_outputs = DebugOutputs(
        stderr=True,
        stderr_format="text",
        file=False,
        file_format="json",  # Would write to .jsonl
        framework=False,
        framework_format="json",  # Would write to .jsonl
    )
    mixed_config = DebugConfig(enabled=True, level="DEBUG", format="text", outputs=mixed_outputs)
    mixed_logger = DebugLogger("test_hook", debug_config=mixed_config)
    mixed_logger.info("Mixed format test - stderr is text")
    mixed_logger.debug("File and framework would be JSON")

    print("\nDebug logger tests complete!", file=sys.stderr)
