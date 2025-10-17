#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
Brainworm Correlation ID Management
Ensures consistent correlation IDs across hook executions in a workflow
Enhanced with infrastructure classes for safe file operations
"""

import os
import uuid
from pathlib import Path
from typing import Optional

# Import the local file manager
from .file_manager import BrainwormStateManager


class CorrelationManager:
    """Manages correlation IDs for workflow tracking across hook executions"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.correlation_file = project_root / '.brainworm' / 'state' / '.correlation_state'
        self.state_manager = BrainwormStateManager(project_root)
    
    def get_or_create_correlation_id(self, session_id: Optional[str] = None) -> str:
        """
        Get existing correlation ID or create a new one for the workflow.
        
        Args:
            session_id: Optional session identifier to tie correlation to
            
        Returns:
            str: Correlation ID for this workflow
        """
        # Strategy 1: Check environment variable (highest priority)
        if corr_id := os.environ.get('CLAUDE_CORRELATION_ID'):
            return corr_id
        
        # Strategy 2: Check for existing correlation for this session
        if session_id:
            existing_id = self._get_session_correlation(session_id)
            if existing_id:
                # Set environment variable for other hooks
                os.environ['CLAUDE_CORRELATION_ID'] = existing_id
                return existing_id
        
        # Strategy 3: Create new correlation ID
        new_id = str(uuid.uuid4())[:8]
        
        # Store for this session if provided
        if session_id:
            self._store_session_correlation(session_id, new_id)
        
        # Set environment variable for downstream hooks
        os.environ['CLAUDE_CORRELATION_ID'] = new_id
        
        return new_id
    
    def _get_session_correlation(self, session_id: str) -> Optional[str]:
        """Get existing correlation ID for a session"""
        correlations = self.state_manager.read_correlation_state()
        return correlations.get(session_id)
    
    def _store_session_correlation(self, session_id: str, correlation_id: str) -> None:
        """Store correlation ID for a session"""
        # Use the state manager which handles atomic writes and cleanup automatically
        self.state_manager.update_correlation_state(session_id, correlation_id)
    
    def clear_session_correlation(self, session_id: str) -> None:
        """
        Clear correlation for a completed session.

        Uses atomic read-modify-write with file locking to prevent race conditions.
        """
        # Import filelock for atomic operations
        try:
            from filelock import FileLock

            # Use file locking to prevent race condition
            lock_file = self.correlation_file.parent / '.correlation_state.lock'
            lock = FileLock(str(lock_file), timeout=10)

            with lock:
                # Read current state while holding lock
                correlations = self.state_manager.read_correlation_state()
                if session_id in correlations:
                    del correlations[session_id]
                    # Write back while still holding lock
                    self.state_manager.write_json_file(self.correlation_file, correlations)
        except ImportError:
            # Fallback without locking (race condition possible but rare)
            correlations = self.state_manager.read_correlation_state()
            if session_id in correlations:
                del correlations[session_id]
                self.state_manager.write_json_file(self.correlation_file, correlations)


def get_workflow_correlation_id(project_root: Path, session_id: Optional[str] = None) -> str:
    """
    Convenience function to get correlation ID for current workflow.
    
    Args:
        project_root: Project root directory
        session_id: Optional session identifier
        
    Returns:
        str: Correlation ID for this workflow
    """
    manager = CorrelationManager(project_root)
    return manager.get_or_create_correlation_id(session_id)


if __name__ == '__main__':
    # Test correlation management
    from pathlib import Path
    
    print("Testing Correlation Manager...")
    
    project_root = Path.cwd()
    manager = CorrelationManager(project_root)
    
    # Test session correlation
    session_id = 'test-session-123'
    
    # First call should create new ID
    corr_id_1 = manager.get_or_create_correlation_id(session_id)
    print(f"First call: {corr_id_1}")
    
    # Second call should return same ID
    corr_id_2 = manager.get_or_create_correlation_id(session_id)
    print(f"Second call: {corr_id_2}")
    
    # Verify they match
    if corr_id_1 == corr_id_2:
        print("✅ Correlation ID persistence working")
    else:
        print("❌ Correlation ID mismatch")
    
    # Test environment variable
    env_id = os.environ.get('CLAUDE_CORRELATION_ID')
    print(f"Environment variable: {env_id}")
    
    if env_id == corr_id_1:
        print("✅ Environment variable set correctly")
    else:
        print("❌ Environment variable not set")
    
    print("Correlation Manager test complete!")