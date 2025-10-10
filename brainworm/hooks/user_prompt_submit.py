#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "toml>=0.10.0",
# ]
# ///

"""
User Prompt Submit Hook - Hooks Framework

Intelligent context injection system with DAIC workflow management.
Provides Claude with contextual guidance based on user prompts.
"""

# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List
from utils.hook_framework import HookFramework
from utils.business_controllers import create_daic_controller
from utils.hook_types import UserPromptContextResponse, DAICMode


def get_basic_prompt_info(prompt: str) -> Dict[str, Any]:
    """Get basic prompt information - no intent analysis, just facts"""
    return {
        'length_chars': len(prompt),
        'word_count': len(prompt.split()),
        'has_question': '?' in prompt,
        'has_code_references': bool('`' in prompt or '.py' in prompt or '.js' in prompt),
        'is_empty': len(prompt.strip()) == 0
    }

def get_context_length_from_transcript(transcript_path: str) -> int:
    """Get current context length from the most recent main-chain message in transcript"""
    try:
        import os
        if not os.path.exists(transcript_path):
            return 0
            
        with open(transcript_path, 'r') as f:
            lines = f.readlines()
        
        most_recent_usage = None
        most_recent_timestamp = None
        
        # Parse each JSONL entry
        for line in lines:
            try:
                data = json.loads(line.strip())
                # Skip sidechain entries (subagent calls)
                if data.get('isSidechain', False):
                    continue
                    
                # Check if this entry has usage data
                if data.get('message', {}).get('usage'):
                    entry_time = data.get('timestamp')
                    # Track the most recent main-chain entry with usage
                    if entry_time and (not most_recent_timestamp or entry_time > most_recent_timestamp):
                        most_recent_timestamp = entry_time
                        most_recent_usage = data['message']['usage']
            except json.JSONDecodeError:
                continue
        
        # Calculate context length from most recent usage
        if most_recent_usage:
            context_length = (
                most_recent_usage.get('input_tokens', 0) +
                most_recent_usage.get('cache_read_input_tokens', 0) +
                most_recent_usage.get('cache_creation_input_tokens', 0)
            )
            return context_length
    except Exception:
        pass
    return 0

def check_context_warnings(transcript_path: str, project_root: Path) -> str:
    """Check and create context usage warnings based on cc-sessions logic"""
    context_warning = ""
    
    try:
        if not transcript_path:
            return context_warning
        
        context_length = get_context_length_from_transcript(transcript_path)
        if context_length > 0:
            # Calculate percentage of usable context (160k practical limit before auto-compact)
            usable_percentage = (context_length / 160000) * 100
            
            # Check for warning flag files to avoid repeating warnings
            state_dir = project_root / ".brainworm" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            
            warning_75_flag = state_dir / "context-warning-75.flag"
            warning_90_flag = state_dir / "context-warning-90.flag"
            
            # Token warnings (only show once per session)
            if usable_percentage >= 90 and not warning_90_flag.exists():
                context_warning = f"\n[90% WARNING] {context_length:,}/160,000 tokens used ({usable_percentage:.1f}%). CRITICAL: Run context compaction to wrap up this session cleanly!\n"
                warning_90_flag.touch()
            elif usable_percentage >= 75 and not warning_75_flag.exists():
                context_warning = f"\n[75% WARNING] {context_length:,}/160,000 tokens used ({usable_percentage:.1f}%). Context is getting low. Be aware of coming context compaction trigger.\n"
                warning_75_flag.touch()
    except Exception:
        pass
    
    return context_warning


# DAIC Workflow Functions using Hooks Framework

def get_daic_state(project_root: Path) -> Dict[str, Any]:
    """Get current DAIC state using business controllers"""
    try:
        controller = create_daic_controller(project_root)
        mode_info = controller.get_mode_with_display()
        
        return {
            "mode": mode_info.mode,
            "timestamp": None,  # Not tracked in this interface
            "previous_mode": None,  # Not tracked in this interface
            "trigger": "business_controller"
        }
    except Exception:
        return {"mode": str(DAICMode.DISCUSSION), "timestamp": None, "previous_mode": None, "trigger": None}


def set_daic_mode(project_root: Path, mode: str, trigger: str = None) -> Dict[str, Any]:
    """Set DAIC mode using business controllers"""
    try:
        controller = create_daic_controller(project_root)
        result = controller.set_mode(mode, trigger=trigger)
        
        return {
            "mode": str(result.new_mode) if result.success and result.new_mode else str(DAICMode.DISCUSSION),
            "timestamp": result.timestamp if result.success else datetime.now(timezone.utc).isoformat(),
            "previous_mode": str(result.old_mode) if result.old_mode else None,
            "trigger": result.trigger or trigger or "user_prompt_submit",
            "success": result.success,
            "error": result.error_message if not result.success else None
        }
    except Exception as e:
        return {
            "mode": str(DAICMode.DISCUSSION),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_mode": None,
            "trigger": trigger or "user_prompt_submit",
            "success": False,
            "error": str(e)
        }


def detect_trigger_phrases(prompt: str, trigger_phrases: List[str]) -> str:
    """Detect trigger phrases in user prompt"""
    prompt_lower = prompt.lower()
    for phrase in trigger_phrases:
        if phrase.lower() in prompt_lower:
            return phrase
    return None


def detect_emergency_stop(prompt: str) -> bool:
    """Detect emergency stop commands"""
    return any(word in prompt for word in ["SILENCE", "STOP"])


def detect_protocols(prompt: str) -> List[str]:
    """Detect protocol-triggering phrases"""
    protocols = []
    prompt_lower = prompt.lower()
    
    # Context compaction detection
    if any(phrase in prompt_lower for phrase in ["compact", "restart session", "context compaction"]):
        protocols.append("context-compaction")
    
    # Task completion detection
    if any(phrase in prompt_lower for phrase in ["complete the task", "finish the task", "task is done", 
                                                   "mark as complete", "close the task", "wrap up the task"]):
        protocols.append("task-completion")
    
    # Task creation detection
    if any(phrase in prompt_lower for phrase in ["create a new task", "create a task", "make a task",
                                                   "new task for", "add a task"]):
        protocols.append("task-creation")
    
    # Task switching detection
    if any(phrase in prompt_lower for phrase in ["switch to task", "work on task", "change to task"]):
        protocols.append("task-startup")
    
    return protocols


def detect_task_patterns(prompt: str) -> bool:
    """Detect patterns that suggest task creation might be needed"""
    task_patterns = [
        r"(?i)we (should|need to|have to) (implement|fix|refactor|migrate|test|research)",
        r"(?i)create a task for",
        r"(?i)add this to the (task list|todo|backlog)",
        r"(?i)we'll (need to|have to) (do|handle|address) (this|that) later",
        r"(?i)that's a separate (task|issue|problem)",
        r"(?i)file this as a (bug|task|issue)"
    ]
    
    return any(re.search(pattern, prompt) for pattern in task_patterns)

def user_prompt_submit_logic(input_data: Dict[str, Any], project_root: Path, config: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """Custom logic for user prompt submit processing"""
    # Get DAIC configuration
    daic_config = config.get("daic", {})
    
    # Extract data
    session_id = input_data.get('session_id', 'unknown')
    prompt = input_data.get('prompt', '')
    transcript_path = input_data.get('transcript_path', '')
    
    # Initialize context response
    context = ""
    debug_info = {}
    
    # Check for context warnings
    context_warning = check_context_warnings(transcript_path, project_root)
    if context_warning:
        print(context_warning, file=sys.stderr)
    
    # DAIC Workflow Processing (only if enabled)
    if daic_config.get("enabled", True):
        # Get current DAIC state
        current_daic_state = get_daic_state(project_root)
        current_mode = current_daic_state.get("mode", str(DAICMode.DISCUSSION))
        is_discussion_mode = current_mode == str(DAICMode.DISCUSSION)
        
        # Emergency stop detection
        if detect_emergency_stop(prompt):
            set_daic_mode(project_root, str(DAICMode.DISCUSSION), "emergency_stop")
            context += "[DAIC: EMERGENCY STOP] All tools locked. You are now in discussion mode. Re-align with your pair programmer.\n"
            if verbose:
                print("🚫 Emergency stop activated - forced to discussion mode", file=sys.stderr)
        
        # Trigger phrase detection (only in discussion mode)
        # NOTE: Only user prompts can trigger DAIC mode switches - the primary Claude agent
        # cannot trigger transitions independently. This enforces human-in-the-loop control.
        elif is_discussion_mode:
            trigger_phrases = daic_config.get("trigger_phrases", [])
            detected_trigger = detect_trigger_phrases(prompt, trigger_phrases)
            
            if detected_trigger:
                # Create trigger exception flag to allow DAIC state management
                trigger_flag = project_root / '.brainworm' / 'state' / 'trigger_phrase_detected.flag'
                try:
                    trigger_flag.touch()
                    set_daic_mode(project_root, str(DAICMode.IMPLEMENTATION), detected_trigger)
                    # Clean up trigger flag after successful mode change
                    trigger_flag.unlink(missing_ok=True)
                except Exception as e:
                    # Clean up flag on error
                    trigger_flag.unlink(missing_ok=True)
                    if verbose:
                        print(f"Warning: Failed to set DAIC mode: {e}", file=sys.stderr)
                
                context += f"[DAIC: Implementation Mode Activated] Trigger phrase '{detected_trigger}' detected. You may now implement ONLY the immediately discussed steps. DO NOT take **any** actions beyond what was explicitly agreed upon. When you're done, run the command: ./daic\n"
                if verbose:
                    print(f"⚡ Implementation mode activated by: '{detected_trigger}'", file=sys.stderr)
        
        # Protocol detection
        detected_protocols = detect_protocols(prompt)
        for protocol in detected_protocols:
            context += f"If the user is asking to {protocol.replace('-', ' ')}, read and follow sessions/protocols/{protocol}.md protocol.\n"
            if verbose:
                print(f"📋 Protocol detected: {protocol}", file=sys.stderr)
        
        # Task pattern detection
        if daic_config.get("task_detection", {}).get("enabled", True):
            if detect_task_patterns(prompt):
                context += """
[Task Detection Notice]
The message may reference something that could be a task.
If this looks like work that should be tracked separately, consider creating a task for it.
Ask the user if they'd like you to create a task for this work.
"""
                if verbose:
                    print("📝 Task pattern detected", file=sys.stderr)
        
        # Iterloop detection
        if "iterloop" in prompt.lower():
            context += "You have been instructed to iteratively loop over a list. Identify what list the user is referring to, then follow this loop: present one item, wait for the user to respond with questions and discussion points, only continue to the next item when the user explicitly says 'continue' or something similar\n"
        
        # Basic workflow guidance
        intelligence_config = daic_config.get("intelligence", {})
        if intelligence_config.get("smart_recommendations", False):
            if is_discussion_mode and len(prompt.split()) > 50:
                context += "\n[DAIC Intelligence] This appears to be a detailed message. Consider discussing the approach thoroughly before implementation.\n"
        
        # Add ultrathink if not in API mode
        if not config.get("api_mode", False) and not prompt.strip().startswith('/'):
            context = "[[ ultrathink ]]\n" + context
        
        # Debug info for response
        debug_info = {
            "current_daic_mode": current_mode,
            "trigger_phrases": daic_config.get("trigger_phrases", []),
            "daic_enabled": daic_config.get("enabled", True)
        }
        
        # Mode indicator for debugging
        mode_emoji = "💭" if is_discussion_mode else "⚡"
        if verbose:
            print(f"{mode_emoji} Current DAIC mode: {current_mode}", file=sys.stderr)
    
    # Return processing results
    return {
        "context": context,
        "debug_info": debug_info,
        "prompt_info": get_basic_prompt_info(prompt),
        "session_id": session_id
    }


def user_prompt_submit_framework_logic(framework, typed_input):
    """Custom logic for user prompt submit using pure framework approach"""
    project_root = framework.project_root
    
    # Handle case where project_root might be None
    if not project_root:
        framework.set_json_response({"context": ""})
        return
    
    # Load configuration
    from utils.config import load_config
    config = load_config(project_root)
    
    # Check if running in verbose mode
    verbose = '--verbose' in sys.argv
    
    # Convert typed input to dict format for legacy function
    input_data = {
        'session_id': typed_input.session_id,
        'transcript_path': typed_input.transcript_path,
        'cwd': typed_input.cwd,
        'hook_event_name': typed_input.hook_event_name,
        'prompt': typed_input.prompt
    }
    
    # Call custom logic
    result = user_prompt_submit_logic(input_data, project_root, config, verbose)
    
    # Generate typed JSON response for Claude
    debug_info = result["debug_info"] if verbose and result.get("debug_info") else None
    typed_response = UserPromptContextResponse.create_context(
        result["context"], debug_info
    )
    
    # RAW DEBUG LOGGING - Capture what we're sending to Claude
    try:
        debug_log_path = project_root / '.brainworm' / 'debug_user_prompt_context.log'
        with open(debug_log_path, 'a') as f:
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            f.write(f"\n=== {timestamp} ===\n")
            f.write(f"INPUT: {input_data.get('prompt', '')[:100]}...\n")
            f.write(f"RESPONSE JSON: {json.dumps(typed_response.to_dict(), indent=2)}\n")
            f.write(f"RAW CONTEXT: {repr(result['context'])}\n")
            f.flush()
    except Exception as debug_err:
        pass  # Don't let debug logging break the hook
    
    # Set typed JSON response for framework to handle
    framework.set_json_response(typed_response.to_dict())


def main() -> None:
    """Main entry point for user prompt submit hook - Pure Framework Approach"""
    try:
        HookFramework("user_prompt_submit", enable_analytics=True, enable_logging=True) \
            .with_custom_logic(user_prompt_submit_framework_logic) \
            .execute()
        
    except Exception:
        # Emergency fallback - always provide some JSON
        print(json.dumps({"context": ""}))

if __name__ == '__main__':
    main()