#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pendulum",
#     "rich>=13.0.0",
# ]
# ///

"""
Hook Analytics with DAIC Integration

Basic hook logging with session correlation tracking,
memory capture, and DAIC workflow discipline support.
"""

import json
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console

# Import type definitions with fallback
try:
    from .hook_types import parse_log_event, PreToolUseLogEvent, PostToolUseLogEvent, get_standard_timestamp
except ImportError:
    parse_log_event = None
    PreToolUseLogEvent = None
    PostToolUseLogEvent = None
    # Fallback timestamp function
    def get_standard_timestamp():
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

# Import existing utilities
try:
    from .hook_logging import HookLogger
except ImportError:
    try:
        from hook_logging import HookLogger
    except ImportError:
        # Fallback basic logger class
        class HookLogger:
            def __init__(self, project_root, hook_name):
                self.project_root = project_root
                self.hook_name = hook_name
            
            def log_event(self, event_data):
                return True

# Import analytics processor for database logging
try:
    from .analytics_processor import ClaudeAnalyticsProcessor
except ImportError:
    try:
        from claude_analytics_processor import ClaudeAnalyticsProcessor
    except ImportError:
        # Fallback when analytics processor not available
        class ClaudeAnalyticsProcessor:
            def __init__(self, analytics_dir):
                pass
            def log_event(self, event_data):
                return False

# Import correlation manager for workflow tracking
try:
    from .correlation_manager import get_workflow_correlation_id
except ImportError:
    try:
        from correlation_manager import get_workflow_correlation_id
    except ImportError:
        # Fallback when correlation manager not available
        def get_workflow_correlation_id(project_root, session_id):
            correlation_uuid = str(uuid.uuid4())
            return f"corr-{correlation_uuid[:12]}"

console = Console()


class AnalyticsHookLogger(HookLogger):
    """Basic logger with Claude Code session correlation and memory capture"""
    
    def __init__(self, project_root: Path, hook_name: str, enable_analytics: bool = False, session_id: str = None):
        super().__init__(project_root, hook_name)
        self.enable_analytics = enable_analytics
        self.session_id = session_id or self._get_fallback_session_id()
        
        # Use correlation manager for workflow-level correlation instead of random IDs
        self.correlation_id = get_workflow_correlation_id(project_root, self.session_id)
        
        self.timing_data = {}  # Keep for backward compatibility
        
        # Shared timing storage directory
        self.timing_dir = project_root / '.brainworm' / 'timing'
        self.timing_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize analytics processor for database logging
        try:
            self.analytics_processor = ClaudeAnalyticsProcessor(project_root / '.brainworm')
        except Exception:
            # Graceful fallback if processor initialization fails
            self.analytics_processor = None
        
    def _get_fallback_session_id(self) -> str:
        """Generate fallback session ID if not provided by Claude Code"""
        # Try to get from environment (set by parent Claude Code process)
        import os
        if session_id := os.environ.get('CLAUDE_SESSION_ID'):
            return session_id
        
        # Fallback to generating one (for standalone testing)
        return f"fallback-{str(uuid.uuid4())[:8]}"
    
    
    def enrich_event_data(self, event_data: dict) -> dict:
        """Add basic metadata to event data for memory capture"""
        if not self.enable_analytics:
            return event_data
            
        enriched = event_data.copy()
        
        # Use typed event parsing if available for better metadata extraction
        if parse_log_event:
            try:
                typed_event = parse_log_event(event_data)
                # Extract typed metadata
                enriched.update({
                    'schema_version': '2.1',  # Updated for typed events
                    'session_id': typed_event.session_id or self.session_id,
                    'correlation_id': typed_event.correlation_id or self.correlation_id,
                    'timestamp': get_standard_timestamp(),  # Use standard ISO format
                    'workflow_phase': typed_event.workflow_phase or self._detect_workflow_phase(event_data),
                    'project_root': typed_event.project_root or str(self.project_root),
                    'hook_event_name': typed_event.hook_event_name,
                    'logged_at': typed_event.logged_at
                })
            except Exception:
                # Fallback to basic enrichment
                enriched.update({
                    'schema_version': '2.0',
                    'session_id': self.session_id,
                    'correlation_id': self.correlation_id,
                    'timestamp': get_standard_timestamp(),  # Use standard ISO format
                    'workflow_phase': self._detect_workflow_phase(event_data),
                    'project_root': str(self.project_root),
                })
        else:
            # Fallback when types are not available
            enriched.update({
                'schema_version': '2.0',
                'session_id': self.session_id,
                'correlation_id': self.correlation_id,
                'timestamp': get_standard_timestamp(),  # Use standard ISO format
                'workflow_phase': self._detect_workflow_phase(event_data),
                'project_root': str(self.project_root),
            })
        
        return enriched
    
    def _detect_workflow_phase(self, event_data: dict) -> str:
        """Detect current workflow phase"""
        hook_name = event_data.get('hook_name', self.hook_name)
        
        if hook_name == 'user_prompt_submit':
            return 'prompt_analysis'
        elif hook_name == 'pre_tool_use':
            return 'tool_preparation'
        elif hook_name == 'post_tool_use':
            return 'tool_completion'
        else:
            return 'unknown'
    
    def log_event_with_analytics(self, event_data: dict, debug: bool = False) -> bool:
        """Log event to analytics database and backup JSONL"""
        try:
            enriched_data = self.enrich_event_data(event_data)

            # Add hook_name to ensure proper typed event parsing
            if 'hook_name' not in enriched_data:
                enriched_data['hook_name'] = self.hook_name

            # Log to analytics processor (database + analytics JSONL backup)
            if self.analytics_processor:
                try:
                    success = self.analytics_processor.log_event(enriched_data)

                    if debug and success:
                        schema_version = enriched_data.get('schema_version', '1.0')
                        print(f"📊 Analytics log (v{schema_version}) [DB+JSONL]: {self.session_id[:8]} in {self.hook_name}", file=sys.stderr)

                    return success
                except Exception as db_e:
                    if debug:
                        print(f"Warning: Analytics logging failed: {db_e}", file=sys.stderr)
                    return False
            else:
                if debug:
                    print(f"Warning: Analytics processor not available", file=sys.stderr)
                return False

        except Exception as e:
            if debug:
                print(f"Warning: Analytics logging failed: {e}", file=sys.stderr)
            return False
    
    def log_pre_tool_execution(self, input_data: dict, debug: bool = False) -> bool:
        """Log pre-tool execution with timing"""
        # Store timing checkpoint
        timing_info = {
            'start_time': get_standard_timestamp(),
            'tool_name': input_data.get('tool_name'),
            'correlation_id': self.correlation_id
        }
        
        # Store in instance for backward compatibility
        self.timing_data[self.session_id] = timing_info
        
        # Also write to shared timing storage for cross-hook coordination
        try:
            timing_file = self.timing_dir / f"{self.session_id}.json"
            with open(timing_file, 'w') as f:
                json.dump(timing_info, f)
        except Exception as e:
            if debug:
                print(f"Warning: Failed to write timing file: {e}", file=sys.stderr)
        
        event_data = {
            'hook_name': 'pre_tool_use',
            'tool_name': input_data.get('tool_name'),
            'tool_input': input_data.get('tool_input'),
            'session_id': input_data.get('session_id'),
            'timing': timing_info  # Include timing data in logged event
        }
        
        return self.log_event_with_analytics(event_data, debug)
    
    def log_post_tool_execution(self, input_data: dict, debug: bool = False) -> bool:
        """Log post-tool execution with duration"""
        # Calculate execution duration
        timing_info = {}
        
        # Try to read from shared timing storage first
        timing_file = self.timing_dir / f"{self.session_id}.json"
        try:
            if timing_file.exists():
                with open(timing_file, 'r') as f:
                    stored_timing = json.load(f)
                start_time = stored_timing['start_time']
                timing_info = {
                    'execution_duration_ms': self._calculate_duration_ms(start_time),
                    'start_timestamp': start_time,
                    'correlation_id': stored_timing.get('correlation_id', self.correlation_id)
                }
                # Clean up the timing file
                timing_file.unlink()
                if debug:
                    print(f"✅ Timing coordination successful: {timing_info['execution_duration_ms']:.2f}ms", file=sys.stderr)
            else:
                # Fallback to instance storage (backward compatibility)
                if self.session_id in self.timing_data:
                    start_time = self.timing_data[self.session_id]['start_time']
                    timing_info = {
                        'execution_duration_ms': self._calculate_duration_ms(start_time),
                        'start_timestamp': start_time
                    }
                    # Clean up timing data
                    del self.timing_data[self.session_id]
                elif debug:
                    print(f"⚠️ No timing data found for session: {self.session_id[:8]}", file=sys.stderr)
        except Exception as e:
            if debug:
                print(f"Warning: Failed to read timing file: {e}", file=sys.stderr)
            # Fallback to instance storage
            if self.session_id in self.timing_data:
                start_time = self.timing_data[self.session_id]['start_time']
                timing_info = {
                    'execution_duration_ms': self._calculate_duration_ms(start_time),
                    'start_timestamp': start_time
                }
                del self.timing_data[self.session_id]
        
        event_data = {
            'hook_name': 'post_tool_use',
            'tool_name': input_data.get('tool_name'),
            'tool_input': input_data.get('tool_input'),
            'tool_result': input_data.get('tool_result'),
            'session_id': input_data.get('session_id'),
            'timing': timing_info
        }
        
        return self.log_event_with_analytics(event_data, debug)
    
    def log_user_prompt(self, prompt_data: dict, debug: bool = False) -> bool:
        """Log user prompt with intent analysis"""
        event_data = {
            'hook_name': 'user_prompt_submit',
            'prompt': prompt_data.get('prompt', ''),
            'session_id': prompt_data.get('session_id'),
        }
        
        if self.enable_analytics:
            event_data['intent_analysis'] = self._analyze_intent(prompt_data.get('prompt', ''))
        
        return self.log_event_with_analytics(event_data, debug)
    
    def _calculate_duration_ms(self, start_time_iso: str) -> float:
        """Calculate duration between ISO timestamp and now in milliseconds."""
        try:
            from datetime import datetime, timezone
            start_time = datetime.fromisoformat(start_time_iso.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            duration_seconds = (now - start_time).total_seconds()
            return duration_seconds * 1000
        except Exception:
            # Fallback to zero if calculation fails
            return 0.0
    
    def _analyze_intent(self, prompt: str) -> dict:
        """Basic intent classification"""
        prompt_lower = prompt.lower()
        
        intent_keywords = {
            'bug_fix': ['fix', 'bug', 'error', 'issue', 'broken'],
            'feature_development': ['add', 'create', 'implement', 'build', 'new'],
            'refactoring': ['refactor', 'cleanup', 'reorganize', 'improve'],
            'documentation': ['document', 'readme', 'docs', 'comment'],
            'testing': ['test', 'spec', 'validate', 'verify'],
            'debugging': ['debug', 'investigate', 'trace', 'analyze']
        }
        
        scores = {}
        for intent, keywords in intent_keywords.items():
            scores[intent] = sum(1 for keyword in keywords if keyword in prompt_lower)
        
        if max(scores.values()) == 0:
            return {'primary_intent': 'general_inquiry', 'confidence': 0.3}
        
        primary_intent = max(scores.keys(), key=lambda k: scores[k])
        confidence = min(0.9, scores[primary_intent] * 0.3)
        
        return {
            'primary_intent': primary_intent,
            'confidence': confidence,
            'matched_keywords': [kw for kw in intent_keywords[primary_intent] if kw in prompt_lower]
        }


def create_analytics_logger(project_root: Path, hook_name: str, enable_analytics: bool = False, session_id: str = None) -> AnalyticsHookLogger:
    """Factory function for basic analytics logger with Claude Code session correlation"""
    return AnalyticsHookLogger(project_root, hook_name, enable_analytics, session_id)