"""Typed schemas for Claude hook stdin/stdout and Brainworm log/DB events.

This module defines:
  * Raw Claude hook input structures (what Claude passes to hook stdin)
  * Hook stdout decision outputs (only pre_tool_use currently meaningful)
  * Logged JSONL event variants (what our hook logger writes)
  * Enhanced analytics extension fields (optional)
  * Normalization helpers to convert heterogeneous historical variants
    into a stable internal representation for analysis / testing.

Design principles:
  * Avoid external deps (use stdlib typing + dataclasses)
  * Be permissive in parsing (accept snake_case / camelCase variants)
  * Separate controlling stdout response (DecisionOutput) from log events
  * Provide to_dict() for serialization and factory parse() helpers

NOTE: We intentionally do not raise on unknown fields; they are preserved
in an 'extra' dict to prevent silent data loss during schema churn.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union, Iterable
from enum import Enum
import datetime as _dt

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """Get current timestamp in standard ISO 8601 format with UTC timezone."""
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _coerce_iso(ts: Any) -> Optional[str]:
    """Convert various timestamp formats to standard ISO 8601 format."""
    if ts is None:
        return None
    if isinstance(ts, str):
        # Already a string, assume it's ISO format
        return ts
    if isinstance(ts, (int, float)):
        try:
            # Handle different numeric formats
            timestamp_val = float(ts)
            if timestamp_val > 1e12:  # Likely milliseconds or nanoseconds
                if timestamp_val > 1e15:  # Likely nanoseconds
                    timestamp_val = timestamp_val / 1_000_000_000
                else:  # Likely milliseconds
                    timestamp_val = timestamp_val / 1000
            return _dt.datetime.fromtimestamp(timestamp_val, _dt.timezone.utc).isoformat()
        except Exception:
            return None
    return None


def _as_list(val: Any) -> List[Any]:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return [val]


# ---------------------------------------------------------------------------
# DAIC Mode enumeration
# ---------------------------------------------------------------------------

class DAICMode(Enum):
    """DAIC workflow modes with standardized string values"""
    DISCUSSION = "discussion"
    IMPLEMENTATION = "implementation"
    
    def __str__(self) -> str:
        """Return the string value for backward compatibility"""
        return self.value
    
    @classmethod
    def from_string(cls, mode_str: str) -> 'DAICMode':
        """Parse DAIC mode from string with case insensitivity"""
        if not mode_str:
            raise ValueError("Empty mode string")
        
        mode_lower = mode_str.lower().strip()
        for mode in cls:
            if mode.value.lower() == mode_lower:
                return mode
        
        raise ValueError(f"Unknown DAIC mode: {mode_str}")
    
    @classmethod  
    def is_valid_mode(cls, mode_str: str) -> bool:
        """Check if a string represents a valid DAIC mode"""
        try:
            cls.from_string(mode_str)
            return True
        except ValueError:
            return False


# ---------------------------------------------------------------------------
# Tool input / response variants
# ---------------------------------------------------------------------------

@dataclass
class CommandToolInput:
    command: str
    description: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def matches(data: Dict[str, Any]) -> bool:
        return 'command' in data
    
    def to_dict(self) -> Dict[str, Any]:
        result = {'command': self.command}
        if self.description:
            result['description'] = self.description
        result.update(self.extra)
        return result

@dataclass
class FileWriteToolInput:
    file_path: str
    content: str
    description: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def matches(data: Dict[str, Any]) -> bool:
        return 'file_path' in data and 'content' in data
    
    def to_dict(self) -> Dict[str, Any]:
        result = {'file_path': self.file_path, 'content': self.content}
        if self.description:
            result['description'] = self.description
        result.update(self.extra)
        return result

@dataclass
class FileEditToolInput:
    file_path: str
    old_string: Optional[str] = None
    new_string: Optional[str] = None
    oldString: Optional[str] = None
    newString: Optional[str] = None
    edits: Optional[List[Dict[str, Any]]] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def matches(data: Dict[str, Any]) -> bool:
        return 'file_path' in data and any(k in data for k in ('old_string','new_string','oldString','newString','edits'))
    
    def to_dict(self) -> Dict[str, Any]:
        result = {'file_path': self.file_path}
        for field in ['old_string', 'new_string', 'oldString', 'newString', 'edits']:
            value = getattr(self, field)
            if value is not None:
                result[field] = value
        result.update(self.extra)
        return result

ToolInputVariant = Union[CommandToolInput, FileWriteToolInput, FileEditToolInput]


def parse_tool_input(data: Optional[Dict[str, Any]]) -> Optional[ToolInputVariant]:
    if not data or not isinstance(data, dict):
        return None
    if CommandToolInput.matches(data):
        return CommandToolInput(
            command=data['command'],
            description=data.get('description'),
            extra={k:v for k,v in data.items() if k not in {'command','description'}}
        )
    if FileWriteToolInput.matches(data):
        return FileWriteToolInput(
            file_path=data['file_path'],
            content=data['content'],
            description=data.get('description'),
            extra={k:v for k,v in data.items() if k not in {'file_path','content','description'}}
        )
    if FileEditToolInput.matches(data):
        return FileEditToolInput(
            file_path=data['file_path'],
            old_string=data.get('old_string'),
            new_string=data.get('new_string'),
            oldString=data.get('oldString'),
            newString=data.get('newString'),
            edits=data.get('edits'),
            extra={k:v for k,v in data.items() if k not in {'file_path','old_string','new_string','oldString','newString','edits'}}
        )
    return None


@dataclass
class ToolResponse:
    filePath: Optional[str] = None
    oldString: Optional[str] = None
    newString: Optional[str] = None
    originalFile: Optional[str] = None
    structuredPatch: Optional[List[Any]] = None
    type: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def parse(raw: Any) -> Optional['ToolResponse']:
        if not isinstance(raw, dict):
            return None
        known = {k: raw.get(k) for k in ('filePath','oldString','newString','originalFile','structuredPatch','type')}
        extra = {k:v for k,v in raw.items() if k not in known}
        return ToolResponse(**known, extra=extra)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for field in ['filePath', 'oldString', 'newString', 'originalFile', 'structuredPatch', 'type']:
            value = getattr(self, field)
            if value is not None:
                result[field] = value
        result.update(self.extra)
        return result


# ---------------------------------------------------------------------------
# Hook stdin input structures (Claude -> Hook)
# ---------------------------------------------------------------------------

@dataclass
class BaseHookInput:
    session_id: str
    transcript_path: str
    cwd: str  # Required field from official specification
    hook_event_name: str
    raw: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def parse(data: Dict[str, Any]) -> 'BaseHookInput':
        return BaseHookInput(
            session_id=data.get('session_id',''),
            transcript_path=data.get('transcript_path',''),
            cwd=data.get('cwd',''),
            hook_event_name=data.get('hook_event_name',''),
            raw=data
        )


@dataclass
class PreToolUseInput:
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_name: str  # Required field from official specification
    tool_input: Optional[ToolInputVariant] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def parse(data: Dict[str, Any]) -> 'PreToolUseInput':
        return PreToolUseInput(
            session_id=data.get('session_id',''),
            transcript_path=data.get('transcript_path',''),
            cwd=data.get('cwd',''),
            hook_event_name=data.get('hook_event_name',''),
            tool_name=data.get('tool_name', ''),
            tool_input=parse_tool_input(data.get('tool_input')),
            raw=data
        )


@dataclass
class PostToolUseInput:
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    tool_name: str  # Required field from official specification
    tool_input: Optional[ToolInputVariant] = None
    tool_response: Optional[ToolResponse] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def parse(data: Dict[str, Any]) -> 'PostToolUseInput':
        return PostToolUseInput(
            session_id=data.get('session_id',''),
            transcript_path=data.get('transcript_path',''),
            cwd=data.get('cwd',''),
            hook_event_name=data.get('hook_event_name',''),
            tool_name=data.get('tool_name', ''),
            tool_input=parse_tool_input(data.get('tool_input')),
            tool_response=ToolResponse.parse(data.get('tool_response')),
            raw=data
        )


@dataclass
class UserPromptSubmitInput:
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str
    prompt: str  # Required field from official specification
    raw: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def parse(data: Dict[str, Any]) -> 'UserPromptSubmitInput':
        return UserPromptSubmitInput(
            session_id=data.get('session_id',''),
            transcript_path=data.get('transcript_path',''),
            cwd=data.get('cwd',''),
            hook_event_name=data.get('hook_event_name',''),
            prompt=data.get('prompt', ''),
            raw=data
        )


# ---------------------------------------------------------------------------  
# Hook output response schemas (for context injection and responses)
# ---------------------------------------------------------------------------

@dataclass
class HookSpecificOutput:
    hookEventName: str
    additionalContext: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"hookEventName": self.hookEventName}
        if self.additionalContext:
            result["additionalContext"] = self.additionalContext
        if self.metadata:
            result["metadata"] = self.metadata
        return result

@dataclass  
class UserPromptContextResponse:
    hookSpecificOutput: HookSpecificOutput
    debug: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"hookSpecificOutput": self.hookSpecificOutput.to_dict()}
        if self.debug:
            result["debug"] = self.debug
        return result
    
    @staticmethod
    def create_context(context: str, debug_info: Dict[str, Any] = None) -> 'UserPromptContextResponse':
        """Factory method for creating UserPromptSubmit context responses"""
        return UserPromptContextResponse(
            hookSpecificOutput=HookSpecificOutput(
                hookEventName="UserPromptSubmit",
                additionalContext=context
            ),
            debug=debug_info
        )

@dataclass
class SessionCorrelationResponse:
    success: bool
    session_id: str
    correlation_id: str
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp
        }

@dataclass
class DAICModeResult:
    success: bool
    old_mode: DAICMode  
    new_mode: DAICMode
    timestamp: str
    trigger: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "success": self.success,
            "old_mode": str(self.old_mode),
            "new_mode": str(self.new_mode),
            "timestamp": self.timestamp
        }
        if self.trigger:
            result["trigger"] = self.trigger
        return result

@dataclass
class ToolAnalysisResult:
    success: bool
    error_info: Dict[str, Any]
    execution_metrics: Dict[str, Any] 
    risk_factors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "error_info": self.error_info,
            "execution_metrics": self.execution_metrics,
            "risk_factors": self.risk_factors
        }

# ---------------------------------------------------------------------------
# Hook stdout decision (only enforced for pre_tool_use currently)
# ---------------------------------------------------------------------------

@dataclass
class PreToolUseDecisionOutput:
    continue_: bool
    stop_reason: Optional[str] = None  # Official spec field
    suppress_output: Optional[bool] = None  # Official spec capability  
    system_message: Optional[str] = None  # Official spec capability
    validation_issues: List[Dict[str, Any]] = field(default_factory=list)
    session_id: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {'continue': self.continue_}
        
        if self.stop_reason:
            result['stopReason'] = self.stop_reason
        if self.suppress_output is not None:
            result['suppressOutput'] = self.suppress_output
        if self.system_message:
            result['systemMessage'] = self.system_message
            
        # Hook-specific output per Claude Code specification
        hook_specific = {
            "hookEventName": "PreToolUse"
        }
        
        # Add permission decision based on continue status
        if self.continue_:
            hook_specific["permissionDecision"] = "allow"
            if self.stop_reason:
                hook_specific["permissionDecisionReason"] = self.stop_reason
        else:
            hook_specific["permissionDecision"] = "deny"  
            if self.stop_reason:
                hook_specific["permissionDecisionReason"] = self.stop_reason
        
        result['hookSpecificOutput'] = hook_specific
        return result

    @staticmethod
    def approve(reason: Optional[str] = None, session_id: Optional[str] = None) -> 'PreToolUseDecisionOutput':
        return PreToolUseDecisionOutput(True, stop_reason=reason, session_id=session_id)

    @staticmethod
    def block(reason: str, validation_issues: Iterable[str | Dict[str, Any]], 
              session_id: Optional[str] = None, suppress_output: bool = False) -> 'PreToolUseDecisionOutput':
        norm = []
        for v in validation_issues:
            if isinstance(v, str):
                norm.append({'message': v})
            else:
                norm.append(v)
        return PreToolUseDecisionOutput(False, stop_reason=reason, suppress_output=suppress_output,
                                      validation_issues=norm, session_id=session_id)


# ---------------------------------------------------------------------------
# Logged JSONL events (after enrichment)
# ---------------------------------------------------------------------------

@dataclass
class BaseLogEvent:
    session_id: str
    hook_event_name: str
    hook_name: str
    logged_at: str
    cwd: Optional[str] = None  # Current working directory from official spec
    working_directory: Optional[str] = None  # Legacy compatibility
    project_root: Optional[str] = None
    correlation_id: Optional[str] = None
    schema_version: Optional[str] = None
    workflow_phase: Optional[str] = None
    timestamp_ns: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def parse(data: Dict[str, Any]) -> 'BaseLogEvent':
        return BaseLogEvent(
            session_id=data.get('session_id',''),
            hook_event_name=data.get('hook_event_name',''),
            hook_name=data.get('hook_name',''),
            logged_at=data.get('logged_at') or _now_iso(),
            cwd=data.get('cwd'),
            working_directory=data.get('working_directory'),
            project_root=data.get('project_root'),
            correlation_id=data.get('correlation_id'),
            schema_version=data.get('schema_version'),
            workflow_phase=data.get('workflow_phase'),
            timestamp_ns=data.get('timestamp_ns'),
            extra={k:v for k,v in data.items() if k not in {
                'session_id','hook_event_name','hook_name','logged_at','cwd','working_directory','project_root',
                'correlation_id','schema_version','workflow_phase','timestamp_ns'
            }}
        )


@dataclass
class PreToolUseLogEvent(BaseLogEvent):
    tool_name: Optional[str] = None
    blocked: Optional[bool] = None
    validation_issues: List[Dict[str, Any]] = field(default_factory=list)
    tool_input: Optional[ToolInputVariant] = None

    @staticmethod
    def parse(data: Dict[str, Any]) -> 'PreToolUseLogEvent':
        base = BaseLogEvent.parse(data)
        raw_issues = data.get('validation_issues') or []
        issues: List[Dict[str, Any]] = []
        for v in raw_issues:
            if isinstance(v, str):
                issues.append({'message': v})
            elif isinstance(v, dict):
                issues.append(v)
        return PreToolUseLogEvent(
            **base.__dict__,
            tool_name=data.get('tool_name'),
            blocked=data.get('blocked'),
            validation_issues=issues,
            tool_input=parse_tool_input(data.get('tool_input'))
        )


@dataclass
class PostToolUseLogEvent(BaseLogEvent):
    tool_name: Optional[str] = None
    tool_input: Optional[ToolInputVariant] = None
    tool_response: Optional[ToolResponse] = None

    @staticmethod
    def parse(data: Dict[str, Any]) -> 'PostToolUseLogEvent':
        base = BaseLogEvent.parse(data)
        return PostToolUseLogEvent(
            **base.__dict__,
            tool_name=data.get('tool_name'),
            tool_input=parse_tool_input(data.get('tool_input')),
            tool_response=ToolResponse.parse(data.get('tool_response'))
        )


@dataclass
class UserPromptSubmitLogEvent(BaseLogEvent):
    prompt: Optional[str] = None
    context_injected: Optional[bool] = None
    context_length: Optional[int] = None
    intent_analysis: Optional[Dict[str, Any]] = None

    @staticmethod
    def parse(data: Dict[str, Any]) -> 'UserPromptSubmitLogEvent':
        base = BaseLogEvent.parse(data)
        return UserPromptSubmitLogEvent(
            **base.__dict__,
            prompt=data.get('prompt'),
            context_injected=data.get('context_injected'),
            context_length=data.get('context_length'),
            intent_analysis=data.get('intent_analysis')
        )


LogEventVariant = Union[PreToolUseLogEvent, PostToolUseLogEvent, UserPromptSubmitLogEvent, BaseLogEvent]


def parse_log_event(data: Dict[str, Any]) -> LogEventVariant:
    name = data.get('hook_name') or ''
    if name == 'pre_tool_use':
        return PreToolUseLogEvent.parse(data)
    if name == 'post_tool_use':
        return PostToolUseLogEvent.parse(data)
    if name == 'user_prompt_submit':
        return UserPromptSubmitLogEvent.parse(data)
    return BaseLogEvent.parse(data)


# ---------------------------------------------------------------------------
# Central DB row representation
# ---------------------------------------------------------------------------

@dataclass
class CentralHookEventRow:
    project_source: str
    original_id: Union[int, str, None]
    timestamp: Optional[float]
    hook_name: str
    event_type: str
    correlation_id: Optional[str]
    session_id: Optional[str]
    success: Optional[bool]
    duration_ms: Optional[float]
    data: Dict[str, Any]
    created_at: Optional[str]

    @staticmethod
    def parse(row: Dict[str, Any]) -> 'CentralHookEventRow':
        raw_data = row.get('data')
        if isinstance(raw_data, str):
            import json
            try:
                raw_data = json.loads(raw_data)
            except Exception:
                raw_data = {'raw': raw_data}
        return CentralHookEventRow(
            project_source=row.get('project_source',''),
            original_id=row.get('original_id'),
            timestamp=row.get('timestamp'),
            hook_name=row.get('hook_name',''),
            event_type=row.get('event_type','hook_execution'),
            correlation_id=row.get('correlation_id'),
            session_id=row.get('session_id'),
            success=row.get('success'),
            duration_ms=row.get('duration_ms'),
            data=raw_data if isinstance(raw_data, dict) else {},
            created_at=row.get('created_at')
        )


# ---------------------------------------------------------------------------
# Developer attribution
# ---------------------------------------------------------------------------

@dataclass
class DeveloperInfo:
    """Developer attribution information for analytics and tracking"""
    name: Optional[str] = None
    email: Optional[str] = None
    source: str = "unknown"  # git, config, unknown
    
    @staticmethod
    def parse(data: Dict[str, Any]) -> 'DeveloperInfo':
        """Parse developer info from dict (backward compatibility)"""
        return DeveloperInfo(
            name=data.get('name'),
            email=data.get('email'),
            source=data.get('source', 'unknown')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization"""
        return {
            'name': self.name,
            'email': self.email,
            'source': self.source
        }


# ---------------------------------------------------------------------------
# Configuration Data Classes  
# ---------------------------------------------------------------------------

@dataclass
class DeveloperConfig:
    """Developer information configuration"""
    name: str = "Developer"
    email: str = "developer@example.com"
    git_identity_source: str = "auto"  # "auto", "config", "manual"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "git_identity_source": self.git_identity_source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeveloperConfig':
        return cls(
            name=data.get("name", "Developer"),
            email=data.get("email", "developer@example.com"),
            git_identity_source=data.get("git_identity_source", "auto")
        )


@dataclass
class PreferencesConfig:
    """User preferences configuration"""
    daic_default_mode: str = field(default_factory=lambda: str(DAICMode.DISCUSSION))
    context_warning_threshold: int = 75
    analytics_participation: bool = True
    statusline_format: str = "full"  # "full", "compact", "minimal"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "daic_default_mode": self.daic_default_mode,
            "context_warning_threshold": self.context_warning_threshold,
            "analytics_participation": self.analytics_participation,
            "statusline_format": self.statusline_format
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PreferencesConfig':
        return cls(
            daic_default_mode=data.get("daic_default_mode", str(DAICMode.DISCUSSION)),
            context_warning_threshold=data.get("context_warning_threshold", 75),
            analytics_participation=data.get("analytics_participation", True),
            statusline_format=data.get("statusline_format", "full")
        )


@dataclass
class TeamConfig:
    """Team and organization configuration"""
    organization: str = ""
    project_role: str = "developer"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "organization": self.organization,
            "project_role": self.project_role
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamConfig':
        return cls(
            organization=data.get("organization", ""),
            project_role=data.get("project_role", "developer")
        )


@dataclass
class UserConfig:
    """Complete user configuration structure"""
    developer: DeveloperConfig = field(default_factory=DeveloperConfig)
    preferences: PreferencesConfig = field(default_factory=PreferencesConfig)
    team: TeamConfig = field(default_factory=TeamConfig)
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "developer": self.developer.to_dict(),
            "preferences": self.preferences.to_dict(),
            "team": self.team.to_dict(),
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserConfig':
        return cls(
            developer=DeveloperConfig.from_dict(data.get("developer", {})),
            preferences=PreferencesConfig.from_dict(data.get("preferences", {})),
            team=TeamConfig.from_dict(data.get("team", {})),
            version=data.get("version", "1.0")
        )


@dataclass
class ReadOnlyCommandsConfig:
    """Configuration for read-only bash commands"""
    basic: List[str] = field(default_factory=lambda: [
        "ls", "ll", "pwd", "cd", "echo", "cat", "head", "tail", "less", "more",
        "grep", "rg", "find", "fd", "which", "whereis", "type", "file", "stat",
        "du", "df", "tree", "basename", "dirname", "realpath", "readlink",
        "whoami", "env", "printenv", "date", "cal", "uptime", "wc", "cut",
        "sort", "uniq", "comm", "diff", "cmp", "md5sum", "sha256sum"
    ])
    git: List[str] = field(default_factory=lambda: [
        "git status", "git log", "git diff", "git show", "git branch",
        "git remote", "git fetch", "git describe", "git rev-parse", "git blame"
    ])
    docker: List[str] = field(default_factory=lambda: [
        "docker ps", "docker images", "docker logs"
    ])
    package_managers: List[str] = field(default_factory=lambda: [
        "npm list", "npm ls", "pip list", "pip show", "yarn list"
    ])
    network: List[str] = field(default_factory=lambda: [
        "curl", "wget", "ping", "nslookup", "dig"
    ])
    text_processing: List[str] = field(default_factory=lambda: [
        "jq", "awk", "sed -n"
    ])
    
    def to_dict(self) -> Dict[str, List[str]]:
        return {
            "basic": self.basic,
            "git": self.git,
            "docker": self.docker,
            "package_managers": self.package_managers,
            "network": self.network,
            "text_processing": self.text_processing
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReadOnlyCommandsConfig':
        return cls(
            basic=data.get("basic", []),
            git=data.get("git", []),
            docker=data.get("docker", []),
            package_managers=data.get("package_managers", []),
            network=data.get("network", []),
            text_processing=data.get("text_processing", [])
        )


@dataclass
class BranchEnforcementConfig:
    """Configuration for branch enforcement rules"""
    enabled: bool = True
    task_prefixes: List[str] = field(default_factory=lambda: [
        "implement-", "fix-", "refactor-", "migrate-", "test-", "docs-"
    ])
    branch_prefixes: Dict[str, str] = field(default_factory=lambda: {
        "implement-": "feature/",
        "fix-": "fix/", 
        "refactor-": "feature/",
        "migrate-": "feature/",
        "test-": "feature/",
        "docs-": "feature/"
    })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "task_prefixes": self.task_prefixes,
            "branch_prefixes": self.branch_prefixes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BranchEnforcementConfig':
        return cls(
            enabled=data.get("enabled", True),
            task_prefixes=data.get("task_prefixes", []),
            branch_prefixes=data.get("branch_prefixes", {})
        )


@dataclass
class IntelligenceConfig:
    """Configuration for DAIC intelligence features"""
    codebase_learning: bool = True
    pattern_recognition: bool = True
    smart_recommendations: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "codebase_learning": self.codebase_learning,
            "pattern_recognition": self.pattern_recognition,
            "smart_recommendations": self.smart_recommendations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntelligenceConfig':
        return cls(
            codebase_learning=data.get("codebase_learning", True),
            pattern_recognition=data.get("pattern_recognition", True),
            smart_recommendations=data.get("smart_recommendations", True)
        )


@dataclass
class TaskDetectionConfig:
    """Configuration for task detection features"""
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {"enabled": self.enabled}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskDetectionConfig':
        return cls(enabled=data.get("enabled", True))


@dataclass
class DAICConfig:
    """Complete DAIC configuration structure"""
    enabled: bool = True
    default_mode: str = field(default_factory=lambda: str(DAICMode.DISCUSSION))
    trigger_phrases: List[str] = field(default_factory=lambda: [
        "make it so", "run that", "go ahead", "ship it", "let's do it", "execute", "implement it"
    ])
    blocked_tools: List[str] = field(default_factory=lambda: [
        "Edit", "Write", "MultiEdit", "NotebookEdit"
    ])
    branch_enforcement: BranchEnforcementConfig = field(default_factory=BranchEnforcementConfig)
    read_only_bash_commands: ReadOnlyCommandsConfig = field(default_factory=ReadOnlyCommandsConfig)
    intelligence: IntelligenceConfig = field(default_factory=IntelligenceConfig)
    task_detection: TaskDetectionConfig = field(default_factory=TaskDetectionConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "default_mode": self.default_mode,
            "trigger_phrases": self.trigger_phrases,
            "blocked_tools": self.blocked_tools,
            "branch_enforcement": self.branch_enforcement.to_dict(),
            "read_only_bash_commands": self.read_only_bash_commands.to_dict(),
            "intelligence": self.intelligence.to_dict(),
            "task_detection": self.task_detection.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DAICConfig':
        return cls(
            enabled=data.get("enabled", True),
            default_mode=data.get("default_mode", str(DAICMode.DISCUSSION)),
            trigger_phrases=data.get("trigger_phrases", []),
            blocked_tools=data.get("blocked_tools", []),
            branch_enforcement=BranchEnforcementConfig.from_dict(data.get("branch_enforcement", {})),
            read_only_bash_commands=ReadOnlyCommandsConfig.from_dict(data.get("read_only_bash_commands", {})),
            intelligence=IntelligenceConfig.from_dict(data.get("intelligence", {})),
            task_detection=TaskDetectionConfig.from_dict(data.get("task_detection", {}))
        )


# ---------------------------------------------------------------------------
# Operation Result Types
# ---------------------------------------------------------------------------

@dataclass
class OperationResult:
    """Base class for standardized operation results across the system"""
    success: bool = field()
    timestamp: str = field(default_factory=_now_iso)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "success": self.success,
            "timestamp": self.timestamp,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "metadata": self.metadata
        }
    
    @classmethod
    def success_result(cls, **metadata) -> 'OperationResult':
        """Factory method for successful operations"""
        return cls(success=True, metadata=metadata)
    
    @classmethod
    def error_result(cls, error_code: str, error_message: str, **metadata) -> 'OperationResult':
        """Factory method for failed operations"""
        return cls(
            success=False, 
            error_code=error_code, 
            error_message=error_message,
            metadata=metadata
        )


@dataclass
class DAICModeOperationResult(OperationResult):
    """Result type for DAIC mode operations (toggle, set, etc.)"""
    old_mode: Optional[DAICMode] = None
    new_mode: Optional[DAICMode] = None
    trigger: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = super().to_dict()
        result.update({
            "old_mode": str(self.old_mode) if self.old_mode else None,
            "new_mode": str(self.new_mode) if self.new_mode else None,
            "trigger": self.trigger
        })
        return result
    
    @classmethod
    def successful_toggle(cls, old_mode: DAICMode, new_mode: DAICMode, trigger: str = None) -> 'DAICModeOperationResult':
        """Factory method for successful mode toggles"""
        return cls(
            success=True,
            old_mode=old_mode,
            new_mode=new_mode,
            trigger=trigger
        )
    
    @classmethod
    def successful_set(cls, mode: DAICMode, trigger: str = None) -> 'DAICModeOperationResult':
        """Factory method for successful mode sets"""
        return cls(
            success=True,
            new_mode=mode,
            trigger=trigger
        )
    
    @classmethod
    def failed_operation(cls, error_code: str, error_message: str) -> 'DAICModeOperationResult':
        """Factory method for failed DAIC operations"""
        return cls(
            success=False,
            error_code=error_code,
            error_message=error_message
        )


@dataclass
class ModeDisplayInfo:
    """Display information for DAIC mode with emoji, color, and success status"""
    mode: str = field()
    emoji: str = field()
    color: str = field()
    success: bool = field()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "mode": self.mode,
            "emoji": self.emoji,
            "color": self.color,
            "success": self.success
        }
    
    @classmethod
    def success_display(cls, mode: DAICMode, emoji: str, color: str) -> 'ModeDisplayInfo':
        """Factory method for successful mode display"""
        return cls(
            mode=str(mode),
            emoji=emoji,
            color=color,
            success=True
        )
    
    @classmethod
    def error_display(cls, mode: str = "unknown", emoji: str = "❓", color: str = "white") -> 'ModeDisplayInfo':
        """Factory method for error mode display"""
        return cls(
            mode=mode,
            emoji=emoji,
            color=color,
            success=False
        )


@dataclass
class ToolBlockingResult:
    """Result type for tool blocking decisions in DAIC workflow"""
    should_block: bool = field()
    reason: str = field()
    blocking_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "should_block": self.should_block,
            "reason": self.reason,
            "blocking_type": self.blocking_type,
            "metadata": self.metadata
        }
    
    def to_tuple(self) -> tuple[bool, str]:
        """Convert to tuple for backward compatibility"""
        return self.should_block, self.reason
    
    @classmethod
    def allow_tool(cls, reason: str = "Tool allowed") -> 'ToolBlockingResult':
        """Factory method for allowing tools"""
        return cls(
            should_block=False,
            reason=reason,
            blocking_type=None
        )
    
    @classmethod
    def block_tool(cls, reason: str, blocking_type: str = "DAIC_BLOCKED") -> 'ToolBlockingResult':
        """Factory method for blocking tools"""
        return cls(
            should_block=True,
            reason=reason,
            blocking_type=blocking_type
        )
    
    @classmethod
    def security_block(cls, reason: str) -> 'ToolBlockingResult':
        """Factory method for security-related blocks"""
        return cls(
            should_block=True,
            reason=reason,
            blocking_type="SECURITY_BLOCKED"
        )
    
    @classmethod
    def discussion_mode_block(cls, tool_name: str, detail: str = None) -> 'ToolBlockingResult':
        """Factory method for discussion mode blocks"""
        if detail:
            reason = f"[DAIC: Tool Blocked] {detail}"
        else:
            reason = f"[DAIC: Tool Blocked] You're in discussion mode. The {tool_name} tool is not allowed. You need to seek alignment first."
        
        return cls(
            should_block=True,
            reason=reason,
            blocking_type="DISCUSSION_MODE_BLOCKED",
            metadata={"blocked_tool": tool_name}
        )
    
    @classmethod
    def command_block(cls, command: str, detail: str = None) -> 'ToolBlockingResult':
        """Factory method for command-specific blocks"""
        if detail:
            reason = f"[DAIC: Command Blocked] {detail}"
        else:
            reason = f"[DAIC: Command Blocked] Potentially modifying Bash command blocked in discussion mode: {command}"
        
        return cls(
            should_block=True,
            reason=reason,
            blocking_type="COMMAND_BLOCKED",
            metadata={"blocked_command": command}
        )


@dataclass
class CorrelationUpdateResult:
    """Result type for session correlation update operations"""
    success: bool = field()
    session_id: str = field()
    correlation_id: str = field()
    timestamp: str = field(default_factory=_now_iso)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "success": self.success,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp
        }
        if self.error:
            result["error"] = self.error
        if self.metadata:
            result["metadata"] = self.metadata
        return result
    
    @classmethod
    def successful_update(cls, session_id: str, correlation_id: str) -> 'CorrelationUpdateResult':
        """Factory method for successful correlation updates"""
        return cls(
            success=True,
            session_id=session_id,
            correlation_id=correlation_id
        )
    
    @classmethod
    def failed_update(cls, session_id: str, correlation_id: str, error: str) -> 'CorrelationUpdateResult':
        """Factory method for failed correlation updates"""
        return cls(
            success=False,
            session_id=session_id,
            correlation_id=correlation_id,
            error=error
        )
    
    @classmethod
    def invalid_session_id(cls) -> 'CorrelationUpdateResult':
        """Factory method for invalid session ID error"""
        return cls(
            success=False,
            session_id="",
            correlation_id="",
            error="Invalid session_id"
        )
    
    @classmethod
    def invalid_correlation_id(cls) -> 'CorrelationUpdateResult':
        """Factory method for invalid correlation ID error"""
        return cls(
            success=False,
            session_id="",
            correlation_id="",
            error="Invalid correlation_id"
        )


@dataclass
class ConsistencyCheckResult:
    """Result type for session correlation consistency checks"""
    consistent: bool = field()
    inconsistencies: List[str] = field(default_factory=list)
    unified_session: Optional[str] = None
    unified_correlation: Optional[str] = None
    task_session: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "consistent": self.consistent,
            "inconsistencies": self.inconsistencies,
            "unified_session": self.unified_session,
            "unified_correlation": self.unified_correlation,
            "task_session": self.task_session
        }
        if self.error:
            result["error"] = self.error
        if self.metadata:
            result["metadata"] = self.metadata
        return result
    
    @classmethod
    def consistent_state(cls, unified_session: str = None, unified_correlation: str = None, 
                        task_session: str = None) -> 'ConsistencyCheckResult':
        """Factory method for consistent state"""
        return cls(
            consistent=True,
            unified_session=unified_session,
            unified_correlation=unified_correlation,
            task_session=task_session
        )
    
    @classmethod
    def inconsistent_state(cls, inconsistencies: List[str], unified_session: str = None, 
                          unified_correlation: str = None, task_session: str = None) -> 'ConsistencyCheckResult':
        """Factory method for inconsistent state"""
        return cls(
            consistent=False,
            inconsistencies=inconsistencies,
            unified_session=unified_session,
            unified_correlation=unified_correlation,
            task_session=task_session
        )
    
    @classmethod
    def check_failed(cls, error: str) -> 'ConsistencyCheckResult':
        """Factory method for failed consistency checks"""
        return cls(
            consistent=False,
            error=error
        )


@dataclass
class IdGenerationResult:
    """Result type for session and correlation ID generation"""
    session_id: str = field()
    correlation_id: str = field()
    timestamp: str = field(default_factory=_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    def to_tuple(self) -> Tuple[str, str]:
        """Convert to tuple for backward compatibility"""
        return self.session_id, self.correlation_id


# ---------------------------------------------------------------------------
# Analytics Result Types
# ---------------------------------------------------------------------------

@dataclass
class DatabaseStats:
    """Analytics database statistics with performance metrics"""
    total_events: int = field()
    unique_sessions: int = field()
    unique_correlations: int = field()
    active_projects: int = field()
    overall_success_rate: float = field()
    avg_duration_ms: float = field()
    analysis_window_hours: int = field()
    timestamp: str = field(default_factory=_now_iso)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'total_events': self.total_events,
            'unique_sessions': self.unique_sessions,
            'unique_correlations': self.unique_correlations,
            'active_projects': self.active_projects,
            'overall_success_rate': self.overall_success_rate,
            'avg_duration_ms': self.avg_duration_ms,
            'analysis_window_hours': self.analysis_window_hours,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_query_result(cls, stats: tuple, hours: int) -> 'DatabaseStats':
        """Factory method for creating from database query results"""
        return cls(
            total_events=stats[0] or 0,
            unique_sessions=stats[1] or 0,
            unique_correlations=stats[2] or 0,
            active_projects=stats[3] or 0,
            overall_success_rate=(stats[4] or 0) * 100,
            avg_duration_ms=stats[5] or 0,
            analysis_window_hours=hours
        )
    
    @classmethod
    def empty_stats(cls, hours: int = 24) -> 'DatabaseStats':
        """Factory method for empty stats (error case)"""
        return cls(
            total_events=0,
            unique_sessions=0,
            unique_correlations=0,
            active_projects=0,
            overall_success_rate=0.0,
            avg_duration_ms=0.0,
            analysis_window_hours=hours
        )


@dataclass
class HarvestResults:
    """Results from data harvesting operations"""
    harvested_sources: int = 0
    new_events: int = 0
    new_session_notes: int = 0
    errors: List[str] = field(default_factory=list)
    sources_processed: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=_now_iso)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'harvested_sources': self.harvested_sources,
            'new_events': self.new_events,
            'new_session_notes': self.new_session_notes,
            'errors': self.errors,
            'sources_processed': self.sources_processed,
            'timestamp': self.timestamp
        }
    
    def add_source_result(self, source_name: str, events: int, notes: int):
        """Add results from processing a source"""
        self.harvested_sources += 1
        self.new_events += events
        self.new_session_notes += notes
        self.sources_processed.append({
            'name': source_name,
            'new_events': events,
            'new_session_notes': notes,
            'timestamp': _now_iso()
        })
    
    def add_error(self, error_message: str):
        """Add an error to the results"""
        self.errors.append(error_message)
    
    @classmethod
    def empty_results(cls) -> 'HarvestResults':
        """Factory method for empty harvest results"""
        return cls()


@dataclass
class CorrelationOperationResult:
    """Results from session correlation operations"""
    correlations_created: int = field()
    correlations_updated: int = field()
    operation_type: str = field()
    correlation_stats: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=_now_iso)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            'correlations_created': self.correlations_created,
            'correlations_updated': self.correlations_updated,
            'operation_type': self.operation_type,
            'timestamp': self.timestamp
        }
        if self.correlation_stats:
            result['correlation_stats'] = self.correlation_stats
        if self.errors:
            result['errors'] = self.errors
        return result
    
    @classmethod
    def successful_operation(cls, created: int, updated: int, operation_type: str = "correlation",
                           stats: Dict[str, Any] = None) -> 'CorrelationOperationResult':
        """Factory method for successful correlation operations"""
        return cls(
            correlations_created=created,
            correlations_updated=updated,
            operation_type=operation_type,
            correlation_stats=stats
        )
    
    @classmethod
    def failed_operation(cls, operation_type: str, error: str) -> 'CorrelationOperationResult':
        """Factory method for failed correlation operations"""
        return cls(
            correlations_created=0,
            correlations_updated=0,
            operation_type=operation_type,
            errors=[error]
        )


@dataclass
class HourlyProductivityStats:
    """Hourly productivity analysis results"""
    hour: int = field()
    event_count: int = field()
    success_rate: float = field()
    session_count: int = field()
    avg_duration: float = field()
    day_of_week: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            'hour': self.hour,
            'event_count': self.event_count,
            'success_rate': self.success_rate,
            'session_count': self.session_count,
            'avg_duration': self.avg_duration
        }
        if self.day_of_week is not None:
            result['day_of_week'] = self.day_of_week
        return result


@dataclass
class HarvestStatistics:
    """Statistics from data harvesting operations"""
    projects: List[Dict[str, Any]] = field(default_factory=list)
    harvest_tracking: List[Dict[str, Any]] = field(default_factory=list)
    total_projects: int = 0
    total_events: int = 0
    timestamp: str = field(default_factory=_now_iso)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'projects': self.projects,
            'harvest_tracking': self.harvest_tracking,
            'total_projects': self.total_projects,
            'total_events': self.total_events,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_query_results(cls, projects: List[Dict[str, Any]], 
                          tracking: List[Dict[str, Any]]) -> 'HarvestStatistics':
        """Factory method for creating from database query results"""
        return cls(
            projects=projects,
            harvest_tracking=tracking,
            total_projects=len(projects),
            total_events=sum(p.get('event_count', 0) for p in projects)
        )


# ---------------------------------------------------------------------------
# Normalization convenience for tests / analytics
# ---------------------------------------------------------------------------

def normalize_validation_issues(issues: List[Dict[str, Any]]) -> List[str]:
    """Return only message strings for comparison use."""
    out = []
    for issue in issues:
        if isinstance(issue, dict):
            msg = issue.get('message') or issue.get('detail') or str(issue)
            out.append(msg)
        elif isinstance(issue, str):
            out.append(issue)
    return out


def to_json_serializable(obj: Any) -> Any:
    """Convert typed objects to JSON-serializable format."""
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        # For dataclasses without to_dict method
        result = {}
        for key, value in obj.__dict__.items():
            result[key] = to_json_serializable(value)
        return result
    elif isinstance(obj, list):
        return [to_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: to_json_serializable(value) for key, value in obj.items()}
    else:
        return obj


# ---------------------------------------------------------------------------
# Timestamp utilities for standardization
# ---------------------------------------------------------------------------

def get_standard_timestamp() -> str:
    """Get current timestamp in standard ISO 8601 format with UTC timezone.
    
    This is the canonical format for all timestamps in the brainworm system.
    Format: "2025-08-11T13:34:27.254010+00:00"
    """
    return _dt.datetime.now(_dt.timezone.utc).isoformat()

def parse_standard_timestamp(ts: str) -> _dt.datetime:
    """Parse standard timestamp with fallback for legacy formats.
    
    Args:
        ts: Timestamp string in ISO 8601 format or legacy numeric format
        
    Returns:
        datetime object in UTC timezone
        
    Raises:
        ValueError: If timestamp cannot be parsed
    """
    if not ts:
        raise ValueError("Empty timestamp")
        
    # Try ISO format first
    try:
        return _dt.datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        pass
    
    # Fallback to numeric timestamp parsing
    try:
        timestamp_val = float(ts)
        if timestamp_val > 1e12:  # Likely milliseconds or nanoseconds
            if timestamp_val > 1e15:  # Likely nanoseconds
                timestamp_val = timestamp_val / 1_000_000_000
            else:  # Likely milliseconds
                timestamp_val = timestamp_val / 1000
        return _dt.datetime.fromtimestamp(timestamp_val, _dt.timezone.utc)
    except (ValueError, TypeError):
        pass
    
    raise ValueError(f"Cannot parse timestamp: {ts}")

def format_for_database(ts: str) -> str:
    """Ensure timestamp is in correct format for database storage.
    
    Args:
        ts: Timestamp in any supported format
        
    Returns:
        ISO 8601 timestamp string suitable for database storage
    """
    if not ts:
        return get_standard_timestamp()
        
    try:
        # Parse and re-format to ensure consistency
        parsed = parse_standard_timestamp(ts)
        return parsed.isoformat()
    except ValueError:
        # Fallback to current timestamp
        return get_standard_timestamp()

__all__ = [
    'BaseHookInput','PreToolUseInput','PostToolUseInput','UserPromptSubmitInput',
    'PreToolUseDecisionOutput','CommandToolInput','FileWriteToolInput','FileEditToolInput',
    'ToolResponse','parse_tool_input','BaseLogEvent','PreToolUseLogEvent','PostToolUseLogEvent',
    'UserPromptSubmitLogEvent','parse_log_event','CentralHookEventRow','DeveloperInfo','normalize_validation_issues',
    'to_json_serializable','get_standard_timestamp','parse_standard_timestamp','format_for_database',
    # DAIC Mode enumeration
    'DAICMode',
    # Configuration data classes
    'DeveloperConfig','PreferencesConfig','TeamConfig','UserConfig',
    'ReadOnlyCommandsConfig','BranchEnforcementConfig','IntelligenceConfig','TaskDetectionConfig','DAICConfig',
    # Operation result types
    'OperationResult','DAICModeOperationResult',
    # Analytics result types
    'DatabaseStats','HarvestResults','CorrelationOperationResult','HourlyProductivityStats','HarvestStatistics',
    # Output schema classes for type-safe responses
    'HookSpecificOutput','UserPromptContextResponse','SessionCorrelationResponse',
    'DAICModeResult','ToolAnalysisResult'
]
