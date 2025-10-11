#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Centralized Debug Logging System for Brainworm
Provides unified, configuration-driven debug output control.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field


# Debug level hierarchy (lower number = higher priority)
DEBUG_LEVELS = {
    'ERROR': 0,    # Only errors
    'WARNING': 1,  # Errors + warnings
    'INFO': 2,     # Normal operations
    'DEBUG': 3,    # Detailed debugging
    'TRACE': 4     # Everything including internal state
}


@dataclass
class DebugOutputs:
    """Configuration for debug output destinations."""
    stderr: bool = True
    file: bool = False
    framework: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> 'DebugOutputs':
        """Create from dictionary."""
        return cls(
            stderr=data.get('stderr', True),
            file=data.get('file', False),
            framework=data.get('framework', False)
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'stderr': self.stderr,
            'file': self.file,
            'framework': self.framework
        }


@dataclass
class DebugConfig:
    """Configuration for debug logging behavior."""
    enabled: bool = False
    level: str = "INFO"
    outputs: DebugOutputs = field(default_factory=DebugOutputs)

    @classmethod
    def from_dict(cls, data: dict) -> 'DebugConfig':
        """Create from dictionary (loaded from config.toml)."""
        outputs_data = data.get('outputs', {})
        outputs = DebugOutputs.from_dict(outputs_data)
        return cls(
            enabled=data.get('enabled', False),
            level=data.get('level', 'INFO').upper(),
            outputs=outputs
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'enabled': self.enabled,
            'level': self.level,
            'outputs': self.outputs.to_dict()
        }


class DebugLogger:
    """
    Centralized debug logger for brainworm hooks and utilities.

    Provides configuration-driven debug output with level control,
    CLI flag override support, and multiple output destinations.
    """

    def __init__(self, hook_name: str, project_root: Optional[Path] = None,
                 debug_config: Optional[DebugConfig] = None,
                 verbose_override: bool = False):
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
            self.debug_config = DebugConfig(
                enabled=True,
                level='DEBUG',
                outputs=debug_config.outputs
            )
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

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Log a debug message according to configuration.

        Args:
            message: Message to log
            level: Debug level (ERROR, WARNING, INFO, DEBUG, TRACE)
        """
        if not self.should_output_level(level):
            return

        timestamp = datetime.now(timezone.utc).isoformat()
        formatted = f"[{timestamp}] [{level.upper()}] {self.hook_name}: {message}"

        # Output to stderr if configured
        if self.debug_config.outputs.stderr:
            print(formatted, file=sys.stderr)

        # Output to file if configured and project root available
        if self.debug_config.outputs.file and self.project_root:
            self._write_to_file(formatted)

        # Output to framework debug log if configured
        if self.debug_config.outputs.framework and self.project_root:
            self._write_to_framework_log(formatted)

    def _write_to_file(self, formatted_message: str) -> None:
        """Write debug message to debug.log file."""
        try:
            debug_file = self.project_root / '.brainworm' / 'logs' / 'debug.log'
            debug_file.parent.mkdir(parents=True, exist_ok=True)
            with open(debug_file, 'a', encoding='utf-8') as f:
                f.write(formatted_message + '\n')
                f.flush()
        except Exception:
            # Don't fail hook on debug logging errors
            pass

    def _write_to_framework_log(self, formatted_message: str) -> None:
        """Write debug message to framework debug log."""
        try:
            framework_log = self.project_root / '.brainworm' / 'debug_framework_output.log'
            framework_log.parent.mkdir(parents=True, exist_ok=True)
            with open(framework_log, 'a', encoding='utf-8') as f:
                f.write(formatted_message + '\n')
                f.flush()
        except Exception:
            # Don't fail hook on debug logging errors
            pass

    def error(self, message: str) -> None:
        """Log an error message."""
        self.log(message, level='ERROR')

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.log(message, level='WARNING')

    def info(self, message: str) -> None:
        """Log an info message."""
        self.log(message, level='INFO')

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.log(message, level='DEBUG')

    def trace(self, message: str) -> None:
        """Log a trace message."""
        self.log(message, level='TRACE')


def get_default_debug_config() -> DebugConfig:
    """Get default debug configuration."""
    return DebugConfig(
        enabled=False,
        level='INFO',
        outputs=DebugOutputs(stderr=True, file=False, framework=False)
    )


def create_debug_logger(hook_name: str, project_root: Optional[Path] = None,
                       debug_config: Optional[DebugConfig] = None,
                       check_verbose_flag: bool = True) -> DebugLogger:
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
    verbose_override = check_verbose_flag and '--verbose' in sys.argv

    if debug_config is None:
        debug_config = get_default_debug_config()

    return DebugLogger(
        hook_name=hook_name,
        project_root=project_root,
        debug_config=debug_config,
        verbose_override=verbose_override
    )


if __name__ == '__main__':
    # Test the debug logger
    print("Testing centralized debug logger...\n", file=sys.stderr)

    # Test with different configurations
    test_configs = [
        ("Disabled", DebugConfig(enabled=False, level='INFO')),
        ("Enabled INFO", DebugConfig(enabled=True, level='INFO')),
        ("Enabled DEBUG", DebugConfig(enabled=True, level='DEBUG')),
        ("Enabled TRACE", DebugConfig(enabled=True, level='TRACE')),
    ]

    for config_name, config in test_configs:
        print(f"\n=== Testing {config_name} ===", file=sys.stderr)
        logger = DebugLogger('test_hook', debug_config=config)

        logger.error("This is an error")
        logger.warning("This is a warning")
        logger.info("This is info")
        logger.debug("This is debug")
        logger.trace("This is trace")

    print("\n=== Testing --verbose Override ===", file=sys.stderr)
    logger = DebugLogger('test_hook', debug_config=DebugConfig(enabled=False), verbose_override=True)
    logger.info("This should appear even though config is disabled")
    logger.debug("This should also appear")

    print("\nDebug logger tests complete!", file=sys.stderr)
