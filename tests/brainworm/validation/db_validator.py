#!/usr/bin/env python3
"""
Database Validation Utilities

Provides comprehensive validation helpers for brainworm SQLite database events.
Used by integration and E2E tests to verify event storage correctness.

Usage:
    validator = DatabaseValidator(db_path)
    validator.assert_event_count(session_id, expected=5)
    validator.assert_all_events_have_required_fields(session_id)
    validator.assert_correlation_ids_valid(session_id)
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass


@dataclass
class EventValidationResult:
    """Result of event validation check"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    event_count: int
    details: Dict[str, Any]


class DatabaseValidator:
    """
    Comprehensive database validation for brainworm analytics.

    Validates:
    - Event count and presence
    - Required field completeness
    - Session and correlation ID consistency
    - Timestamp ordering
    - Hook type validity
    - Database schema integrity
    """

    # Required fields in hook_events table
    REQUIRED_FIELDS = {
        'session_id',
        'correlation_id',
        'hook_name',
        'timestamp_ns',
        'execution_id'
    }

    # Valid hook names
    VALID_HOOK_NAMES = {
        'session_start',
        'session_end',
        'user_prompt_submit',
        'pre_tool_use',
        'post_tool_use',
        'stop',
        'notification',
        'transcript_processor'
    }

    def __init__(self, db_path: Path):
        """
        Initialize database validator.

        Args:
            db_path: Path to brainworm SQLite database
        """
        self.db_path = Path(db_path)

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

    def _execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """Execute query and return results"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def get_event_count(self, session_id: Optional[str] = None) -> int:
        """
        Get total event count, optionally filtered by session.

        Args:
            session_id: Optional session ID to filter by

        Returns:
            Number of events
        """
        if session_id:
            query = "SELECT COUNT(*) FROM hook_events WHERE session_id = ?"
            params = (session_id,)
        else:
            query = "SELECT COUNT(*) FROM hook_events"
            params = ()

        result = self._execute_query(query, params)
        return result[0][0] if result else 0

    def get_events(
        self,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        hook_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get events with optional filtering.

        Args:
            session_id: Filter by session ID
            correlation_id: Filter by correlation ID
            hook_name: Filter by hook name

        Returns:
            List of event dictionaries
        """
        query = "SELECT * FROM hook_events WHERE 1=1"
        params = []

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if correlation_id:
            query += " AND correlation_id = ?"
            params.append(correlation_id)

        if hook_name:
            query += " AND hook_name = ?"
            params.append(hook_name)

        query += " ORDER BY timestamp_ns"

        rows = self._execute_query(query, tuple(params))

        # Get column names
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("SELECT * FROM hook_events LIMIT 0")
            columns = [desc[0] for desc in cursor.description]

        return [dict(zip(columns, row)) for row in rows]

    def assert_event_count(
        self,
        session_id: str,
        expected: int,
        message: Optional[str] = None
    ):
        """
        Assert that session has expected number of events.

        Args:
            session_id: Session ID to check
            expected: Expected event count
            message: Optional custom error message

        Raises:
            AssertionError: If count doesn't match
        """
        actual = self.get_event_count(session_id)

        if actual != expected:
            error_msg = message or (
                f"Event count mismatch for session {session_id}:\n"
                f"Expected: {expected}\n"
                f"Actual: {actual}"
            )
            raise AssertionError(error_msg)

    def assert_all_events_have_required_fields(self, session_id: str):
        """
        Assert all events have required fields populated.

        Args:
            session_id: Session ID to validate

        Raises:
            AssertionError: If any required field is missing or null
        """
        events = self.get_events(session_id=session_id)

        if not events:
            raise AssertionError(f"No events found for session {session_id}")

        errors = []

        for i, event in enumerate(events):
            for field in self.REQUIRED_FIELDS:
                if field not in event:
                    errors.append(
                        f"Event {i}: Missing required field '{field}'"
                    )
                elif event[field] is None:
                    errors.append(
                        f"Event {i}: Required field '{field}' is NULL"
                    )

        if errors:
            raise AssertionError(
                f"Required field validation failed for session {session_id}:\n" +
                "\n".join(errors)
            )

    def assert_correlation_ids_valid(self, session_id: str):
        """
        Assert all correlation IDs are valid (non-null, proper format).

        Args:
            session_id: Session ID to validate

        Raises:
            AssertionError: If correlation IDs are invalid
        """
        events = self.get_events(session_id=session_id)

        errors = []

        for i, event in enumerate(events):
            corr_id = event.get('correlation_id')

            if not corr_id:
                errors.append(f"Event {i}: Missing or null correlation_id")
            elif not isinstance(corr_id, str):
                errors.append(
                    f"Event {i}: correlation_id is not a string: {type(corr_id)}"
                )
            elif len(corr_id) == 0:
                errors.append(f"Event {i}: correlation_id is empty string")

        if errors:
            raise AssertionError(
                f"Correlation ID validation failed for session {session_id}:\n" +
                "\n".join(errors)
            )

    def assert_timestamps_ordered(self, session_id: str):
        """
        Assert event timestamps are in chronological order.

        Args:
            session_id: Session ID to validate

        Raises:
            AssertionError: If timestamps are out of order
        """
        events = self.get_events(session_id=session_id)

        if len(events) < 2:
            return  # Nothing to validate

        errors = []
        prev_timestamp = 0

        for i, event in enumerate(events):
            timestamp = event.get('timestamp_ns', 0)

            if timestamp < prev_timestamp:
                errors.append(
                    f"Event {i}: Timestamp out of order\n"
                    f"  Previous: {prev_timestamp}\n"
                    f"  Current: {timestamp}"
                )

            prev_timestamp = timestamp

        if errors:
            raise AssertionError(
                f"Timestamp ordering validation failed for session {session_id}:\n" +
                "\n".join(errors)
            )

    def assert_hook_names_valid(self, session_id: str):
        """
        Assert all hook names are valid known types.

        Args:
            session_id: Session ID to validate

        Raises:
            AssertionError: If invalid hook names found
        """
        events = self.get_events(session_id=session_id)

        invalid_hooks = []

        for event in events:
            hook_name = event.get('hook_name')
            if hook_name and hook_name not in self.VALID_HOOK_NAMES:
                invalid_hooks.append(hook_name)

        if invalid_hooks:
            raise AssertionError(
                f"Invalid hook names found in session {session_id}:\n"
                f"Invalid: {set(invalid_hooks)}\n"
                f"Valid: {self.VALID_HOOK_NAMES}"
            )

    def validate_session(self, session_id: str) -> EventValidationResult:
        """
        Run comprehensive validation on a session.

        Args:
            session_id: Session ID to validate

        Returns:
            EventValidationResult with validation details
        """
        errors = []
        warnings = []
        details = {}

        # Get event count
        event_count = self.get_event_count(session_id)
        details['event_count'] = event_count

        if event_count == 0:
            errors.append("No events found for session")
            return EventValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                event_count=0,
                details=details
            )

        # Get all events
        events = self.get_events(session_id=session_id)
        details['events'] = events

        # Check required fields
        try:
            self.assert_all_events_have_required_fields(session_id)
        except AssertionError as e:
            errors.append(f"Required fields: {str(e)}")

        # Check correlation IDs
        try:
            self.assert_correlation_ids_valid(session_id)
        except AssertionError as e:
            errors.append(f"Correlation IDs: {str(e)}")

        # Check timestamp ordering
        try:
            self.assert_timestamps_ordered(session_id)
        except AssertionError as e:
            errors.append(f"Timestamp order: {str(e)}")

        # Check hook names
        try:
            self.assert_hook_names_valid(session_id)
        except AssertionError as e:
            errors.append(f"Hook names: {str(e)}")

        # Check for duplicate execution IDs (should be unique per execution)
        execution_ids = [e.get('execution_id') for e in events if e.get('execution_id')]
        if len(execution_ids) != len(set(execution_ids)):
            warnings.append("Duplicate execution IDs found (may indicate duplicate hook invocations)")

        return EventValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            event_count=event_count,
            details=details
        )

    def get_correlation_groups(self, session_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group events by correlation ID.

        Args:
            session_id: Session ID to analyze

        Returns:
            Dictionary mapping correlation_id -> list of events
        """
        events = self.get_events(session_id=session_id)

        groups = {}
        for event in events:
            corr_id = event.get('correlation_id')
            if corr_id:
                if corr_id not in groups:
                    groups[corr_id] = []
                groups[corr_id].append(event)

        return groups

    def assert_pre_post_hooks_paired(self, session_id: str):
        """
        Assert PreToolUse and PostToolUse hooks are properly paired
        with matching correlation IDs.

        Args:
            session_id: Session ID to validate

        Raises:
            AssertionError: If pre/post hooks are not properly paired
        """
        groups = self.get_correlation_groups(session_id)

        errors = []

        for corr_id, events in groups.items():
            hook_names = [e.get('hook_name') for e in events]

            has_pre = 'pre_tool_use' in hook_names
            has_post = 'post_tool_use' in hook_names

            # If we have pre_tool_use, we should have post_tool_use
            if has_pre and not has_post:
                errors.append(
                    f"Correlation {corr_id}: Has pre_tool_use but missing post_tool_use"
                )

            # If we have post_tool_use without pre_tool_use, that's unusual
            if has_post and not has_pre:
                errors.append(
                    f"Correlation {corr_id}: Has post_tool_use but missing pre_tool_use"
                )

        if errors:
            raise AssertionError(
                f"Pre/Post hook pairing validation failed:\n" +
                "\n".join(errors)
            )
