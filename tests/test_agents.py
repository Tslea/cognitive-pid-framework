"""
Tests for agent modules
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from src.agent_keeper import call_keeper, _parse_keeper_output, validate_task
from src.agent_developer import call_developer, _parse_developer_output, estimate_patch_impact
from src.agent_qa import call_qa, _parse_qa_output


@pytest.fixture
def mock_keeper_params():
    """Mock parameters for Keeper agent."""
    return {
        'model_name': 'gpt-3.5-turbo',
        'temperature': 0.7,
        'max_tokens': 2000,
        'provider': 'openai',
        'language': 'en'
    }


@pytest.fixture
def mock_developer_params():
    """Mock parameters for Developer agent."""
    return {
        'model_name': 'gpt-3.5-turbo',
        'temperature': 0.5,
        'max_tokens': 3000,
        'provider': 'openai',
        'language': 'en'
    }


@pytest.fixture
def mock_qa_params():
    """Mock parameters for QA agent."""
    return {
        'model_name': 'gpt-3.5-turbo',
        'temperature': 0.3,
        'max_tokens': 2500,
        'provider': 'openai',
        'language': 'en'
    }


@pytest.fixture
def sample_task():
    """Sample task dictionary."""
    return {
        'id': 'TASK-001',
        'title': 'Create user authentication',
        'description': 'Implement user login and registration',
        'priority': 'high',
        'estimated_complexity': 'medium',
        'acceptance_criteria': [
            'Users can register with email and password',
            'Users can log in',
            'Passwords are hashed'
        ]
    }


# Keeper Agent Tests

def test_parse_keeper_output_valid():
    """Test parsing valid Keeper output."""
    response = json.dumps({
        'tasks': [
            {
                'id': 'TASK-001',
                'title': 'Setup project structure',
                'description': 'Create initial folders and files',
                'priority': 'high',
                'estimated_complexity': 'low',
                'dependencies': [],
                'acceptance_criteria': ['Folders created', 'README exists']
            }
        ],
        'reasoning': 'Start with basic structure'
    })
    
    output = _parse_keeper_output(response)
    
    assert 'tasks' in output
    assert len(output['tasks']) == 1
    assert output['tasks'][0]['id'] == 'TASK-001'
    assert output['reasoning'] == 'Start with basic structure'


def test_parse_keeper_output_with_markdown():
    """Test parsing Keeper output wrapped in markdown."""
    response = f"""```json
{{
  "tasks": [
    {{
      "id": "TASK-001",
      "title": "Test task",
      "description": "Test",
      "priority": "medium"
    }}
  ],
  "reasoning": "Testing"
}}
```"""
    
    output = _parse_keeper_output(response)
    
    assert 'tasks' in output
    assert len(output['tasks']) == 1


def test_parse_keeper_output_invalid_json():
    """Test parsing invalid JSON."""
    response = "This is not JSON"
    
    output = _parse_keeper_output(response)
    
    # Should return fallback structure
    assert output['tasks'] == []
    assert 'error' in output['reasoning'].lower() or 'parse' in output['reasoning'].lower()


def test_parse_keeper_output_missing_fields():
    """Test parsing output with missing fields."""
    response = json.dumps({
        'tasks': [
            {
                'id': 'TASK-001'
                # Missing other required fields
            }
        ]
    })
    
    output = _parse_keeper_output(response)
    
    # Should fill in defaults
    assert output['tasks'][0]['title'] == 'Untitled task'
    assert output['tasks'][0]['priority'] == 'medium'


def test_validate_task():
    """Test task validation."""
    valid_task = {
        'id': 'TASK-001',
        'title': 'Test',
        'description': 'Test task'
    }
    assert validate_task(valid_task)
    
    invalid_task = {
        'id': 'TASK-001'
        # Missing title and description
    }
    assert not validate_task(invalid_task)


@patch('src.agent_keeper.call_llm')
def test_call_keeper_success(mock_llm, mock_keeper_params):
    """Test successful Keeper agent call."""
    mock_response = json.dumps({
        'tasks': [
            {
                'id': 'TASK-001',
                'title': 'Create API',
                'description': 'Build REST API',
                'priority': 'high',
                'estimated_complexity': 'medium',
                'dependencies': [],
                'acceptance_criteria': ['API endpoints work']
            }
        ],
        'reasoning': 'API is core functionality'
    })
    
    mock_llm.return_value = mock_response
    
    state = {
        'setpoint': 'Build a web application',
        'iteration': 1,
        'completed_tasks': [],
        'codebase_path': '/tmp/test'
    }
    
    output = call_keeper(state, mock_keeper_params)
    
    assert len(output['tasks']) == 1
    assert output['tasks'][0]['id'] == 'TASK-001'
    mock_llm.assert_called_once()


@patch('src.agent_keeper.call_llm')
def test_call_keeper_error_handling(mock_llm, mock_keeper_params):
    """Test Keeper error handling."""
    mock_llm.side_effect = Exception("API error")
    
    state = {
        'setpoint': 'Build app',
        'iteration': 1,
        'completed_tasks': [],
        'codebase_path': '/tmp/test'
    }
    
    output = call_keeper(state, mock_keeper_params)
    
    # Should return empty tasks on error
    assert output['tasks'] == []
    assert 'error' in output['reasoning'].lower()


# Developer Agent Tests

def test_parse_developer_output_valid():
    """Test parsing valid Developer output."""
    response = json.dumps({
        'patch': 'diff --git a/file.py ...',
        'files_modified': ['src/auth.py'],
        'files_created': ['src/models/user.py'],
        'risks': [
            {
                'severity': 'medium',
                'description': 'Password hashing needs review',
                'mitigation': 'Use bcrypt library'
            }
        ],
        'implementation_notes': 'Used JWT for tokens',
        'testing_suggestions': ['Test password hashing', 'Test JWT generation']
    })
    
    output = _parse_developer_output(response)
    
    assert 'patch' in output
    assert len(output['files_modified']) == 1
    assert len(output['risks']) == 1
    assert output['risks'][0]['severity'] == 'medium'


def test_parse_developer_output_missing_fields():
    """Test parsing Developer output with missing fields."""
    response = json.dumps({
        'patch': 'some diff'
        # Missing other fields
    })
    
    output = _parse_developer_output(response)
    
    # Should fill defaults
    assert output['files_modified'] == []
    assert output['files_created'] == []
    assert output['risks'] == []


@patch('src.agent_developer.call_llm')
def test_call_developer_success(mock_llm, sample_task, mock_developer_params):
    """Test successful Developer agent call."""
    mock_response = json.dumps({
        'patch': 'diff --git a/auth.py ...',
        'files_modified': ['auth.py'],
        'files_created': [],
        'risks': [],
        'implementation_notes': 'Implemented basic auth',
        'testing_suggestions': ['Test login flow']
    })
    
    mock_llm.return_value = mock_response
    
    output = call_developer(sample_task, '/tmp/test', mock_developer_params)
    
    assert 'patch' in output
    assert len(output['files_modified']) == 1
    mock_llm.assert_called_once()


def test_estimate_patch_impact():
    """Test patch impact estimation."""
    patch = """diff --git a/file.py b/file.py
index 1234567..abcdefg 100644
--- a/file.py
+++ b/file.py
@@ -1,5 +1,7 @@
 def hello():
-    print("Hello")
+    print("Hello World")
+    print("New line")
+def goodbye():
+    print("Goodbye")
"""
    
    impact = estimate_patch_impact(patch)
    
    assert impact['additions'] > 0
    assert impact['deletions'] > 0
    assert impact['total_changes'] == impact['additions'] + impact['deletions']


# QA Agent Tests

def test_parse_qa_output_valid():
    """Test parsing valid QA output."""
    response = json.dumps({
        'verdict': 'pass',
        'test_cases': [
            {
                'name': 'test_login',
                'type': 'unit',
                'description': 'Test user login',
                'code': 'def test_login(): ...'
            }
        ],
        'issues': [],
        'test_results': {'total': 10, 'passed': 10, 'failed': 0, 'skipped': 0},
        'quality_score': 0.9,
        'feedback': 'Code looks good'
    })
    
    output = _parse_qa_output(response)
    
    assert output['verdict'] == 'pass'
    assert len(output['test_cases']) == 1
    assert output['quality_score'] == 0.9


def test_parse_qa_output_with_issues():
    """Test parsing QA output with issues."""
    response = json.dumps({
        'verdict': 'fail',
        'test_cases': [],
        'issues': [
            {
                'severity': 'critical',
                'type': 'bug',
                'description': 'Null pointer exception',
                'location': 'file.py:42',
                'suggestion': 'Add null check'
            }
        ],
        'test_results': {'total': 10, 'passed': 5, 'failed': 5, 'skipped': 0},
        'quality_score': 0.3,
        'feedback': 'Critical bugs found'
    })
    
    output = _parse_qa_output(response)
    
    assert output['verdict'] == 'fail'
    assert len(output['issues']) == 1
    assert output['issues'][0]['severity'] == 'critical'


def test_parse_qa_output_invalid_verdict():
    """Test QA output with invalid verdict."""
    response = json.dumps({
        'verdict': 'maybe',  # Invalid
        'test_cases': [],
        'issues': []
    })
    
    output = _parse_qa_output(response)
    
    # Should default to 'fail'
    assert output['verdict'] == 'fail'


@patch('src.agent_qa.call_llm')
def test_call_qa_success(mock_llm, mock_qa_params):
    """Test successful QA agent call."""
    mock_response = json.dumps({
        'verdict': 'pass',
        'test_cases': [],
        'issues': [],
        'test_results': {'total': 5, 'passed': 5, 'failed': 0, 'skipped': 0},
        'quality_score': 0.95,
        'feedback': 'Excellent code quality'
    })
    
    mock_llm.return_value = mock_response
    
    output = call_qa('diff --git ...', '/tmp/test', mock_qa_params)
    
    assert output['verdict'] == 'pass'
    assert output['quality_score'] == 0.95
    mock_llm.assert_called_once()


def test_qa_quality_score_estimation():
    """Test quality score estimation from issues."""
    # Critical issue → score 0.0
    response_critical = json.dumps({
        'verdict': 'fail',
        'issues': [{'severity': 'critical', 'description': 'Bad bug', 'type': 'bug', 'location': 'x', 'suggestion': 'fix'}]
    })
    output = _parse_qa_output(response_critical)
    assert output['quality_score'] == 0.0
    
    # Multiple high issues → lower score
    response_high = json.dumps({
        'verdict': 'fail',
        'issues': [
            {'severity': 'high', 'description': 'Issue 1', 'type': 'bug', 'location': 'x', 'suggestion': 'fix'},
            {'severity': 'high', 'description': 'Issue 2', 'type': 'bug', 'location': 'y', 'suggestion': 'fix'},
            {'severity': 'high', 'description': 'Issue 3', 'type': 'bug', 'location': 'z', 'suggestion': 'fix'}
        ]
    })
    output = _parse_qa_output(response_high)
    assert output['quality_score'] == 0.4


# Integration Tests

@patch('src.agent_keeper.call_llm')
@patch('src.agent_developer.call_llm')
@patch('src.agent_qa.call_llm')
def test_agent_pipeline(mock_qa_llm, mock_dev_llm, mock_keeper_llm):
    """Test full agent pipeline."""
    # Mock Keeper response
    keeper_response = json.dumps({
        'tasks': [{'id': 'TASK-001', 'title': 'Test', 'description': 'Test task', 
                   'priority': 'high', 'estimated_complexity': 'low',
                   'dependencies': [], 'acceptance_criteria': []}],
        'reasoning': 'Test'
    })
    mock_keeper_llm.return_value = keeper_response
    
    # Mock Developer response
    dev_response = json.dumps({
        'patch': 'diff',
        'files_modified': ['test.py'],
        'files_created': [],
        'risks': [],
        'implementation_notes': 'Done',
        'testing_suggestions': []
    })
    mock_dev_llm.return_value = dev_response
    
    # Mock QA response
    qa_response = json.dumps({
        'verdict': 'pass',
        'test_cases': [],
        'issues': [],
        'test_results': {'total': 1, 'passed': 1, 'failed': 0, 'skipped': 0},
        'quality_score': 1.0,
        'feedback': 'Perfect'
    })
    mock_qa_llm.return_value = qa_response
    
    # Call agents in sequence
    keeper_out = call_keeper(
        {'setpoint': 'test', 'iteration': 1, 'completed_tasks': [], 'codebase_path': '/tmp'},
        {'model_name': 'gpt-3.5-turbo', 'temperature': 0.7, 'max_tokens': 2000, 'provider': 'openai', 'language': 'en'}
    )
    
    assert len(keeper_out['tasks']) == 1
    
    task = keeper_out['tasks'][0]
    dev_out = call_developer(
        task,
        '/tmp',
        {'model_name': 'gpt-3.5-turbo', 'temperature': 0.5, 'max_tokens': 3000, 'provider': 'openai', 'language': 'en'}
    )
    
    assert 'patch' in dev_out
    
    qa_out = call_qa(
        dev_out['patch'],
        '/tmp',
        {'model_name': 'gpt-3.5-turbo', 'temperature': 0.3, 'max_tokens': 2500, 'provider': 'openai', 'language': 'en'}
    )
    
    assert qa_out['verdict'] == 'pass'
