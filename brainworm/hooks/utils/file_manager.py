#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Safe file operations with atomic writes and state management.

This module provides AtomicFileWriter and StateFileManager classes for safe
file operations across brainworm components, eliminating the scattered manual
JSON file handling patterns and providing consistency, error recovery, and
atomic operations.
"""

import json
import shutil
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional, List, Union, Callable, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class FileManagerConfig:
    """Configuration for file management operations"""
    backup_count: int = 5
    create_parents: bool = True
    atomic_writes: bool = True
    backup_on_update: bool = True
    json_indent: Optional[int] = 2
    json_sort_keys: bool = False
    file_permissions: int = 0o644
    dir_permissions: int = 0o755

class AtomicFileWriter:
    """
    Context manager for atomic file writing operations.
    
    This class ensures that file writes are atomic - either the entire
    operation succeeds or the file is left unchanged. It uses a temporary
    file and atomic rename operation to achieve this.
    """
    
    def __init__(self,
                 file_path: Path,
                 mode: str = 'w',
                 encoding: str = 'utf-8',
                 create_backup: bool = False,
                 backup_suffix: str = '.backup',
                 backup_count: int = 5):
        self.file_path = file_path
        self.mode = mode
        self.encoding = encoding
        self.create_backup = create_backup
        self.backup_suffix = backup_suffix
        self.backup_count = backup_count

        self.temp_path = None
        self.backup_path = None
        self.file_handle = None
        self._original_exists = False
    
    def __enter__(self):
        """Enter the context and prepare for atomic write"""
        # Create parent directories if they don't exist
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if original file exists
        self._original_exists = self.file_path.exists()
        
        # Create backup if requested and file exists
        if self.create_backup and self._original_exists:
            self.backup_path = self._create_backup()
        
        # Create temporary file in the same directory as target
        # This ensures the rename operation is atomic (same filesystem)
        temp_dir = self.file_path.parent
        temp_fd, temp_path = tempfile.mkstemp(
            dir=temp_dir,
            prefix=f".{self.file_path.name}.",
            suffix=".tmp"
        )
        
        self.temp_path = Path(temp_path)
        
        # Close the file descriptor and open with the requested mode
        import os
        os.close(temp_fd)
        
        self.file_handle = open(self.temp_path, self.mode, encoding=self.encoding)
        return self.file_handle
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and finalize the atomic operation"""
        if self.file_handle:
            self.file_handle.close()
        
        if exc_type is None:
            # No exception occurred, atomically rename temp file to target
            if self.temp_path and self.temp_path.exists():
                try:
                    # Set proper permissions
                    self.temp_path.chmod(0o644)
                    
                    # Atomic rename
                    self.temp_path.replace(self.file_path)
                    logger.debug(f"Atomically wrote file {self.file_path}")
                    
                except Exception as e:
                    logger.error(f"Failed to atomically replace {self.file_path}: {e}")
                    self._cleanup_temp_file()
                    raise
        else:
            # Exception occurred, clean up temp file
            self._cleanup_temp_file()
            logger.debug(f"Cleaned up temporary file due to exception: {exc_type.__name__}")
    
    def _create_backup(self) -> Path:
        """Create a backup of the existing file and cleanup old backups"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup_path = self.file_path.with_name(
            f"{self.file_path.name}{self.backup_suffix}_{timestamp}"
        )

        try:
            shutil.copy2(self.file_path, backup_path)
            logger.debug(f"Created backup at {backup_path}")

            # Clean up old backups
            self._cleanup_old_backups()

            return backup_path
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
            return None

    def _cleanup_old_backups(self):
        """Clean up old backup files, keeping only the most recent backups"""
        backup_pattern = f"{self.file_path.name}{self.backup_suffix}_*"
        backup_files = list(self.file_path.parent.glob(backup_pattern))

        if len(backup_files) > self.backup_count:
            # Sort by modification time, newest first
            backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            # Remove excess backups
            for backup_file in backup_files[self.backup_count:]:
                try:
                    backup_file.unlink()
                    logger.debug(f"Removed old backup {backup_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove old backup {backup_file}: {e}")
    
    def _cleanup_temp_file(self):
        """Clean up the temporary file"""
        if self.temp_path and self.temp_path.exists():
            try:
                self.temp_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {self.temp_path}: {e}")

class StateFileManager:
    """
    Manager for brainworm state files with validation, atomic operations,
    and backup management.
    
    This class provides a high-level interface for managing JSON state files
    with proper error handling, validation, and atomic operations.
    """
    
    def __init__(self, 
                 state_dir: Path,
                 config: Optional[FileManagerConfig] = None):
        self.state_dir = state_dir
        self.config = config or FileManagerConfig()
        self._lock = threading.RLock()
        
        # Ensure state directory exists
        if self.config.create_parents:
            self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def read_json_file(self, 
                      file_path: Path, 
                      default: Optional[Any] = None,
                      validate_func: Optional[Callable[[Any], bool]] = None) -> Any:
        """
        Read a JSON file with error handling and optional validation.
        
        Args:
            file_path: Path to the JSON file
            default: Default value to return if file doesn't exist or is invalid
            validate_func: Optional function to validate the loaded data
            
        Returns:
            Parsed JSON data or default value
        """
        if not file_path.exists():
            logger.debug(f"File {file_path} does not exist, returning default")
            return default
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate data if validator provided
            if validate_func and not validate_func(data):
                logger.warning(f"Validation failed for {file_path}, returning default")
                return default
            
            logger.debug(f"Successfully read JSON file {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {file_path}: {e}, returning default")
            return default
        except (IOError, OSError) as e:
            logger.warning(f"Failed to read {file_path}: {e}, returning default")
            return default
    
    def write_json_file(self, 
                       file_path: Path, 
                       data: Any,
                       create_backup: bool = None,
                       validate_func: Optional[Callable[[Any], bool]] = None) -> bool:
        """
        Write data to a JSON file atomically.
        
        Args:
            file_path: Path to write to
            data: Data to write (must be JSON serializable)
            create_backup: Whether to create backup (uses config default if None)
            validate_func: Optional function to validate data before writing
            
        Returns:
            bool: True if write succeeded, False otherwise
        """
        if create_backup is None:
            create_backup = self.config.backup_on_update
        
        # Validate data if validator provided
        if validate_func and not validate_func(data):
            logger.error(f"Data validation failed for {file_path}")
            return False
        
        try:
            with AtomicFileWriter(
                file_path,
                create_backup=create_backup and file_path.exists(),
                backup_count=self.config.backup_count
            ) as f:
                json.dump(
                    data, 
                    f, 
                    indent=self.config.json_indent,
                    sort_keys=self.config.json_sort_keys,
                    ensure_ascii=False
                )
            
            logger.debug(f"Successfully wrote JSON file {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write JSON file {file_path}: {e}")
            return False
    
    def update_json_file(self, 
                        file_path: Path,
                        updates: Dict[str, Any],
                        create_if_missing: bool = True,
                        merge_func: Optional[Callable[[Dict, Dict], Dict]] = None) -> bool:
        """
        Update specific fields in a JSON file atomically.
        
        Args:
            file_path: Path to the JSON file
            updates: Dictionary of updates to apply
            create_if_missing: Whether to create file if it doesn't exist
            merge_func: Custom merge function (default: shallow merge)
            
        Returns:
            bool: True if update succeeded, False otherwise
        """
        with self._lock:
            # Read current data
            current_data = self.read_json_file(file_path, default={})
            
            if not current_data and not create_if_missing:
                logger.warning(f"File {file_path} doesn't exist and create_if_missing=False")
                return False
            
            # Ensure current_data is a dict
            if not isinstance(current_data, dict):
                if create_if_missing:
                    current_data = {}
                else:
                    logger.error(f"Current data in {file_path} is not a dict")
                    return False
            
            # Apply updates
            if merge_func:
                updated_data = merge_func(current_data, updates)
            else:
                # Default shallow merge
                updated_data = {**current_data, **updates}
            
            # Add timestamp
            if 'last_updated' not in updates:  # Don't override explicit timestamp
                updated_data['last_updated'] = datetime.now(timezone.utc).isoformat()
            
            # Write updated data
            return self.write_json_file(file_path, updated_data)
    
    def backup_file(self, file_path: Path) -> Optional[Path]:
        """
        Create a timestamped backup of a file.
        
        Args:
            file_path: File to backup
            
        Returns:
            Path to backup file, or None if backup failed
        """
        if not file_path.exists():
            logger.warning(f"Cannot backup non-existent file {file_path}")
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup_path = file_path.with_name(f"{file_path.name}.backup_{timestamp}")
        
        try:
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup at {backup_path}")
            
            # Clean up old backups
            self._cleanup_old_backups(file_path)
            
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup of {file_path}: {e}")
            return None
    
    def _cleanup_old_backups(self, file_path: Path):
        """Clean up old backup files for a given file"""
        backup_pattern = f"{file_path.name}.backup_*"
        backup_files = list(file_path.parent.glob(backup_pattern))
        
        if len(backup_files) > self.config.backup_count:
            # Sort by modification time, newest first
            backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Remove excess backups
            for backup_file in backup_files[self.config.backup_count:]:
                try:
                    backup_file.unlink()
                    logger.debug(f"Removed old backup {backup_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove old backup {backup_file}: {e}")
    
    def list_backups(self, file_path: Path) -> List[Path]:
        """List all backup files for a given file"""
        backup_pattern = f"{file_path.name}.backup_*"
        backup_files = list(file_path.parent.glob(backup_pattern))
        # Sort by modification time, newest first
        backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return backup_files
    
    def restore_from_backup(self, file_path: Path, backup_path: Optional[Path] = None) -> bool:
        """
        Restore a file from backup.
        
        Args:
            file_path: Target file to restore
            backup_path: Specific backup to restore from (or None for most recent)
            
        Returns:
            bool: True if restore succeeded, False otherwise
        """
        if backup_path is None:
            # Find most recent backup
            backups = self.list_backups(file_path)
            if not backups:
                logger.error(f"No backups found for {file_path}")
                return False
            backup_path = backups[0]  # Most recent
        
        if not backup_path.exists():
            logger.error(f"Backup file {backup_path} does not exist")
            return False
        
        try:
            # Use atomic write to restore
            with open(backup_path, 'r', encoding='utf-8') as src:
                with AtomicFileWriter(file_path) as dst:
                    dst.write(src.read())
            
            logger.info(f"Successfully restored {file_path} from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore {file_path} from {backup_path}: {e}")
            return False

class BrainwormStateManager(StateFileManager):
    """
    Specialized state manager for brainworm-specific state files.
    
    This class provides high-level methods for managing common brainworm
    state files like session state, DAIC state, correlation state, etc.
    """
    
    def __init__(self, project_root: Path, config: Optional[FileManagerConfig] = None):
        state_dir = project_root / '.brainworm' / 'state'
        super().__init__(state_dir, config)
        self.project_root = project_root
        
        # Common state file paths
        self.unified_state_file = self.state_dir / 'unified_session_state.json'
        self.correlation_state_file = self.state_dir / '.correlation_state'
        self.daic_mode_file = self.state_dir / 'daic-mode.json'
    
    def read_unified_state(self) -> Dict[str, Any]:
        """Read unified session state with validation"""
        def validate_unified_state(data):
            return isinstance(data, dict) and 'session_id' in data
        
        return self.read_json_file(
            self.unified_state_file,
            default=self._get_default_unified_state(),
            validate_func=validate_unified_state
        )
    
    def update_unified_state(self, updates: Dict[str, Any]) -> bool:
        """Update unified session state atomically"""
        return self.update_json_file(self.unified_state_file, updates)
    
    def read_correlation_state(self) -> Dict[str, str]:
        """Read correlation state mapping"""
        def validate_correlation_state(data):
            return isinstance(data, dict)
        
        return self.read_json_file(
            self.correlation_state_file,
            default={},
            validate_func=validate_correlation_state
        )
    
    def update_correlation_state(self, session_id: str, correlation_id: str) -> bool:
        """Update correlation mapping with cleanup of old entries"""
        def merge_correlations(current: Dict[str, str], updates: Dict[str, str]) -> Dict[str, str]:
            merged = {**current, **updates}
            
            # Clean up old entries (keep only last 100, most recent 50)
            if len(merged) > 100:
                recent_items = list(merged.items())[-50:]
                merged = dict(recent_items)
            
            return merged
        
        return self.update_json_file(
            self.correlation_state_file,
            {session_id: correlation_id},
            merge_func=merge_correlations
        )
    
    def read_daic_mode(self) -> Dict[str, Any]:
        """Read DAIC mode state"""
        def validate_daic_mode(data):
            return isinstance(data, dict)
        
        return self.read_json_file(
            self.daic_mode_file,
            default={'mode': 'discussion', 'updated_at': datetime.now(timezone.utc).isoformat()},
            validate_func=validate_daic_mode
        )
    
    def update_daic_mode(self, mode: str, trigger: Optional[str] = None) -> bool:
        """Update DAIC mode with validation"""
        if mode not in ['discussion', 'implementation']:
            logger.error(f"Invalid DAIC mode: {mode}")
            return False
        
        updates = {
            'mode': mode,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        if trigger:
            updates['trigger'] = trigger
        
        return self.update_json_file(self.daic_mode_file, updates)
    
    def _get_default_unified_state(self) -> Dict[str, Any]:
        """Get default unified state structure"""
        return {
            'session_id': 'unknown',
            'correlation_id': 'unknown',
            'daic_mode': 'discussion',
            'current_task': None,
            'current_branch': None,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_updated': datetime.now(timezone.utc).isoformat()
        }

# Backward compatibility functions
@contextmanager
def atomic_json_write(file_path: Path, create_backup: bool = False):
    """
    Context manager for atomic JSON file writing (backward compatible).
    
    Args:
        file_path: Path to write to
        create_backup: Whether to create a backup
        
    Yields:
        file handle for writing
    """
    with AtomicFileWriter(file_path, create_backup=create_backup) as f:
        yield f

def safe_json_read(file_path: Path, default: Any = None) -> Any:
    """
    Safely read a JSON file with error handling (backward compatible).
    
    Args:
        file_path: Path to read from
        default: Default value if file doesn't exist or is invalid
        
    Returns:
        Parsed JSON data or default value
    """
    manager = StateFileManager(file_path.parent)
    return manager.read_json_file(file_path, default)

def safe_json_write(file_path: Path, data: Any, create_backup: bool = True) -> bool:
    """
    Safely write data to JSON file atomically (backward compatible).
    
    Args:
        file_path: Path to write to
        data: Data to write
        create_backup: Whether to create backup
        
    Returns:
        bool: True if successful, False otherwise
    """
    manager = StateFileManager(file_path.parent)
    return manager.write_json_file(file_path, data, create_backup)