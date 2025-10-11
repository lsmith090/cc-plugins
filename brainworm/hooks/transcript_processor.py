#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0.0",
#     "tiktoken>=0.7.0",
# ]
# ///

"""
Transcript Processor Hook - Hooks Framework

Core intelligence engine for context-aware subagent execution.
Processes transcripts for optimal subagent consumption with service awareness.
"""

# Add plugin root to sys.path before any utils imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime, timezone
from collections import deque
from typing import Dict, Any, List, Optional
from utils.hook_framework import HookFramework
from utils.business_controllers import create_subagent_manager

def detect_project_structure(project_root: Path) -> Dict[str, Any]:
    """
    Detect multi-service project structure by analyzing file indicators.
    
    Returns:
        dict: Project structure information including services and type
    """
    services = []
    
    # Find all CLAUDE.md files (excluding node_modules)
    claude_files = []
    for claude_path in project_root.rglob("CLAUDE.md"):
        # Skip node_modules and other common excludes
        if any(exclude in str(claude_path) for exclude in ["node_modules", ".git", "__pycache__", ".venv"]):
            continue
        claude_files.append(claude_path)
    
    # Find service indicators
    service_indicators = {
        "nodejs": list(project_root.glob("*/package.json")) + list(project_root.glob("package.json")),
        "python": list(project_root.rglob("pyproject.toml")) + list(project_root.rglob("setup.py")) + list(project_root.rglob("requirements.txt")),
        "powershell": list(project_root.rglob("requirements.psd1")),
        "go": list(project_root.rglob("go.mod")),
        "rust": list(project_root.rglob("Cargo.toml"))
    }
    
    # Filter out node_modules and deep nested files
    filtered_indicators = {}
    for lang, files in service_indicators.items():
        filtered_files = []
        for file_path in files:
            # Skip node_modules and deep nesting
            if "node_modules" not in str(file_path) and len(file_path.parts) - len(project_root.parts) <= 2:
                filtered_files.append(file_path)
        filtered_indicators[lang] = filtered_files
    
    # Identify services from indicators
    service_paths = set()
    for lang, files in filtered_indicators.items():
        for file_path in files:
            if file_path.parent == project_root:
                # Root level service
                service_path = project_root
                service_name = project_root.name
            else:
                # Sub-directory service
                service_path = file_path.parent
                service_name = service_path.name
            
            service_paths.add((service_path, service_name, lang))
    
    # Convert to service list
    for service_path, service_name, tech_type in service_paths:
        # Find corresponding CLAUDE.md
        service_claude = service_path / "CLAUDE.md"
        
        services.append({
            "name": service_name,
            "path": str(service_path.relative_to(project_root)) if service_path != project_root else ".",
            "absolute_path": str(service_path),
            "type": tech_type,
            "claude_md": str(service_claude) if service_claude.exists() else None,
            "description": f"{tech_type.title()} service"
        })
    
    # Determine project type
    if len(services) > 1:
        project_type = "multi_service"
    elif len(claude_files) > 1:
        project_type = "mono_repo_with_services" 
    elif len(services) == 1 and services[0]["path"] != ".":
        project_type = "mono_repo_with_services"
    else:
        project_type = "single_service"
    
    return {
        "project_type": project_type,
        "project_root": str(project_root),
        "services": services,
        "claude_files": [str(f.relative_to(project_root)) for f in claude_files]
    }


def identify_current_service_context(project_root: Path, task_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Determine which service context we're currently operating in.
    
    Args:
        project_root: Project root directory
        task_data: Task tool data for context analysis
        
    Returns:
        dict: Current service context information
    """
    current_service = None
    project_structure = detect_project_structure(project_root)
    
    # Method 1: Analyze current working directory
    cwd = Path.cwd()
    cwd_service = None
    
    for service in project_structure["services"]:
        service_abs_path = Path(service["absolute_path"])
        try:
            # Check if current directory is within this service
            cwd.relative_to(service_abs_path)
            cwd_service = service
            break
        except ValueError:
            continue
    
    # Method 2: Analyze task parameters (if available)
    task_service = None
    if task_data and "parameters" in task_data:
        # Look for file paths or service names in task description
        task_prompt = task_data["parameters"].get("prompt", "").lower()
        for service in project_structure["services"]:
            if service["name"].lower() in task_prompt or service["path"] in task_prompt:
                task_service = service
                break
    
    # Method 3: Git branch analysis
    branch_service = None
    try:
        import subprocess
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, cwd=project_root)
        if result.returncode == 0:
            branch_name = result.stdout.strip().lower()
            for service in project_structure["services"]:
                if service["name"].lower() in branch_name:
                    branch_service = service
                    break
    except:
        pass
    
    # Priority resolution: current directory > task context > git branch > first service
    current_service = (cwd_service or 
                      task_service or 
                      branch_service or 
                      (project_structure["services"][0] if project_structure["services"] else None))
    
    return {
        "current_service": current_service,
        "detection_method": (
            "current_directory" if cwd_service else
            "task_context" if task_service else
            "git_branch" if branch_service else
            "default_first" if current_service else
            "none"
        ),
        "project_structure": project_structure
    }


def create_service_context_file(service_context: dict, batch_dir: Path):
    """
    Create service context file for subagent consumption.
    
    Args:
        service_context: Service context data
        batch_dir: Directory to save context file
    """
    service_context_file = batch_dir / "service_context.json"
    
    # Prepare context data for subagent
    context_data = {
        "project_type": service_context["project_structure"]["project_type"],
        "project_root": service_context["project_structure"]["project_root"],
        "current_service": service_context["current_service"],
        "all_services": service_context["project_structure"]["services"],
        "claude_files": service_context["project_structure"]["claude_files"],
        "detection_method": service_context["detection_method"],
        "service_relationships": analyze_service_relationships(service_context["project_structure"])
    }
    
    with open(service_context_file, 'w') as f:
        json.dump(context_data, f, indent=2)


def analyze_service_relationships(project_structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze relationships between services based on common patterns.
    
    Args:
        project_structure: Project structure data
        
    Returns:
        dict: Service relationship mapping
    """
    relationships = {}
    services = project_structure["services"]
    
    # Simple heuristic-based relationship detection
    for service in services:
        service_name = service["name"]
        relationships[service_name] = {
            "depends_on": [],
            "communication": [],
            "type": service["type"]
        }
        
        # Common patterns
        if "api" in service_name.lower():
            relationships[service_name]["provides"] = ["API endpoints", "Backend services"]
        elif "client" in service_name.lower():
            relationships[service_name]["consumes"] = ["API services"]
        elif "docs" in service_name.lower():
            relationships[service_name]["documents"] = [s["name"] for s in services if s["name"] != service_name]
        
        # Frontend typically depends on API
        if service["type"] == "nodejs" and any("api" in s["name"].lower() for s in services):
            api_services = [s["name"] for s in services if "api" in s["name"].lower()]
            relationships[service_name]["depends_on"].extend(api_services)
            relationships[service_name]["communication"].append("HTTP API calls")
    
    return relationships

def remove_prework_entries(transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove transcript entries before first implementation tool use.
    Based on cc-sessions logic - finds first Edit/MultiEdit/Write tool.
    """
    start_found = False
    cleaned_transcript = []
    
    for entry in transcript:
        if not start_found:
            message = entry.get('message')
            if message:
                content = message.get('content')
                if isinstance(content, list):
                    for block in content:
                        if (block.get('type') == 'tool_use' and 
                            block.get('name') in ['Edit', 'MultiEdit', 'Write']):
                            start_found = True
                            break
            
            # If we found the start, include this entry and all subsequent ones
            if start_found:
                cleaned_transcript.append(entry)
        else:
            # Already found start, include all subsequent entries
            cleaned_transcript.append(entry)
    
    return cleaned_transcript

def clean_transcript_entries(transcript: List[Dict[str, Any]]) -> deque:
    """
    Clean transcript entries to simple {role, content} format for subagents.
    Enhanced with action summarization to create clean context bundles.
    Based on cc-sessions cleaning logic with context delivery optimization.
    """
    clean_transcript = deque()
    truncation_stats = {
        'total_entries': 0,
        'truncated_entries': 0,
        'tokens_saved': 0
    }
    
    # First pass: Build tool_use_id mapping to fix cross-entry tool tracking
    tool_use_map = {}
    for entry in transcript:
        message = entry.get('message')
        if not message or message.get('role') != 'assistant':
            continue
            
        content = message.get('content', [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'tool_use':
                    tool_use_id = item.get('id')
                    if tool_use_id:
                        tool_use_map[tool_use_id] = item
    
    # Second pass: Process entries with proper tool matching
    for entry in transcript:
        message = entry.get('message')
        
        if not message:
            continue
            
        role = message.get('role')
        content = message.get('content')
        
        # Only include user and assistant messages
        if role not in ['user', 'assistant']:
            continue
        
        truncation_stats['total_entries'] += 1
        
        # Process content for tool result summarization and user prompt flattening
        processed_content = _process_content_for_summarization(content, tool_use_map, role)
        
        if processed_content.get('was_summarized'):
            truncation_stats['truncated_entries'] += 1
            truncation_stats['tokens_saved'] += processed_content['tokens_saved']
        
        clean_entry = {
            'role': role,
            'content': processed_content['content']
        }
        
        # Add summarization metadata if content was summarized
        if processed_content.get('was_summarized'):
            clean_entry['_meta'] = {
                'action_summarization_applied': True,
                'original_tokens': processed_content['original_tokens'],
                'final_tokens': processed_content['final_tokens'],
                'summarized_items': processed_content['summarized_items']
            }
        
        clean_transcript.append(clean_entry)
    
    # Log action summarization statistics if any summarization occurred
    if truncation_stats['truncated_entries'] > 0:
        print(f"🔧 Action summarization applied:")
        print(f"   Entries processed: {truncation_stats['total_entries']}")
        print(f"   Entries with tool results summarized: {truncation_stats['truncated_entries']}")
        print(f"   Tokens saved: {truncation_stats['tokens_saved']:,}")
    
    return clean_transcript

def _process_content_for_summarization(content: Any, tool_use_map: Dict[str, Dict[str, Any]], role: str) -> Dict[str, Any]:
    """Process content to replace tool results with action summaries and flatten user prompts."""
    import re
    
    result = {
        'content': content,
        'was_summarized': False,
        'tokens_saved': 0,
        'original_tokens': 0,
        'final_tokens': 0,
        'summarized_items': 0
    }
    
    # Handle user prompt flattening for better visibility
    if role == 'user' and isinstance(content, list) and len(content) == 1:
        item = content[0]
        if isinstance(item, dict) and item.get('type') == 'text':
            # Flatten simple text prompts to string for better visibility
            text_content = item.get('text', '')
            if text_content and not any(x in str(item) for x in ['tool_use_id', 'tool_result']):
                result['content'] = text_content
                return result
    
    if not isinstance(content, list):
        return result
    
    processed_content = []
    total_tokens_saved = 0
    original_total_tokens = 0
    final_total_tokens = 0
    
    for item in content:
        if not isinstance(item, dict):
            processed_content.append(item)
            continue
        
        # Replace tool results with action summaries
        if item.get('type') == 'tool_result':
            tool_content = item.get('content', '')
            tool_use_id = item.get('tool_use_id')
            
            if isinstance(tool_content, str):
                # Calculate original tokens
                original_tokens = get_token_count(tool_content)
                original_total_tokens += original_tokens
                
                # Find matching tool_use by ID for proper action summary
                matching_tool_use = tool_use_map.get(tool_use_id) if tool_use_id else None
                action_summary = _create_action_summary(matching_tool_use, tool_content)
                
                # Create new item with action summary
                new_item = item.copy()
                new_item['content'] = action_summary
                
                # Add metadata about the replacement
                summary_tokens = get_token_count(action_summary)
                new_item['_action_summary_meta'] = {
                    'original_tokens': original_tokens,
                    'summary_tokens': summary_tokens,
                    'reduction_percent': round((original_tokens - summary_tokens) / original_tokens * 100, 1) if original_tokens > 0 else 0,
                    'reason': 'action_summary_for_context_delivery',
                    'tool_use_id': tool_use_id,
                    'tool_matched': matching_tool_use is not None
                }
                
                processed_content.append(new_item)
                
                # Update statistics
                tokens_saved = original_tokens - summary_tokens
                total_tokens_saved += tokens_saved
                final_total_tokens += summary_tokens
                result['summarized_items'] += 1
                result['was_summarized'] = True
                
            else:
                processed_content.append(item)
        else:
            # Non-tool-result content, include as-is
            processed_content.append(item)
            if isinstance(item, dict) and 'content' in item:
                item_tokens = get_token_count(str(item.get('content', '')))
                original_total_tokens += item_tokens
                final_total_tokens += item_tokens
    
    result['content'] = processed_content
    result['tokens_saved'] = total_tokens_saved
    result['original_tokens'] = original_total_tokens
    result['final_tokens'] = final_total_tokens
    
    return result

def _create_action_summary(tool_use: Dict[str, Any], tool_result_content: str) -> str:
    """Create a simple action summary from tool use and result."""
    
    if not tool_use:
        return "Unknown action"
    
    tool_name = tool_use.get('name', 'Unknown')
    tool_input = tool_use.get('input', {})
    
    # Create action summaries based on tool type
    if tool_name == 'Read':
        file_path = tool_input.get('file_path', 'unknown file')
        return f"Read: {file_path}"
    
    elif tool_name == 'Write':
        file_path = tool_input.get('file_path', 'unknown file')
        return f"Write: {file_path}"
    
    elif tool_name == 'Edit':
        file_path = tool_input.get('file_path', 'unknown file')
        return f"Edit: {file_path}"
    
    elif tool_name == 'MultiEdit':
        file_path = tool_input.get('file_path', 'unknown file')
        return f"MultiEdit: {file_path}"
    
    elif tool_name == 'Bash':
        command = tool_input.get('command', 'unknown command')
        return f"Bash: {command}"
    
    elif tool_name == 'Glob':
        pattern = tool_input.get('pattern', 'unknown pattern')
        return f"Glob: {pattern}"
    
    elif tool_name == 'Grep':
        pattern = tool_input.get('pattern', 'unknown pattern')
        path = tool_input.get('path', '')
        if path:
            return f"Grep: {pattern} in {path}"
        else:
            return f"Grep: {pattern}"
    
    elif tool_name == 'TodoWrite':
        return "TodoWrite: Updated task list"
    
    elif tool_name == 'WebFetch':
        url = tool_input.get('url', 'unknown url')
        return f"WebFetch: {url}"
    
    elif tool_name == 'WebSearch':
        query = tool_input.get('query', 'unknown query')
        return f"WebSearch: {query}"
    
    elif tool_name == 'Task':
        subagent_type = tool_input.get('subagent_type', 'unknown')
        description = tool_input.get('description', '')
        return f"Task: {subagent_type} - {description}"
    
    # For any other tools, create a generic summary
    else:
        # Try to find the most relevant parameter
        key_params = []
        for key in ['file_path', 'path', 'command', 'pattern', 'query', 'url', 'description']:
            if key in tool_input:
                value = str(tool_input[key])
                if len(value) > 100:  # Truncate very long parameters
                    value = value[:97] + "..."
                key_params.append(value)
                break
        
        if key_params:
            return f"{tool_name}: {key_params[0]}"
        else:
            return f"{tool_name}: executed"

def _truncate_tool_result_content(content: str, max_tokens: int = 1500) -> Dict[str, Any]:
    """Intelligently truncate tool result content while preserving essential context."""
    import re
    
    original_tokens = get_token_count(content)
    
    if original_tokens <= max_tokens:
        return {
            'content': content,
            'truncated': False,
            'original_tokens': original_tokens,
            'truncated_tokens': original_tokens,
            'reduction_percent': 0.0
        }
    
    # Detect if this looks like a file read result (has line numbers)
    if re.search(r'^\s*\d+→', content, re.MULTILINE):
        truncated_content = _truncate_file_read_result(content, max_tokens)
    else:
        truncated_content = _truncate_general_content(content, max_tokens)
    
    return {
        'content': truncated_content,
        'truncated': True,
        'original_tokens': original_tokens,
        'truncated_tokens': get_token_count(truncated_content),
        'reduction_percent': round((original_tokens - get_token_count(truncated_content)) / original_tokens * 100, 1)
    }

def _truncate_file_read_result(content: str, max_tokens: int) -> str:
    """Truncate file read results while preserving structure."""
    import re
    
    lines = content.split('\n')
    
    # Find where line-numbered content starts
    content_start_idx = 0
    for i, line in enumerate(lines):
        if re.match(r'^\s*\d+→', line):
            content_start_idx = i
            break
    
    header_lines = lines[:content_start_idx]
    content_lines = lines[content_start_idx:]
    
    if len(content_lines) <= 30:  # Small file, use general truncation
        return _truncate_general_content(content, max_tokens)
    
    # Keep first 15 and last 8 lines of numbered content
    keep_start = 15
    keep_end = 8
    
    start_lines = content_lines[:keep_start]
    end_lines = content_lines[-keep_end:]
    truncated_lines = len(content_lines) - keep_start - keep_end
    
    truncation_notice = [
        "",
        f"... [TRUNCATED {truncated_lines} lines - removed for context delivery optimization] ...",
        ""
    ]
    
    result_lines = header_lines + start_lines + truncation_notice + end_lines
    result = '\n'.join(result_lines)
    
    # If still too large, use aggressive truncation
    if get_token_count(result) > max_tokens:
        return _truncate_general_content(result, max_tokens)
    
    return result

def _truncate_general_content(content: str, max_tokens: int) -> str:
    """General content truncation preserving beginning and end."""
    
    # Estimate words needed (rough: 0.75 tokens per word)
    target_words = int(max_tokens / 0.75 * 0.85)  # 85% of max to be safe
    
    words = content.split()
    
    if len(words) <= target_words:
        return content
    
    # Keep 70% from start, 15% from end
    start_words = int(target_words * 0.7)
    end_words = int(target_words * 0.15)
    
    start_content = ' '.join(words[:start_words])
    end_content = ' '.join(words[-end_words:]) if end_words > 0 else ""
    
    truncated_words = len(words) - start_words - end_words
    
    if end_content:
        result = f"{start_content}\n\n... [TRUNCATED ~{truncated_words} words - removed for context delivery optimization] ...\n\n{end_content}"
    else:
        result = f"{start_content}\n\n... [TRUNCATED ~{truncated_words} words - removed for context delivery optimization] ..."
    
    return result

def extract_subagent_type(transcript: List[Dict[str, Any]], input_data: Dict[str, Any] = None) -> str:
    """
    Extract subagent_type from the Task tool call.
    Based on cc-sessions routing logic.
    """
    # First check if subagent_type is directly in input_data (from hook invocation)
    if input_data and 'tool_input' in input_data:
        tool_input = input_data.get('tool_input', {})
        if 'subagent_type' in tool_input:
            return tool_input['subagent_type']
    
    # Fallback: look in transcript for Task tool call
    if not transcript:
        return 'shared'
    
    # Look at the last message (the Task call)
    task_call = transcript[-1]
    message = task_call.get('message', {})
    content = message.get('content', [])
    
    if isinstance(content, list):
        for block in content:
            if block.get('type') == 'tool_use' and block.get('name') == 'Task':
                task_input = block.get('input', {})
                return task_input.get('subagent_type', 'shared')
    
    return 'shared'

def get_token_count(text: str) -> int:
    """
    Count tokens using tiktoken cl100k_base encoding.
    Matches cc-sessions implementation.
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding('cl100k_base')
        return len(enc.encode(text))
    except ImportError:
        # Fallback to approximate count if tiktoken not available
        return len(text.split()) * 1.3

def chunk_transcript(clean_transcript: deque, max_tokens: int = 18000) -> List[List[Dict]]:
    """
    Chunk transcript into token-aware batches.
    Based on cc-sessions chunking algorithm.
    """
    chunks = []
    current_batch = []
    current_batch_tokens = 0
    
    while clean_transcript:
        entry = clean_transcript.popleft()
        entry_tokens = get_token_count(json.dumps(entry, ensure_ascii=False))
        
        # If adding this entry would exceed limit and we have entries, save current batch
        if current_batch_tokens + entry_tokens > max_tokens and current_batch:
            chunks.append(current_batch)
            current_batch = []
            current_batch_tokens = 0
        
        current_batch.append(entry)
        current_batch_tokens += entry_tokens
    
    # Add final batch if it has content
    if current_batch:
        chunks.append(current_batch)
    
    return chunks

def _clean_metadata_for_subagent(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove internal processing metadata from transcript entry before sending to subagent.
    
    Subagents should only receive clean content without our processing details.
    """
    cleaned_entry = {}
    
    # Copy essential fields only
    for key, value in entry.items():
        if key.startswith('_'):
            # Skip all internal metadata fields like _meta, _action_summary_meta, etc.
            continue
        
        if key == 'content' and isinstance(value, list):
            # Clean content items
            cleaned_content = []
            for item in value:
                if isinstance(item, dict):
                    cleaned_item = {}
                    for item_key, item_value in item.items():
                        if not item_key.startswith('_'):
                            # Skip internal metadata in content items
                            cleaned_item[item_key] = item_value
                    cleaned_content.append(cleaned_item)
                else:
                    cleaned_content.append(item)
            cleaned_entry[key] = cleaned_content
        else:
            cleaned_entry[key] = value
    
    return cleaned_entry

def save_transcript_chunks(chunks: List[List[Dict]], batch_dir: Path) -> None:
    """
    Save transcript chunks as numbered JSON files.
    Based on cc-sessions file naming convention.
    
    Cleans all internal metadata before saving to ensure subagents
    receive only relevant content.
    """
    # Clear existing files in directory
    if batch_dir.exists():
        for item in batch_dir.iterdir():
            if item.is_file() and item.name.startswith('current_transcript_'):
                item.unlink()
    
    # Clean and save chunks
    for file_index, chunk in enumerate(chunks, 1):
        # Clean metadata from each entry in the chunk
        cleaned_chunk = [_clean_metadata_for_subagent(entry) for entry in chunk]
        
        file_path = batch_dir / f"current_transcript_{file_index:03d}.json"
        with file_path.open('w') as f:
            json.dump(cleaned_chunk, f, indent=2, ensure_ascii=False)

def create_subagent_flag(project_root: Path) -> None:
    """
    Create in_subagent_context.flag to signal subagent execution.
    Based on cc-sessions flag coordination.
    """
    flag_path = project_root / '.brainworm' / 'state' / 'in_subagent_context.flag'
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    flag_path.touch()

def log_analytics_event(project_root: Path, event_data: Dict[str, Any]) -> None:
    """
    Log transcript processing event to brainworm analytics with comprehensive metrics.
    """
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))  # Add plugin root for utils access
        from utils.analytics_processor import ClaudeAnalyticsProcessor
        
        # Enhance event data with additional brainworm-specific fields
        enhanced_event = {
            **event_data,
            'hook_name': 'transcript_processor',
            'component': 'brainworm_transcript_processing',
            'correlation_id': event_data.get('correlation_id', 'unknown'),
            'logged_at': datetime.now(timezone.utc).isoformat()
        }
        
        processor = ClaudeAnalyticsProcessor(project_root / '.brainworm')
        success = processor.log_event(enhanced_event)
        
        if not success:
            print("Warning: Analytics event logging returned false", file=sys.stderr)
            
    except Exception as e:
        print(f"Warning: Analytics logging failed: {e}", file=sys.stderr)

def transcript_processor_logic(input_data: Dict[str, Any], project_root: Path, verbose: bool = False) -> Dict[str, Any]:
    """Custom logic for transcript processing"""
    start_time = datetime.now(timezone.utc)
    tool_name = input_data.get("tool_name", "")
    
    # Only process Task tool calls
    if tool_name != "Task":
        if verbose:
            print(f"Skipping non-Task tool: {tool_name}", file=sys.stderr)
        return {"skip": True, "reason": "non_task_tool"}
    
    # RECURSION PREVENTION: Check if we're already in a subagent context
    try:
        subagent_manager = create_subagent_manager(project_root)
        if subagent_manager.is_in_subagent_context():
            if verbose:
                print("⚠️  Recursion prevention: Already in subagent context, skipping transcript processing", file=sys.stderr)
            return {"skip": True, "reason": "recursion_prevention"}
    except Exception:
        # Fallback to direct flag check
        state_dir = project_root / '.brainworm' / 'state'
        subagent_flag = state_dir / 'in_subagent_context.flag'
        if subagent_flag.exists():
            if verbose:
                print("⚠️  Recursion prevention: Already in subagent context, skipping transcript processing", file=sys.stderr)
            return {"skip": True, "reason": "recursion_prevention"}
    
    transcript_path = input_data.get("transcript_path", "")
    if not transcript_path:
        if verbose:
            print("No transcript_path provided", file=sys.stderr)
        return {"skip": True, "reason": "no_transcript_path"}
    
    if verbose:
        print("🔄 Processing transcript for Task tool", file=sys.stderr)
        print(f"Transcript: {transcript_path}", file=sys.stderr)
    
    # Read and parse transcript
    with open(transcript_path, 'r') as f:
        transcript = [json.loads(line) for line in f if line.strip()]
    
    original_entry_count = len(transcript)
    if verbose:
        print(f"Raw transcript entries: {original_entry_count}", file=sys.stderr)
    
    # Remove pre-work entries
    transcript = remove_prework_entries(transcript)
    processed_entry_count = len(transcript)
    if verbose:
        print(f"After pre-work removal: {processed_entry_count}", file=sys.stderr)
    
    # Clean transcript entries
    clean_transcript = clean_transcript_entries(transcript)
    cleaned_entry_count = len(list(clean_transcript))
    
    # Extract subagent type for routing
    subagent_type = extract_subagent_type(list(clean_transcript), input_data)
    if verbose:
        print(f"🤖 Routing to subagent: {subagent_type}", file=sys.stderr)

    # Normalize subagent_type for directory name (strip plugin namespace prefix)
    # e.g., "brainworm:context-gathering" -> "context-gathering"
    subagent_dir_name = subagent_type.split(':', 1)[-1] if ':' in subagent_type else subagent_type

    # Detect service context for location awareness
    service_context = identify_current_service_context(project_root, input_data)

    if verbose:
        current_service = service_context.get("current_service", {})
        service_name = current_service.get("name", "unknown") if current_service else "none"
        detection_method = service_context.get("detection_method", "unknown")
        project_type = service_context.get("project_structure", {}).get("project_type", "unknown")
        print(f"🎯 Service context: {service_name} ({project_type}) via {detection_method}", file=sys.stderr)

    # Create output directory using normalized directory name
    batch_dir = project_root / '.brainworm' / 'state' / subagent_dir_name
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    # Chunk transcript
    chunks = chunk_transcript(clean_transcript)
    chunk_count = len(chunks)
    if verbose:
        print(f"📦 Created {chunk_count} transcript chunks", file=sys.stderr)
    
    # Calculate processing metrics
    processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
    
    # Save chunks
    save_transcript_chunks(chunks, batch_dir)
    
    # Save service context for subagent location awareness
    create_service_context_file(service_context, batch_dir)
    if verbose:
        print("📍 Created service context file for location awareness", file=sys.stderr)
    
    # Create subagent context flag using business controller
    # Use normalized directory name for consistency
    try:
        subagent_manager = create_subagent_manager(project_root)
        subagent_manager.set_subagent_context(subagent_dir_name)
    except Exception:
        # Fallback to direct flag creation
        create_subagent_flag(project_root)
    
    # Return processing results
    return {
        "skip": False,
        "start_time": start_time,
        "subagent_type": subagent_type,
        "service_context": service_context,
        "original_entry_count": original_entry_count,
        "processed_entry_count": processed_entry_count,
        "cleaned_entry_count": cleaned_entry_count,
        "chunk_count": chunk_count,
        "processing_time": processing_time,
        "transcript_path": transcript_path,
        "batch_dir": str(batch_dir)
    }


def transcript_processor_success_handler(result: Dict[str, Any], verbose: bool = False) -> None:
    """Generate success message for transcript processing"""
    if result.get("skip", False):
        return  # No message for skipped processing
    
    processing_time = result.get("processing_time", 0)
    if verbose:
        print(f"✅ Transcript processing complete ({processing_time:.1f}ms)", file=sys.stderr)


def transcript_processor_framework_logic(framework, typed_input):
    """Custom logic for transcript processor using pure framework approach"""
    project_root = framework.project_root
    
    # Handle case where project_root might be None
    if not project_root:
        return  # Exit gracefully if no project root
    
    # Check if running in verbose mode
    verbose = '--verbose' in sys.argv
    
    # Convert typed input to dict format for legacy function
    # For transcript_processor, we need to check raw data as well since it may not have tool_name in BaseHookInput
    input_data = {
        'session_id': typed_input.session_id,
        'transcript_path': typed_input.transcript_path,
        'cwd': typed_input.cwd,
        'hook_event_name': typed_input.hook_event_name,
        'tool_name': getattr(typed_input, 'tool_name', framework.raw_input_data.get('tool_name', '')),
        'tool_input': getattr(typed_input, 'tool_input', framework.raw_input_data.get('tool_input', {}))
    }
    
    # Call custom logic
    result = transcript_processor_logic(input_data, project_root, verbose)
    
    # Call success handler if we have a result
    if result:
        transcript_processor_success_handler(result, verbose)
    
    # Skip processing or handle special transcript processor requirements
    if result and result.get("skip", False):
        return
        
    # Framework handles successful exit automatically


def main() -> None:
    """Main transcript processor entry point - Pure Framework Approach"""
    try:
        HookFramework("transcript_processor", enable_analytics=True, enable_logging=True) \
            .with_custom_logic(transcript_processor_framework_logic) \
            .execute()
            
    except Exception as e:
        # Handle errors gracefully
        print(f"Error in transcript processor: {e}", file=sys.stderr)
        sys.exit(0)  # Non-blocking error


if __name__ == '__main__':
    main()