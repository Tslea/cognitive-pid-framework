"""
Tests for measurement system
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.measure import (
    compute_pv,
    compute_similarity,
    compute_test_pass_rate,
    compute_lint_score,
    compute_req_coverage,
    initialize_metrics,
    _extract_keywords
)


@pytest.fixture
def mock_config():
    """Mock configuration."""
    return {
        'metrics': {
            'weights': {
                'similarity': 0.4,
                'test_pass_rate': 0.3,
                'lint_score': 0.2,
                'req_coverage': 0.1
            }
        }
    }


def test_compute_test_pass_rate():
    """Test test pass rate computation."""
    # All tests pass
    result = compute_test_pass_rate({'total': 10, 'passed': 10, 'failed': 0, 'skipped': 0})
    assert result == 1.0
    
    # Half pass
    result = compute_test_pass_rate({'total': 10, 'passed': 5, 'failed': 5, 'skipped': 0})
    assert result == 0.5
    
    # No tests
    result = compute_test_pass_rate(None)
    assert result == 0.5
    
    # Empty results
    result = compute_test_pass_rate({'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0})
    assert result == 0.5


def test_compute_pv(mock_config):
    """Test process variable computation."""
    with patch('src.measure.compute_similarity', return_value=0.8), \
         patch('src.measure.compute_test_pass_rate', return_value=0.9), \
         patch('src.measure.compute_lint_score', return_value=0.7), \
         patch('src.measure.compute_req_coverage', return_value=0.6):
        
        pv = compute_pv(
            setpoint="Test project",
            codebase_path="/fake/path",
            test_results={'total': 10, 'passed': 9},
            config=mock_config
        )
        
        # Expected: 0.4*0.8 + 0.3*0.9 + 0.2*0.7 + 0.1*0.6
        expected = 0.4 * 0.8 + 0.3 * 0.9 + 0.2 * 0.7 + 0.1 * 0.6
        assert abs(pv - expected) < 0.001


def test_extract_keywords():
    """Test keyword extraction."""
    text = "Create a simple calculator application with basic arithmetic operations"
    keywords = _extract_keywords(text)
    
    assert 'simple' in keywords
    assert 'calculator' in keywords
    assert 'application' in keywords
    
    # Short words should be excluded
    assert 'a' not in keywords


def test_compute_similarity_no_embedding():
    """Test similarity when embeddings are disabled."""
    with patch('src.measure._metrics_initialized', False):
        similarity = compute_similarity("test", "/fake/path")
        assert similarity == 0.5  # Default value


@patch('src.measure._sentence_transformer')
@patch('src.measure._metrics_initialized', True)
@patch('src.measure._extract_codebase_text')
def test_compute_similarity_with_embedding(mock_extract, mock_transformer):
    """Test similarity with mock embeddings."""
    # Mock embeddings
    setpoint_emb = np.array([1.0, 0.0, 0.0])
    codebase_emb = np.array([0.9, 0.1, 0.0])
    
    mock_transformer.encode.side_effect = [setpoint_emb, codebase_emb]
    mock_extract.return_value = "Some code content"
    
    similarity = compute_similarity("Build a web app", "/fake/path")
    
    # Should be between 0 and 1
    assert 0.0 <= similarity <= 1.0


def test_compute_lint_score_empty_codebase():
    """Test lint score for empty/non-existent codebase."""
    result = compute_lint_score("/nonexistent/path")
    assert result == 1.0  # Empty = no issues


@pytest.mark.parametrize("issues,files,expected_range", [
    (0, 10, (0.9, 1.0)),      # No issues
    (50, 10, (0.4, 0.6)),     # 5 issues per file
    (100, 10, (0.0, 0.1)),    # 10 issues per file
])
def test_lint_score_calculation(issues, files, expected_range):
    """Test lint score calculation logic."""
    # Formula: max(0, 1 - (issues_per_file / 10))
    issues_per_file = issues / files if files > 0 else 0
    score = max(0.0, 1.0 - (issues_per_file / 10.0))
    
    assert expected_range[0] <= score <= expected_range[1]


def test_compute_req_coverage():
    """Test requirements coverage computation."""
    with patch('src.measure._extract_keywords', return_value=['create', 'simple', 'calculator']), \
         patch('src.measure._extract_codebase_text', return_value='def create_calculator(): simple code here'):
        
        coverage = compute_req_coverage("Create a simple calculator", "/fake/path")
        
        # All 3 keywords present
        assert coverage == 1.0


def test_compute_req_coverage_partial():
    """Test partial requirements coverage."""
    with patch('src.measure._extract_keywords', return_value=['create', 'simple', 'calculator']), \
         patch('src.measure._extract_codebase_text', return_value='def create_simple(): code here'):
        
        coverage = compute_req_coverage("Create a simple calculator", "/fake/path")
        
        # 2 out of 3 keywords
        assert abs(coverage - 0.666) < 0.01


def test_pv_bounds(mock_config):
    """Test that PV stays within 0-1 bounds."""
    # All metrics at max
    with patch('src.measure.compute_similarity', return_value=1.0), \
         patch('src.measure.compute_test_pass_rate', return_value=1.0), \
         patch('src.measure.compute_lint_score', return_value=1.0), \
         patch('src.measure.compute_req_coverage', return_value=1.0):
        
        pv = compute_pv("test", "/fake", None, mock_config)
        assert 0.0 <= pv <= 1.0
        assert abs(pv - 1.0) < 0.001
    
    # All metrics at min
    with patch('src.measure.compute_similarity', return_value=0.0), \
         patch('src.measure.compute_test_pass_rate', return_value=0.0), \
         patch('src.measure.compute_lint_score', return_value=0.0), \
         patch('src.measure.compute_req_coverage', return_value=0.0):
        
        pv = compute_pv("test", "/fake", None, mock_config)
        assert 0.0 <= pv <= 1.0
        assert abs(pv - 0.0) < 0.001
