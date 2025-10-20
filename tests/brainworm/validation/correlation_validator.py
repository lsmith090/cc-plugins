#!/usr/bin/env python3
"""
Correlation ID Validation Utilities

Provides validation helpers for brainworm correlation tracking.
Validates that correlation IDs flow correctly through hook sequences.

Usage:
    validator = CorrelationValidator()
    validator.assert_pre_post_paired(events)
    validator.assert_correlation_flow_valid(events)
    flow_analysis = validator.analyze_correlation_flow(events)
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class CorrelationFlowAnalysis:
    """Analysis of correlation ID flow through events"""
    valid: bool
    correlation_groups: Dict[str, List[Dict[str, Any]]]
    paired_count: int
    unpaired_pre: int
    unpaired_post: int
    orphaned_events: List[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]


class CorrelationValidator:
    """
    Validates correlation ID flow and hook pairing.

    Correlation tracking rules:
    - PreToolUse and PostToolUse for same tool share correlation_id
    - Each tool invocation gets unique correlation_id
    - Session-level hooks (SessionStart, SessionEnd) have their own IDs
    - UserPromptSubmit hooks have their own IDs
    """

    # Hooks that should be paired with same correlation_id
    PAIRED_HOOKS = {
        ('pre_tool_use', 'post_tool_use'),
    }

    # Hooks that are standalone (don't require pairing)
    STANDALONE_HOOKS = {
        'session_start',
        'session_end',
        'user_prompt_submit',
        'stop',
        'notification'
    }

    def group_by_correlation(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group events by correlation ID.

        Args:
            events: List of event dictionaries

        Returns:
            Dictionary mapping correlation_id -> events
        """
        groups = defaultdict(list)

        for event in events:
            corr_id = event.get('correlation_id')
            if corr_id:
                groups[corr_id].append(event)

        return dict(groups)

    def assert_pre_post_paired(self, events: List[Dict[str, Any]]):
        """
        Assert PreToolUse and PostToolUse hooks are properly paired.

        Args:
            events: List of event dictionaries

        Raises:
            AssertionError: If pairing is incorrect
        """
        groups = self.group_by_correlation(events)

        errors = []

        for corr_id, group_events in groups.items():
            hook_names = [e.get('hook_name') for e in group_events]

            has_pre = 'pre_tool_use' in hook_names
            has_post = 'post_tool_use' in hook_names

            # Pre without Post
            if has_pre and not has_post:
                errors.append(
                    f"Correlation {corr_id}: PreToolUse without matching PostToolUse"
                )

            # Post without Pre (unusual but not necessarily wrong)
            if has_post and not has_pre:
                # This could happen if PreToolUse blocked the tool
                # Don't treat as hard error, but note it
                pass

        if errors:
            raise AssertionError(
                "Pre/Post hook pairing validation failed:\n" +
                "\n".join(errors)
            )

    def assert_correlation_flow_valid(self, events: List[Dict[str, Any]]):
        """
        Assert correlation ID flow is valid and consistent.

        Args:
            events: List of event dictionaries

        Raises:
            AssertionError: If flow is invalid
        """
        errors = []

        # Check all events have correlation IDs
        for i, event in enumerate(events):
            corr_id = event.get('correlation_id')

            if not corr_id:
                errors.append(
                    f"Event {i} ({event.get('hook_name')}): Missing correlation_id"
                )
            elif not isinstance(corr_id, str):
                errors.append(
                    f"Event {i} ({event.get('hook_name')}): "
                    f"correlation_id is not a string: {type(corr_id)}"
                )
            elif len(corr_id) == 0:
                errors.append(
                    f"Event {i} ({event.get('hook_name')}): "
                    f"correlation_id is empty string"
                )

        # Check pre/post pairing
        try:
            self.assert_pre_post_paired(events)
        except AssertionError as e:
            errors.append(str(e))

        if errors:
            raise AssertionError(
                "Correlation flow validation failed:\n" +
                "\n".join(errors)
            )

    def analyze_correlation_flow(
        self,
        events: List[Dict[str, Any]]
    ) -> CorrelationFlowAnalysis:
        """
        Analyze correlation ID flow and provide detailed report.

        Args:
            events: List of event dictionaries

        Returns:
            CorrelationFlowAnalysis with detailed findings
        """
        errors = []
        warnings = []

        # Group by correlation
        groups = self.group_by_correlation(events)

        # Count paired and unpaired hooks
        paired_count = 0
        unpaired_pre = 0
        unpaired_post = 0
        orphaned_events = []

        for corr_id, group_events in groups.items():
            hook_names = [e.get('hook_name') for e in group_events]

            has_pre = 'pre_tool_use' in hook_names
            has_post = 'post_tool_use' in hook_names

            if has_pre and has_post:
                paired_count += 1
            elif has_pre:
                unpaired_pre += 1
                orphaned_events.extend([
                    e for e in group_events
                    if e.get('hook_name') == 'pre_tool_use'
                ])
            elif has_post:
                unpaired_post += 1
                orphaned_events.extend([
                    e for e in group_events
                    if e.get('hook_name') == 'post_tool_use'
                ])

        # Validate correlation flow
        try:
            self.assert_correlation_flow_valid(events)
        except AssertionError as e:
            errors.append(str(e))

        # Check for tool name consistency within correlation groups
        for corr_id, group_events in groups.items():
            tool_names = {
                e.get('tool_name') for e in group_events
                if e.get('tool_name') is not None
            }

            # Tool events in same correlation should have same tool_name
            if len(tool_names) > 1:
                warnings.append(
                    f"Correlation {corr_id}: Multiple tool names: {tool_names}"
                )

        return CorrelationFlowAnalysis(
            valid=len(errors) == 0,
            correlation_groups=groups,
            paired_count=paired_count,
            unpaired_pre=unpaired_pre,
            unpaired_post=unpaired_post,
            orphaned_events=orphaned_events,
            errors=errors,
            warnings=warnings
        )

    def get_correlation_chain(
        self,
        events: List[Dict[str, Any]],
        correlation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all events in a correlation chain, ordered by timestamp.

        Args:
            events: List of event dictionaries
            correlation_id: Correlation ID to trace

        Returns:
            List of events with matching correlation_id, time-ordered
        """
        chain = [
            e for e in events
            if e.get('correlation_id') == correlation_id
        ]

        # Sort by timestamp_ns if available
        chain.sort(key=lambda e: e.get('timestamp_ns', 0))

        return chain

    def assert_tool_name_consistency(
        self,
        events: List[Dict[str, Any]]
    ):
        """
        Assert tool names are consistent within correlation groups.

        Args:
            events: List of event dictionaries

        Raises:
            AssertionError: If tool names are inconsistent
        """
        groups = self.group_by_correlation(events)

        errors = []

        for corr_id, group_events in groups.items():
            # Get all tool names in this correlation
            tool_names = [
                e.get('tool_name') for e in group_events
                if e.get('tool_name') is not None
            ]

            # Should all be the same (or all None)
            unique_tools = set(tool_names)

            if len(unique_tools) > 1:
                errors.append(
                    f"Correlation {corr_id}: Inconsistent tool names: {unique_tools}"
                )

        if errors:
            raise AssertionError(
                "Tool name consistency validation failed:\n" +
                "\n".join(errors)
            )

    def assert_session_id_consistency(
        self,
        events: List[Dict[str, Any]],
        expected_session_id: str
    ):
        """
        Assert all events have consistent session ID.

        Args:
            events: List of event dictionaries
            expected_session_id: Expected session ID

        Raises:
            AssertionError: If session IDs are inconsistent
        """
        errors = []

        for i, event in enumerate(events):
            session_id = event.get('session_id')

            if session_id != expected_session_id:
                errors.append(
                    f"Event {i} ({event.get('hook_name')}): "
                    f"session_id mismatch\n"
                    f"  Expected: {expected_session_id}\n"
                    f"  Actual: {session_id}"
                )

        if errors:
            raise AssertionError(
                "Session ID consistency validation failed:\n" +
                "\n".join(errors)
            )

    def get_correlation_statistics(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistical analysis of correlation tracking.

        Args:
            events: List of event dictionaries

        Returns:
            Dictionary with correlation statistics
        """
        analysis = self.analyze_correlation_flow(events)

        groups = analysis.correlation_groups

        return {
            'total_events': len(events),
            'unique_correlations': len(groups),
            'paired_hooks': analysis.paired_count,
            'unpaired_pre_hooks': analysis.unpaired_pre,
            'unpaired_post_hooks': analysis.unpaired_post,
            'orphaned_events': len(analysis.orphaned_events),
            'avg_events_per_correlation': (
                len(events) / len(groups) if groups else 0
            ),
            'errors': analysis.errors,
            'warnings': analysis.warnings
        }
