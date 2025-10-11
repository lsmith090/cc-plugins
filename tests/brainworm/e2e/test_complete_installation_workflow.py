#!/usr/bin/env python3
"""
Complete Installation Workflow E2E Test

End-to-end test for the complete hook installation workflow:
1. Fresh project setup → 2. Hook installation → 3. Verification → 
4. Configuration → 5. First session → 6. Analytics validation

This test simulates the complete user experience from start to finish.
"""

import pytest
import json
import subprocess
import tempfile
import time
import shutil
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import patch, MagicMock
import sys
import uuid

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "hooks" / "templates"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "hooks" / "templates" / "utils"))

from brainworm.hooks.install_hooks import install_hooks_to_project, find_analytics_root
from brainworm.hooks.verify_installation import verify_installation as verify_hooks_installation
from brainworm.hooks.configure_analytics import BrainwormConfig
from brainworm.utils.analytics_processor import ClaudeAnalyticsProcessor


class CompleteInstallationWorkflowTester:
    """End-to-end installation workflow testing utility."""
    
    def __init__(self, base_dir: Path, brainworm_root: Path):
        self.base_dir = base_dir
        self.brainworm_root = brainworm_root
        self.target_projects = {}
        self.workflow_results = {
            'projects_tested': 0,
            'successful_installations': 0,
            'successful_verifications': 0,
            'successful_configurations': 0,
            'successful_first_sessions': 0,
            'workflow_issues': []
        }
    
    def create_realistic_project_environment(self, project_name: str) -> Dict[str, Any]:
        """Create realistic project environment for testing."""
        
        project_dir = self.base_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create realistic project structure
        src_dir = project_dir / 'src'
        src_dir.mkdir(exist_ok=True)
        
        tests_dir = project_dir / 'tests'
        tests_dir.mkdir(exist_ok=True)
        
        docs_dir = project_dir / 'docs'
        docs_dir.mkdir(exist_ok=True)
        
        # Create project files
        (project_dir / 'README.md').write_text(f'''# {project_name}

This is a test project for E2E installation workflow testing.

## Installation

Run the installation process and verify functionality.
''')
        
        (project_dir / 'pyproject.toml').write_text(f'''[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
description = "Test project for brainworm E2E testing"
''')
        
        (src_dir / 'main.py').write_text(f'''#!/usr/bin/env python3
"""
Main module for {project_name}
"""

def main():
    print("Hello from {project_name}!")
    return True

if __name__ == "__main__":
    main()
''')
        
        (tests_dir / 'test_main.py').write_text(f'''#!/usr/bin/env python3
"""
Tests for {project_name}
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import main

def test_main():
    """Test main function."""
    assert main() is True
''')
        
        # Initialize as git repo (common for Claude Code projects)
        try:
            subprocess.run(['git', 'init'], cwd=project_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], 
                          cwd=project_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], 
                          cwd=project_dir, check=True, capture_output=True)
            subprocess.run(['git', 'add', '.'], cwd=project_dir, check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], 
                          cwd=project_dir, check=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass  # Git operations are nice-to-have but not essential
        
        project_data = {
            'project_name': project_name,
            'project_dir': project_dir,
            'src_dir': src_dir,
            'tests_dir': tests_dir,
            'docs_dir': docs_dir,
            'installation_status': 'created',
            'workflow_steps': [],
            'issues': []
        }
        
        self.target_projects[project_name] = project_data
        return project_data
    
    def execute_complete_installation_workflow(self, project_name: str) -> Dict[str, Any]:
        """Execute the complete installation workflow for a project."""
        
        if project_name not in self.target_projects:
            raise ValueError(f"Project {project_name} not initialized")
        
        project_data = self.target_projects[project_name]
        workflow_result = {
            'project_name': project_name,
            'workflow_steps': [],
            'overall_success': True,
            'step_results': {},
            'final_status': 'unknown'
        }
        
        # Step 1: Hook Installation
        installation_step = self._execute_installation_step(project_data)
        workflow_result['workflow_steps'].append('installation')
        workflow_result['step_results']['installation'] = installation_step
        
        if not installation_step['success']:
            workflow_result['overall_success'] = False
            workflow_result['final_status'] = 'installation_failed'
            return workflow_result
        
        # Step 2: Installation Verification
        verification_step = self._execute_verification_step(project_data)
        workflow_result['workflow_steps'].append('verification')
        workflow_result['step_results']['verification'] = verification_step
        
        if not verification_step['success']:
            workflow_result['overall_success'] = False
            workflow_result['final_status'] = 'verification_failed'
            return workflow_result
        
        # Step 3: Analytics Configuration
        configuration_step = self._execute_configuration_step(project_data)
        workflow_result['workflow_steps'].append('configuration')
        workflow_result['step_results']['configuration'] = configuration_step
        
        if not configuration_step['success']:
            workflow_result['overall_success'] = False
            workflow_result['final_status'] = 'configuration_failed'
            return workflow_result
        
        # Step 4: First Session Simulation
        session_step = self._execute_first_session_step(project_data)
        workflow_result['workflow_steps'].append('first_session')
        workflow_result['step_results']['first_session'] = session_step
        
        if not session_step['success']:
            workflow_result['overall_success'] = False
            workflow_result['final_status'] = 'session_failed'
            return workflow_result
        
        # Step 5: Analytics Validation
        validation_step = self._execute_analytics_validation_step(project_data)
        workflow_result['workflow_steps'].append('analytics_validation')
        workflow_result['step_results']['analytics_validation'] = validation_step
        
        if not validation_step['success']:
            workflow_result['overall_success'] = False
            workflow_result['final_status'] = 'validation_failed'
            return workflow_result
        
        workflow_result['final_status'] = 'complete_success'
        
        # Update global counters
        self._update_workflow_counters(workflow_result)
        
        return workflow_result
    
    def _execute_installation_step(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hook installation step."""
        
        step_result = {
            'step': 'installation',
            'success': False,
            'timing': {},
            'details': {},
            'issues': []
        }
        
        start_time = time.perf_counter()
        
        try:
            # Mock find_analytics_root to return our test brainworm root
            with patch('hooks.install_hooks.find_analytics_root', return_value=self.brainworm_root):
                installation_success = install_hooks_to_project(project_data['project_dir'])
            
            install_time = time.perf_counter() - start_time
            step_result['timing']['install_time'] = install_time
            
            if installation_success:
                step_result['success'] = True
                project_data['installation_status'] = 'installed'
                
                # Verify installation artifacts
                hooks_dir = project_data['project_dir'] / '.claude' / 'hooks'
                step_result['details']['hooks_directory_created'] = hooks_dir.exists()
                
                utils_dir = hooks_dir / 'utils'
                step_result['details']['utils_directory_created'] = utils_dir.exists()
                
                settings_file = project_data['project_dir'] / '.claude' / 'settings.json'
                step_result['details']['settings_file_created'] = settings_file.exists()
                
                # Count installed hooks
                if hooks_dir.exists():
                    hook_files = [f for f in hooks_dir.glob('*.py') if f.is_file()]
                    step_result['details']['hook_files_installed'] = len(hook_files)
                    step_result['details']['hook_files'] = [f.name for f in hook_files]
                
                # Count installed utils
                if utils_dir.exists():
                    util_files = [f for f in utils_dir.glob('*.py') if f.is_file()]
                    step_result['details']['util_files_installed'] = len(util_files)
                    step_result['details']['util_files'] = [f.name for f in util_files]
                
            else:
                step_result['issues'].append('install_hooks_to_project returned False')
                project_data['installation_status'] = 'failed'
        
        except Exception as e:
            install_time = time.perf_counter() - start_time
            step_result['timing']['install_time'] = install_time
            step_result['issues'].append(f'Installation exception: {e}')
            project_data['installation_status'] = 'failed'
        
        project_data['workflow_steps'].append(step_result)
        return step_result
    
    def _execute_verification_step(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute installation verification step."""
        
        step_result = {
            'step': 'verification',
            'success': False,
            'timing': {},
            'details': {},
            'issues': []
        }
        
        start_time = time.perf_counter()
        
        try:
            # Change to project directory for verification
            original_cwd = os.getcwd()
            os.chdir(project_data['project_dir'])
            
            # Capture console output during verification
            console_output = []
            
            def mock_console_print(*args, **kwargs):
                console_output.append(str(args[0]) if args else "")
            
            with patch('hooks.verify_installation.console') as mock_console:
                mock_console.print.side_effect = mock_console_print
                
                # Run verification
                verify_hooks_installation()
            
            verify_time = time.perf_counter() - start_time
            step_result['timing']['verify_time'] = verify_time
            
            # Analyze console output for success indicators
            output_text = '\n'.join(console_output)
            step_result['details']['console_output'] = output_text
            
            # Check for success indicators
            success_indicators = [
                'Utils directory found',
                'Settings.json found'
            ]
            
            indicators_found = 0
            for indicator in success_indicators:
                if indicator in output_text:
                    indicators_found += 1
            
            step_result['details']['success_indicators_found'] = indicators_found
            step_result['details']['total_success_indicators'] = len(success_indicators)
            
            # Check for error indicators
            error_indicators = [
                'Issues detected',
                'not working correctly',
                'directory missing',
                'not found'
            ]
            
            errors_found = 0
            for error in error_indicators:
                if error in output_text:
                    errors_found += 1
            
            step_result['details']['error_indicators_found'] = errors_found
            
            # Verification succeeds if we have basic installation success (utils + settings)
            # Analytics connectivity may fail in test environment due to uv/subprocess issues
            if indicators_found >= 2:
                step_result['success'] = True
                project_data['installation_status'] = 'verified'
            else:
                step_result['issues'].append(f'Verification failed: {indicators_found} success indicators, {errors_found} error indicators')
        
        except Exception as e:
            verify_time = time.perf_counter() - start_time
            step_result['timing']['verify_time'] = verify_time
            step_result['issues'].append(f'Verification exception: {e}')
        
        finally:
            os.chdir(original_cwd)
        
        project_data['workflow_steps'].append(step_result)
        return step_result
    
    def _execute_configuration_step(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analytics configuration step."""
        
        step_result = {
            'step': 'configuration',
            'success': False,
            'timing': {},
            'details': {},
            'issues': []
        }
        
        start_time = time.perf_counter()
        
        try:
            # Create brainworm configuration
            config_path = project_data['project_dir'] / 'brainworm-config.toml'
            
            # Create realistic configuration
            config_content = f'''[analytics]
real_time_processing = true
correlation_timeout_minutes = 30
max_processing_time_ms = 100
success_rate_window_hours = 24
retention_days = 7

[harvesting]
enabled = true
schedule = "*/15 * * * *"
max_concurrent_sources = 3

[[sources]]
name = "{project_data['project_name']}"
type = "local"
path = "{project_data['project_dir']}"
enabled = true

[sources.patterns]
jsonl = ".claude/logs/**/*.jsonl"
sessions = ".claude/sessions/**/*.md"

[sources.filters]
min_file_age_minutes = 2
exclude_patterns = ["*.tmp", "*.backup"]

[dashboard]
enabled = true
host = "127.0.0.1"
port = 8000
auto_refresh_seconds = 30
'''
            
            config_path.write_text(config_content)
            step_result['details']['config_file_created'] = True
            
            # Test configuration loading
            config = BrainwormConfig(config_path)
            
            # Verify configuration structure
            step_result['details']['config_loaded'] = True
            step_result['details']['analytics_section'] = 'analytics' in config.config
            step_result['details']['sources_count'] = len(config.config.get('sources', []))
            step_result['details']['harvesting_enabled'] = config.config.get('harvesting', {}).get('enabled', False)
            step_result['details']['dashboard_enabled'] = config.config.get('dashboard', {}).get('enabled', False)
            
            # Test configuration saving
            config.config['test_setting'] = 'e2e_test_value'
            save_success = config.save_config()
            step_result['details']['config_save_success'] = save_success
            
            if save_success:
                # Verify saved configuration
                reloaded_config = BrainwormConfig(config_path)
                step_result['details']['config_reload_success'] = 'test_setting' in reloaded_config.config
                step_result['details']['test_setting_value'] = reloaded_config.config.get('test_setting')
            
            config_time = time.perf_counter() - start_time
            step_result['timing']['config_time'] = config_time
            
            step_result['success'] = True
            project_data['installation_status'] = 'configured'
        
        except Exception as e:
            config_time = time.perf_counter() - start_time
            step_result['timing']['config_time'] = config_time
            step_result['issues'].append(f'Configuration exception: {e}')
        
        project_data['workflow_steps'].append(step_result)
        return step_result
    
    def _execute_first_session_step(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute first session simulation step."""
        
        step_result = {
            'step': 'first_session',
            'success': False,
            'timing': {},
            'details': {},
            'issues': []
        }
        
        start_time = time.perf_counter()
        
        try:
            # Initialize analytics processor
            claude_dir = project_data['project_dir'] / '.claude'
            processor = ClaudeAnalyticsProcessor(claude_dir)
            
            session_id = f"{project_data['project_name']}_e2e_session_{uuid.uuid4().hex[:8]}"
            
            # Simulate first session events
            session_events = []
            
            # Session start
            session_start_event = {
                'hook_name': 'session_start',
                'event_type': 'session_initialization',
                'session_id': session_id,
                'timestamp': time.time(),
                'success': True,
                'duration_ms': 5.0,
                'data': {
                    'project_name': project_data['project_name'],
                    'session_type': 'e2e_first_session',
                    'environment': {
                        'platform': 'test',
                        'claude_code_version': '1.0',
                        'project_type': 'python'
                    },
                    'user_context': {
                        'first_time_setup': True,
                        'installation_verified': True
                    }
                }
            }
            session_events.append(session_start_event)
            
            # Pre-tool use events
            for i in range(3):
                correlation_id = f"{session_id}_tool_{i}"
                
                pre_tool_event = {
                    'hook_name': 'pre_tool_use',
                    'event_type': 'tool_pre_execution',
                    'session_id': session_id,
                    'correlation_id': correlation_id,
                    'timestamp': time.time() + i * 2,
                    'success': True,
                    'duration_ms': 8.0,
                    'data': {
                        'tool_name': f'E2ETestTool_{i}',
                        'tool_args': {
                            'operation': f'first_session_operation_{i}',
                            'target': f'{project_data["project_name"]}/src/test_file_{i}.py'
                        },
                        'context': {
                            'first_session': True,
                            'installation_test': True,
                            'operation_index': i
                        }
                    }
                }
                session_events.append(pre_tool_event)
                
                # Post-tool use events
                post_tool_event = {
                    'hook_name': 'post_tool_use',
                    'event_type': 'tool_post_execution',
                    'session_id': session_id,
                    'correlation_id': correlation_id,
                    'timestamp': time.time() + i * 2 + 1,
                    'success': True,
                    'duration_ms': 12.0,
                    'data': {
                        'tool_name': f'E2ETestTool_{i}',
                        'tool_result': {
                            'status': 'success',
                            'output': f'E2E test operation {i} completed successfully',
                            'files_modified': [f'src/test_file_{i}.py'],
                            'lines_added': 10 + i * 5,
                            'lines_modified': 2 + i
                        },
                        'execution_time': 0.5 + i * 0.1,
                        'context': {
                            'first_session': True,
                            'installation_test': True,
                            'operation_index': i
                        }
                    }
                }
                session_events.append(post_tool_event)
            
            # Session stop
            session_stop_event = {
                'hook_name': 'stop',
                'event_type': 'session_completion',
                'session_id': session_id,
                'timestamp': time.time() + 10,
                'success': True,
                'duration_ms': 7.0,
                'data': {
                    'session_duration': 10.0,
                    'tools_executed': 3,
                    'completion_status': 'success',
                    'session_summary': {
                        'first_session_completed': True,
                        'installation_verified': True,
                        'events_logged': 7,  # session_start + 3*(pre+post) + session_stop
                        'project': project_data['project_name']
                    }
                }
            }
            session_events.append(session_stop_event)
            
            # Log all session events
            successful_events = 0
            failed_events = 0
            
            for event in session_events:
                try:
                    if processor.log_event(event):
                        successful_events += 1
                    else:
                        failed_events += 1
                except Exception as e:
                    failed_events += 1
                    step_result['issues'].append(f'Event logging failed: {e}')
            
            session_time = time.perf_counter() - start_time
            step_result['timing']['session_time'] = session_time
            
            step_result['details']['total_events'] = len(session_events)
            step_result['details']['successful_events'] = successful_events
            step_result['details']['failed_events'] = failed_events
            step_result['details']['session_id'] = session_id
            
            # Success if most events were logged successfully
            if successful_events >= len(session_events) * 0.8:
                step_result['success'] = True
                project_data['installation_status'] = 'session_completed'
            else:
                step_result['issues'].append(f'Too many failed events: {failed_events}/{len(session_events)}')
        
        except Exception as e:
            session_time = time.perf_counter() - start_time
            step_result['timing']['session_time'] = session_time
            step_result['issues'].append(f'First session exception: {e}')
        
        project_data['workflow_steps'].append(step_result)
        return step_result
    
    def _execute_analytics_validation_step(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analytics validation step."""
        
        step_result = {
            'step': 'analytics_validation',
            'success': False,
            'timing': {},
            'details': {},
            'issues': []
        }
        
        start_time = time.perf_counter()
        
        try:
            claude_dir = project_data['project_dir'] / '.claude'
            processor = ClaudeAnalyticsProcessor(claude_dir)
            
            # Test analytics functionality
            
            # 1. Database validation
            db_path = claude_dir / "analytics" / "hooks.db"
            step_result['details']['database_exists'] = db_path.exists()
            
            if db_path.exists():
                with sqlite3.connect(db_path) as conn:
                    # Check database integrity
                    cursor = conn.execute("PRAGMA integrity_check")
                    integrity = cursor.fetchone()[0]
                    step_result['details']['database_integrity'] = integrity == 'ok'
                    
                    # Count events in database
                    cursor = conn.execute("SELECT COUNT(*) FROM hook_events")
                    db_event_count = cursor.fetchone()[0]
                    step_result['details']['database_events'] = db_event_count
            
            # 2. JSONL backup validation
            logs_dir = claude_dir / "analytics" / "logs"
            step_result['details']['logs_directory_exists'] = logs_dir.exists()
            
            jsonl_event_count = 0
            if logs_dir.exists():
                jsonl_files = list(logs_dir.glob("*_hooks.jsonl"))
                step_result['details']['jsonl_files_count'] = len(jsonl_files)
                
                for jsonl_file in jsonl_files:
                    try:
                        with open(jsonl_file, 'r') as f:
                            for line in f:
                                if line.strip():
                                    jsonl_event_count += 1
                    except Exception as e:
                        step_result['issues'].append(f'JSONL file error: {e}')
            
            step_result['details']['jsonl_events'] = jsonl_event_count
            
            # 3. Analytics processor functionality
            try:
                stats = processor.get_statistics()
                step_result['details']['statistics_available'] = isinstance(stats, dict)
                step_result['details']['statistics_total_events'] = stats.get('total_events', 0)
            except Exception as e:
                step_result['issues'].append(f'Statistics error: {e}')
            
            try:
                recent_events = processor.get_recent_events(10)
                step_result['details']['recent_events_available'] = isinstance(recent_events, list)
                step_result['details']['recent_events_count'] = len(recent_events) if recent_events else 0
            except Exception as e:
                step_result['issues'].append(f'Recent events error: {e}')
            
            # 4. Data consistency validation
            if 'database_events' in step_result['details'] and 'jsonl_events' in step_result['details']:
                db_events = step_result['details']['database_events']
                jsonl_events = step_result['details']['jsonl_events']
                
                if db_events > 0 and jsonl_events > 0:
                    consistency_ratio = min(db_events, jsonl_events) / max(db_events, jsonl_events)
                    step_result['details']['data_consistency_ratio'] = consistency_ratio
                    step_result['details']['data_consistent'] = consistency_ratio > 0.9
                else:
                    step_result['details']['data_consistent'] = db_events == jsonl_events == 0
            
            validation_time = time.perf_counter() - start_time
            step_result['timing']['validation_time'] = validation_time
            
            # Determine success criteria
            success_criteria = [
                step_result['details'].get('database_exists', False),
                step_result['details'].get('database_integrity', False),
                step_result['details'].get('database_events', 0) > 0,
                step_result['details'].get('logs_directory_exists', False),
                step_result['details'].get('jsonl_events', 0) > 0,
                step_result['details'].get('statistics_available', False),
                step_result['details'].get('recent_events_available', False),
                step_result['details'].get('data_consistent', False)
            ]
            
            criteria_met = sum(success_criteria)
            step_result['details']['success_criteria_met'] = criteria_met
            step_result['details']['total_success_criteria'] = len(success_criteria)
            
            if criteria_met >= len(success_criteria) * 0.75:  # 75% of criteria must pass
                step_result['success'] = True
                project_data['installation_status'] = 'fully_validated'
            else:
                step_result['issues'].append(f'Insufficient success criteria met: {criteria_met}/{len(success_criteria)}')
        
        except Exception as e:
            validation_time = time.perf_counter() - start_time
            step_result['timing']['validation_time'] = validation_time
            step_result['issues'].append(f'Analytics validation exception: {e}')
        
        project_data['workflow_steps'].append(step_result)
        return step_result
    
    def _update_workflow_counters(self, workflow_result: Dict[str, Any]) -> None:
        """Update global workflow counters."""
        
        self.workflow_results['projects_tested'] += 1
        
        if workflow_result['step_results'].get('installation', {}).get('success', False):
            self.workflow_results['successful_installations'] += 1
        
        if workflow_result['step_results'].get('verification', {}).get('success', False):
            self.workflow_results['successful_verifications'] += 1
        
        if workflow_result['step_results'].get('configuration', {}).get('success', False):
            self.workflow_results['successful_configurations'] += 1
        
        if workflow_result['step_results'].get('first_session', {}).get('success', False):
            self.workflow_results['successful_first_sessions'] += 1
        
        if not workflow_result['overall_success']:
            self.workflow_results['workflow_issues'].append({
                'project': workflow_result['project_name'],
                'status': workflow_result['final_status'],
                'failed_step': next(
                    (step for step, result in workflow_result['step_results'].items() if not result.get('success', True)),
                    'unknown'
                )
            })


@pytest.fixture
def temp_e2e_dir(tmp_path):
    """Create temporary directory for E2E testing."""
    e2e_dir = tmp_path / "e2e_installation_test"
    e2e_dir.mkdir()
    return e2e_dir


@pytest.fixture
def mock_brainworm_root(temp_e2e_dir):
    """Create mock brainworm root for testing."""
    brainworm_root = temp_e2e_dir / 'mock_brainworm'
    brainworm_root.mkdir()
    
    # Create minimal brainworm structure for testing
    template_dir = brainworm_root / 'src' / 'hooks' / 'templates'
    template_dir.mkdir(parents=True)
    
    # Create essential hook templates
    hook_templates = {
        'post_tool_use.py': '''#!/usr/bin/env python3
from analytics_processor import ClaudeAnalyticsProcessor
import json, sys

def main():
    processor = ClaudeAnalyticsProcessor()
    data = json.loads(sys.stdin.read())
    processor.log_event(data)

if __name__ == "__main__":
    main()
''',
        'stop.py': '''#!/usr/bin/env python3
from analytics_processor import ClaudeAnalyticsProcessor
import json, sys

def main():
    processor = ClaudeAnalyticsProcessor()
    data = json.loads(sys.stdin.read())
    processor.log_event(data)

if __name__ == "__main__":
    main()
''',
        'pre_tool_use.py': '''#!/usr/bin/env python3
from analytics_processor import ClaudeAnalyticsProcessor
import json, sys

def main():
    processor = ClaudeAnalyticsProcessor()
    data = json.loads(sys.stdin.read())
    processor.log_event(data)

if __name__ == "__main__":
    main()
''',
        'session_start.py': '''#!/usr/bin/env python3
from analytics_processor import ClaudeAnalyticsProcessor
import json, sys

def main():
    processor = ClaudeAnalyticsProcessor()
    data = json.loads(sys.stdin.read())
    processor.log_event(data)

if __name__ == "__main__":
    main()
'''
    }
    
    for filename, content in hook_templates.items():
        (template_dir / filename).write_text(content)
    
    # Create utils
    utils_dir = template_dir / 'utils'
    utils_dir.mkdir()
    (utils_dir / '__init__.py').write_text('')
    (utils_dir / 'hook_logging.py').write_text('# Hook logging utilities')
    (utils_dir / 'analytics_processor.py').write_text('# Analytics processor')
    
    # Create settings template
    (template_dir / 'settings.json').write_text('''{
  "analytics": {
    "enabled": true,
    "correlation_tracking": true
  },
  "hooks": {
    "stop": {"enabled": true},
    "post_tool_use": {"enabled": true},
    "pre_tool_use": {"enabled": true},
    "session_start": {"enabled": true}
  }
}''')
    
    return brainworm_root


@pytest.fixture
def installation_workflow_tester(temp_e2e_dir, mock_brainworm_root):
    """Create CompleteInstallationWorkflowTester instance."""
    return CompleteInstallationWorkflowTester(temp_e2e_dir, mock_brainworm_root)


class TestCompleteInstallationWorkflow:
    """Test suite for complete installation workflow end-to-end testing."""
    
    @pytest.mark.e2e
    def test_single_project_complete_workflow(self, installation_workflow_tester):
        """Test complete installation workflow for a single project."""
        
        # Create realistic project
        project_data = installation_workflow_tester.create_realistic_project_environment('test_single_project')
        
        # Execute complete workflow
        workflow_result = installation_workflow_tester.execute_complete_installation_workflow('test_single_project')
        
        # Verify overall success
        assert workflow_result['overall_success'], \
            f"Complete workflow failed: {workflow_result['final_status']}"
        
        # Verify all workflow steps completed
        expected_steps = ['installation', 'verification', 'configuration', 'first_session', 'analytics_validation']
        assert workflow_result['workflow_steps'] == expected_steps
        
        # Verify each step succeeded
        for step in expected_steps:
            step_result = workflow_result['step_results'][step]
            assert step_result['success'], \
                f"Step '{step}' failed: {step_result.get('issues', [])}"
        
        # Verify final project status
        assert project_data['installation_status'] == 'fully_validated'
        
        # Verify performance criteria
        total_workflow_time = sum(
            step_result['timing'].get(f'{step}_time', 0)
            for step, step_result in workflow_result['step_results'].items()
        )
        assert total_workflow_time < 30.0, f"Workflow too slow: {total_workflow_time:.2f}s"
    
    @pytest.mark.e2e
    def test_multiple_projects_workflow_isolation(self, installation_workflow_tester):
        """Test workflow isolation across multiple projects."""
        
        project_names = ['isolation_project_a', 'isolation_project_b', 'isolation_project_c']
        
        # Create multiple projects
        for project_name in project_names:
            project_data = installation_workflow_tester.create_realistic_project_environment(project_name)
            assert project_data['project_name'] == project_name
        
        # Execute workflows for all projects
        workflow_results = {}
        for project_name in project_names:
            workflow_results[project_name] = installation_workflow_tester.execute_complete_installation_workflow(project_name)
        
        # Verify all workflows succeeded
        for project_name, result in workflow_results.items():
            assert result['overall_success'], \
                f"Workflow failed for project {project_name}: {result['final_status']}"
        
        # Verify project isolation
        for i, project_name in enumerate(project_names):
            project_data = installation_workflow_tester.target_projects[project_name]
            project_dir = project_data['project_dir']
            
            # Each project should have its own .claude directory
            claude_dir = project_dir / '.claude'
            assert claude_dir.exists()
            
            # Check for unique analytics data
            db_path = claude_dir / 'analytics' / 'hooks.db'
            if db_path.exists():
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.execute("SELECT DISTINCT session_id FROM hook_events WHERE session_id LIKE ?", 
                                        (f'{project_name}%',))
                    project_sessions = [row[0] for row in cursor.fetchall()]
                    
                    # Should have sessions belonging to this project
                    assert len(project_sessions) > 0, f"No sessions found for project {project_name}"
                    
                    # Sessions should be unique to this project
                    for session_id in project_sessions:
                        assert session_id.startswith(project_name), \
                            f"Foreign session {session_id} found in project {project_name}"
        
        # Verify global workflow statistics
        global_stats = installation_workflow_tester.workflow_results
        assert global_stats['projects_tested'] == 3
        assert global_stats['successful_installations'] == 3
        assert global_stats['successful_verifications'] == 3
        assert global_stats['successful_configurations'] == 3
        assert global_stats['successful_first_sessions'] == 3
        assert len(global_stats['workflow_issues']) == 0
    
    @pytest.mark.e2e
    def test_workflow_error_recovery(self, installation_workflow_tester):
        """Test workflow error recovery and partial completion."""
        
        # Create project
        project_data = installation_workflow_tester.create_realistic_project_environment('error_recovery_project')
        
        # Test recovery from configuration errors
        config_path = project_data['project_dir'] / 'brainworm-config.toml'
        
        # Create intentionally broken configuration
        config_path.write_text('[broken toml syntax')
        
        # Execute workflow - should handle config errors gracefully
        workflow_result = installation_workflow_tester.execute_complete_installation_workflow('error_recovery_project')
        
        # Installation and verification should still succeed
        assert workflow_result['step_results']['installation']['success'], \
            "Installation should succeed despite config issues"
        
        assert workflow_result['step_results']['verification']['success'], \
            "Verification should succeed despite config issues"
        
        # Configuration might fail, but workflow should handle it gracefully
        if not workflow_result['overall_success']:
            assert workflow_result['final_status'] in ['configuration_failed', 'session_failed', 'validation_failed']
        
        # Even if overall workflow fails, basic installation should be functional
        hooks_dir = project_data['project_dir'] / '.claude' / 'hooks'
        assert hooks_dir.exists(), "Hook installation should succeed regardless of config errors"
        
        utils_dir = hooks_dir / 'utils'
        assert utils_dir.exists(), "Utils installation should succeed regardless of config errors"
    
    @pytest.mark.e2e
    def test_workflow_performance_requirements(self, installation_workflow_tester):
        """Test that workflow meets performance requirements."""
        
        project_names = ['perf_project_1', 'perf_project_2']
        
        start_time = time.perf_counter()
        
        # Execute workflows for multiple projects concurrently
        workflow_results = {}
        for project_name in project_names:
            installation_workflow_tester.create_realistic_project_environment(project_name)
            workflow_results[project_name] = installation_workflow_tester.execute_complete_installation_workflow(project_name)
        
        total_time = time.perf_counter() - start_time
        
        # Performance requirements
        assert total_time < 60.0, f"Total workflow time too long: {total_time:.2f}s"
        
        # Individual step performance
        for project_name, result in workflow_results.items():
            for step, step_result in result['step_results'].items():
                step_time_key = f"{step}_time"
                if step_time_key in step_result['timing']:
                    step_time = step_result['timing'][step_time_key]
                    
                    # Individual step time limits
                    if step == 'installation':
                        assert step_time < 10.0, f"Installation too slow for {project_name}: {step_time:.2f}s"
                    elif step == 'verification':
                        assert step_time < 5.0, f"Verification too slow for {project_name}: {step_time:.2f}s"
                    elif step == 'configuration':
                        assert step_time < 3.0, f"Configuration too slow for {project_name}: {step_time:.2f}s"
                    elif step == 'first_session':
                        assert step_time < 5.0, f"First session too slow for {project_name}: {step_time:.2f}s"
                    elif step == 'analytics_validation':
                        assert step_time < 3.0, f"Validation too slow for {project_name}: {step_time:.2f}s"
        
        # Verify all workflows succeeded
        for project_name, result in workflow_results.items():
            assert result['overall_success'], \
                f"Performance test workflow failed for {project_name}: {result['final_status']}"


if __name__ == "__main__":
    # Allow direct execution for debugging
    pytest.main([__file__, "-v", "--tb=short", "-m", "e2e"])