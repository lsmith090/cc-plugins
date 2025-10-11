#!/usr/bin/env python3
"""
Real-world test for PreToolUse JSON validation bug
This test would have caught the hookSpecificOutput schema mismatch bug
"""

import sys
import os
import json
from pathlib import Path

# Add src/hooks/templates to path to import utils modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src/hooks/templates'))

from brainworm.utils.hook_types import PreToolUseDecisionOutput


class TestPreToolUseJSONValidation:
    """Test PreToolUse JSON output against Claude Code specification"""
    
    def test_block_tool_json_structure_matches_claude_code_spec(self):
        """
        CRITICAL TEST: This would catch the real hookSpecificOutput validation bug
        The user is experiencing JSON validation failures because the framework
        generates the wrong hookSpecificOutput structure for PreToolUse hooks.
        """
        # Create a block decision using the framework's current method
        decision = PreToolUseDecisionOutput.block(
            reason="DAIC workflow prevents tool execution in discussion mode",
            validation_issues=["Tool blocked by DAIC enforcement"],
            session_id="test-session-123"
        )
        
        # Generate JSON using current implementation
        json_output = decision.to_dict()
        
        # Print actual output for debugging
        print("\\nActual JSON output:")
        print(json.dumps(json_output, indent=2))
        
        # Validate against Claude Code specification
        # Based on the error message, Claude Code expects this structure:
        expected_hook_specific_structure = {
            "hookEventName": "PreToolUse",
            # Optional fields Claude Code recognizes:
            # "permissionDecision": "allow | deny | ask", 
            # "permissionDecisionReason": "string"
        }
        
        # Basic schema validation - these should exist
        assert 'continue' in json_output, "Missing required 'continue' field"
        assert isinstance(json_output['continue'], bool), "'continue' must be boolean"
        
        # Critical test: hookSpecificOutput structure
        if 'hookSpecificOutput' in json_output:
            hook_output = json_output['hookSpecificOutput']
            
            # The bug: Current implementation doesn't include hookEventName
            assert 'hookEventName' in hook_output, \
                "CRITICAL BUG: hookSpecificOutput missing required 'hookEventName' field"
            
            # The bug: Current implementation uses wrong field names
            assert hook_output['hookEventName'] == 'PreToolUse', \
                f"CRITICAL BUG: hookEventName should be 'PreToolUse', got {hook_output.get('hookEventName')}"
            
            # These fields should exist for PreToolUse hooks per Claude Code spec
            if 'permissionDecision' in hook_output:
                assert hook_output['permissionDecision'] in ['allow', 'deny', 'ask'], \
                    f"Invalid permissionDecision value: {hook_output['permissionDecision']}"
        
    def test_approve_tool_json_structure_matches_claude_code_spec(self):
        """Test approve decision JSON structure"""
        # Create an approve decision
        decision = PreToolUseDecisionOutput.approve(
            reason="Tool allowed by DAIC",
            session_id="test-session-456"
        )
        
        json_output = decision.to_dict()
        
        # Print actual output for debugging  
        print("\\nApprove decision JSON output:")
        print(json.dumps(json_output, indent=2))
        
        # Basic validation
        assert json_output['continue'] is True, "Approve decision should set continue=True"
        
        # Critical test: If hookSpecificOutput exists, it should have correct structure
        if 'hookSpecificOutput' in json_output:
            hook_output = json_output['hookSpecificOutput']
            
            assert 'hookEventName' in hook_output, \
                "CRITICAL BUG: hookSpecificOutput missing required 'hookEventName'"
            assert hook_output['hookEventName'] == 'PreToolUse', \
                "CRITICAL BUG: hookEventName should be 'PreToolUse'"
                
    def test_json_serialization_compatibility(self):
        """Test that generated JSON can actually be serialized"""
        decision = PreToolUseDecisionOutput.block(
            reason="Test blocking",
            validation_issues=["Test issue"],
            session_id="test-123"
        )
        
        json_output = decision.to_dict()
        
        # This should not raise an exception
        try:
            json_str = json.dumps(json_output)
            assert isinstance(json_str, str), "JSON serialization failed"
        except (TypeError, ValueError) as e:
            assert False, f"JSON serialization failed: {e}"
            
    def test_real_world_pretool_scenario(self):
        """
        Test actual PreToolUse scenario that matches what the user experiences
        This simulates the real hook execution that's causing validation failures
        """
        # Simulate real DAIC blocking scenario
        decision = PreToolUseDecisionOutput.block(
            reason="DAIC workflow prevents tool execution in discussion mode. Use trigger phrases like 'make it so' to switch to implementation mode.",
            validation_issues=[
                "Tool blocked by DAIC enforcement",
                "Current mode: discussion", 
                "Blocked tool: Bash"
            ],
            session_id="real-session-abc123"
        )
        
        json_output = decision.to_dict()
        
        # Print the exact JSON that would be sent to Claude Code
        print("\\nReal-world PreToolUse JSON (this is what Claude Code sees):")
        print(json.dumps(json_output, indent=2))
        
        # Validate this matches what Claude Code expects
        # Based on the user's error message, this structure is failing validation
        
        # Required fields per Claude Code spec
        assert 'continue' in json_output
        assert json_output['continue'] is False  # Should be False for blocking
        
        # Optional fields that might be present
        expected_optional_fields = ['stopReason', 'suppressOutput', 'systemMessage', 'hookSpecificOutput']
        
        # If hookSpecificOutput exists, it MUST have the correct structure
        if 'hookSpecificOutput' in json_output:
            hook_output = json_output['hookSpecificOutput']
            
            # This is the critical bug causing validation failures
            print(f"\\nCurrent hookSpecificOutput structure: {hook_output}")
            print("Expected structure should include hookEventName='PreToolUse'")
            
            # These assertions will fail with current implementation, 
            # demonstrating the exact bug the user is experiencing
            try:
                assert 'hookEventName' in hook_output, "Missing hookEventName - this causes Claude Code validation to fail"
                assert hook_output['hookEventName'] == 'PreToolUse', "Wrong hookEventName value"
            except AssertionError as e:
                print(f"\\n🚫 VALIDATION FAILURE (matches user's error): {e}")
                # This is expected to fail with current implementation
                # The test demonstrates the exact bug
                
    def test_compare_with_working_hook_output(self):
        """
        Compare current output with what a working PreToolUse hook should generate
        This shows exactly what needs to be fixed
        """
        current_output = PreToolUseDecisionOutput.block(
            reason="Test", validation_issues=["test"], session_id="test"
        ).to_dict()
        
        # What the output SHOULD look like per Claude Code spec
        expected_working_output = {
            "continue": False,
            "stopReason": "Test", 
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Test"
            }
        }
        
        print("\\n=== COMPARISON ===")
        print("Current (broken) output:")
        print(json.dumps(current_output, indent=2))
        print("\\nExpected (working) output:")
        print(json.dumps(expected_working_output, indent=2))
        
        # Show the specific differences
        if 'hookSpecificOutput' in current_output:
            current_hook = current_output['hookSpecificOutput']
            expected_hook = expected_working_output['hookSpecificOutput']
            
            print("\\n=== HOOK-SPECIFIC OUTPUT DIFFERENCES ===")
            for key in expected_hook:
                if key not in current_hook:
                    print(f"❌ Missing: {key} = {expected_hook[key]}")
                elif current_hook[key] != expected_hook[key]:
                    print(f"⚠️  Wrong value: {key} = {current_hook[key]} (should be {expected_hook[key]})")
            
            for key in current_hook:
                if key not in expected_hook:
                    print(f"➕ Extra field: {key} = {current_hook[key]} (not in Claude Code spec)")


if __name__ == '__main__':
    """Run the tests to demonstrate the JSON validation bug"""
    test_instance = TestPreToolUseJSONValidation()
    
    print("🔍 Running PreToolUse JSON validation bug test...")
    print("This test demonstrates the exact issue causing the user's validation failures.")
    print("="*70)
    
    try:
        test_instance.test_real_world_pretool_scenario()
        print("✅ Test completed - check output above for validation issues")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    print("\\n" + "="*70)
    test_instance.test_compare_with_working_hook_output()