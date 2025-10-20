#!/usr/bin/env python3
"""
JSONL Event Log Validation Utilities

Provides validation helpers for brainworm JSONL event logs.
Used by integration and E2E tests to verify event logging correctness.

Usage:
    validator = JSONLValidator(logs_dir)
    validator.assert_event_count(session_id, expected=5)
    validator.assert_events_match_schema(session_id)
    validator.assert_consistency_with_db(session_id, db_validator)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class JSONLValidationResult:
    """Result of JSONL validation check"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    event_count: int
    details: Dict[str, Any]


class JSONLValidator:
    """
    Comprehensive JSONL validation for brainworm analytics.

    Validates:
    - Event count and presence
    - JSON schema compliance
    - Required field completeness
    - Session and correlation ID consistency
    - Schema version compliance
    - Consistency with database events
    """

    # Required fields in event schema v2.0
    REQUIRED_FIELDS_V2 = {
        'session_id',
        'correlation_id',
        'hook_name',
        'timestamp_ns',
        'schema_version'
    }

    # Valid schema versions
    VALID_SCHEMA_VERSIONS = {'2.0'}

    def __init__(self, logs_dir: Path):
        """
        Initialize JSONL validator.

        Args:
            logs_dir: Path to .brainworm/analytics/logs/ directory
        """
        self.logs_dir = Path(logs_dir)

        if not self.logs_dir.exists():
            raise FileNotFoundError(f"Logs directory not found: {self.logs_dir}")

    def get_log_file_for_date(self, date: Optional[str] = None) -> Path:
        """
        Get JSONL log file for a specific date.

        Args:
            date: Date in YYYY-MM-DD format, or None for today

        Returns:
            Path to log file

        Raises:
            FileNotFoundError: If log file doesn't exist
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        log_file = self.logs_dir / f"{date}_hooks.jsonl"

        if not log_file.exists():
            raise FileNotFoundError(
                f"JSONL log file not found for date {date}: {log_file}"
            )

        return log_file

    def read_events(
        self,
        date: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Read events from JSONL file.

        Args:
            date: Date to read (YYYY-MM-DD), or None for today
            session_id: Filter by session ID, or None for all

        Returns:
            List of event dictionaries
        """
        try:
            log_file = self.get_log_file_for_date(date)
        except FileNotFoundError:
            return []

        events = []

        with open(log_file) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)

                    # Filter by session_id if specified
                    if session_id is None or event.get('session_id') == session_id:
                        events.append(event)

                except json.JSONDecodeError as e:
                    # Skip malformed lines but record them
                    events.append({
                        '_error': f"Line {line_num}: Invalid JSON: {e}",
                        '_raw_line': line
                    })

        return events

    def get_event_count(
        self,
        session_id: str,
        date: Optional[str] = None
    ) -> int:
        """
        Get event count for a session.

        Args:
            session_id: Session ID to count
            date: Date to check (YYYY-MM-DD), or None for today

        Returns:
            Number of events
        """
        events = self.read_events(date=date, session_id=session_id)
        # Don't count error entries
        return sum(1 for e in events if '_error' not in e)

    def assert_event_count(
        self,
        session_id: str,
        expected: int,
        date: Optional[str] = None,
        message: Optional[str] = None
    ):
        """
        Assert that session has expected number of events.

        Args:
            session_id: Session ID to check
            expected: Expected event count
            date: Date to check (YYYY-MM-DD), or None for today
            message: Optional custom error message

        Raises:
            AssertionError: If count doesn't match
        """
        actual = self.get_event_count(session_id, date=date)

        if actual != expected:
            error_msg = message or (
                f"JSONL event count mismatch for session {session_id}:\n"
                f"Expected: {expected}\n"
                f"Actual: {actual}"
            )
            raise AssertionError(error_msg)

    def assert_events_match_schema(
        self,
        session_id: str,
        date: Optional[str] = None
    ):
        """
        Assert all events match the expected schema.

        Args:
            session_id: Session ID to validate
            date: Date to check (YYYY-MM-DD), or None for today

        Raises:
            AssertionError: If schema validation fails
        """
        events = self.read_events(date=date, session_id=session_id)

        errors = []

        for i, event in enumerate(events):
            # Skip error entries
            if '_error' in event:
                errors.append(f"Event {i}: {event['_error']}")
                continue

            # Check schema version
            schema_version = event.get('schema_version')
            if schema_version not in self.VALID_SCHEMA_VERSIONS:
                errors.append(
                    f"Event {i}: Invalid schema_version '{schema_version}', "
                    f"expected one of {self.VALID_SCHEMA_VERSIONS}"
                )
                continue

            # Check required fields based on schema version
            if schema_version == '2.0':
                required_fields = self.REQUIRED_FIELDS_V2
            else:
                # Unknown version, use v2 as baseline
                required_fields = self.REQUIRED_FIELDS_V2

            for field in required_fields:
                if field not in event:
                    errors.append(
                        f"Event {i}: Missing required field '{field}' "
                        f"(schema v{schema_version})"
                    )
                elif event[field] is None:
                    errors.append(
                        f"Event {i}: Required field '{field}' is null "
                        f"(schema v{schema_version})"
                    )

        if errors:
            raise AssertionError(
                f"Schema validation failed for session {session_id}:\n" +
                "\n".join(errors)
            )

    def validate_session(
        self,
        session_id: str,
        date: Optional[str] = None
    ) -> JSONLValidationResult:
        """
        Run comprehensive validation on a session's JSONL events.

        Args:
            session_id: Session ID to validate
            date: Date to check (YYYY-MM-DD), or None for today

        Returns:
            JSONLValidationResult with validation details
        """
        errors = []
        warnings = []
        details = {}

        # Get event count
        event_count = self.get_event_count(session_id, date=date)
        details['event_count'] = event_count

        if event_count == 0:
            errors.append("No events found for session in JSONL")
            return JSONLValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                event_count=0,
                details=details
            )

        # Get all events
        events = self.read_events(date=date, session_id=session_id)
        details['events'] = events

        # Check for JSON parse errors
        parse_errors = [e for e in events if '_error' in e]
        if parse_errors:
            for err_event in parse_errors:
                errors.append(err_event['_error'])

        # Check schema compliance
        try:
            self.assert_events_match_schema(session_id, date=date)
        except AssertionError as e:
            errors.append(f"Schema: {str(e)}")

        # Check for duplicate events (same correlation_id + hook_name + timestamp)
        seen = set()
        for event in events:
            if '_error' in event:
                continue

            key = (
                event.get('correlation_id'),
                event.get('hook_name'),
                event.get('timestamp_ns')
            )

            if key in seen:
                warnings.append(
                    f"Potential duplicate event: {event.get('hook_name')} "
                    f"at {event.get('timestamp_ns')}"
                )
            seen.add(key)

        return JSONLValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            event_count=event_count,
            details=details
        )

    def assert_consistency_with_db(
        self,
        session_id: str,
        db_events: List[Dict[str, Any]],
        date: Optional[str] = None
    ):
        """
        Assert JSONL events are consistent with database events.

        Args:
            session_id: Session ID to validate
            db_events: Events from database for comparison
            date: Date to check (YYYY-MM-DD), or None for today

        Raises:
            AssertionError: If events are inconsistent
        """
        jsonl_events = self.read_events(date=date, session_id=session_id)

        # Filter out error events
        jsonl_events = [e for e in jsonl_events if '_error' not in e]

        errors = []

        # Check event counts match
        if len(jsonl_events) != len(db_events):
            errors.append(
                f"Event count mismatch:\n"
                f"  JSONL: {len(jsonl_events)}\n"
                f"  DB: {len(db_events)}"
            )

        # Get correlation IDs from each source
        jsonl_corr_ids = {e.get('correlation_id') for e in jsonl_events}
        db_corr_ids = {e.get('correlation_id') for e in db_events}

        missing_in_jsonl = db_corr_ids - jsonl_corr_ids
        missing_in_db = jsonl_corr_ids - db_corr_ids

        if missing_in_jsonl:
            errors.append(
                f"Events in DB but not in JSONL:\n"
                f"  Correlation IDs: {missing_in_jsonl}"
            )

        if missing_in_db:
            errors.append(
                f"Events in JSONL but not in DB:\n"
                f"  Correlation IDs: {missing_in_db}"
            )

        # Check session IDs match
        for event in jsonl_events:
            if event.get('session_id') != session_id:
                errors.append(
                    f"JSONL event has wrong session_id: {event.get('session_id')}"
                )

        if errors:
            raise AssertionError(
                f"JSONL/DB consistency check failed for session {session_id}:\n" +
                "\n".join(errors)
            )

    def get_correlation_groups(
        self,
        session_id: str,
        date: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group events by correlation ID.

        Args:
            session_id: Session ID to analyze
            date: Date to check (YYYY-MM-DD), or None for today

        Returns:
            Dictionary mapping correlation_id -> list of events
        """
        events = self.read_events(date=date, session_id=session_id)

        # Filter out error events
        events = [e for e in events if '_error' not in e]

        groups = {}
        for event in events:
            corr_id = event.get('correlation_id')
            if corr_id:
                if corr_id not in groups:
                    groups[corr_id] = []
                groups[corr_id].append(event)

        return groups
