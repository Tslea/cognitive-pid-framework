"""
Measurement System

Implements metrics computation for process variable (PV) calculation including:
- Embedding similarity to setpoint
- Test pass rate
- Lint/code quality score
- Requirements coverage
"""

import logging
import os
import subprocess
from typing import Dict, Any, Optional
import numpy as np


# Global metrics state
_metrics_initialized = False
_sentence_transformer = None


def initialize_metrics(config: Dict[str, Any]) -> None:
    """Initialize metrics system.
    
    Args:
        config: Configuration dictionary
    """
    global _metrics_initialized, _sentence_transformer
    
    logger = logging.getLogger(__name__)
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # Load embedding model (lightweight)
        logger.info("Loading sentence transformer model...")
        _sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
        _metrics_initialized = True
        logger.info("Metrics system initialized")
        
    except ImportError:
        logger.warning(
            "sentence-transformers not installed. "
            "Similarity metrics will be disabled. "
            "Install with: pip install sentence-transformers"
        )
        _metrics_initialized = False
    except Exception as e:
        logger.error(f"Failed to initialize metrics: {e}")
        _metrics_initialized = False


def compute_pv(
    setpoint: str,
    codebase_path: str,
    test_results: Optional[Dict[str, int]] = None,
    config: Optional[Dict[str, Any]] = None
) -> float:
    """Compute process variable (PV) from multiple metrics.
    
    PV = w1*similarity + w2*test_pass_rate + w3*lint_score + w4*req_coverage
    
    Args:
        setpoint: Target project description
        codebase_path: Path to codebase
        test_results: Test execution results
        config: Configuration with weights
        
    Returns:
        Process variable (0-1 scale)
    """
    logger = logging.getLogger(__name__)
    
    # Default weights
    if config:
        weights = config['metrics']['weights']
    else:
        weights = {
            'similarity': 0.4,
            'test_pass_rate': 0.3,
            'lint_score': 0.2,
            'req_coverage': 0.1
        }
    
    # Compute individual metrics
    similarity = compute_similarity(setpoint, codebase_path)
    test_pass_rate = compute_test_pass_rate(test_results)
    lint_score = compute_lint_score(codebase_path)
    req_coverage = compute_req_coverage(setpoint, codebase_path)
    
    # Weighted sum
    pv = (
        weights['similarity'] * similarity +
        weights['test_pass_rate'] * test_pass_rate +
        weights['lint_score'] * lint_score +
        weights['req_coverage'] * req_coverage
    )
    
    logger.info(
        f"PV components: sim={similarity:.3f}, tests={test_pass_rate:.3f}, "
        f"lint={lint_score:.3f}, req={req_coverage:.3f} → PV={pv:.3f}"
    )
    
    return pv


def compute_similarity(setpoint: str, codebase_path: str) -> float:
    """Compute embedding similarity between setpoint and codebase.
    
    Args:
        setpoint: Target description
        codebase_path: Path to codebase
        
    Returns:
        Similarity score (0-1)
    """
    logger = logging.getLogger(__name__)
    
    if not _metrics_initialized or _sentence_transformer is None:
        logger.debug("Similarity metrics disabled, returning default 0.5")
        return 0.5
    
    try:
        # Get codebase representation
        codebase_text = _extract_codebase_text(codebase_path)
        
        if not codebase_text.strip():
            logger.debug("Empty codebase, similarity=0.0")
            return 0.0
        
        # Compute embeddings
        setpoint_embedding = _sentence_transformer.encode(setpoint, convert_to_tensor=False)
        codebase_embedding = _sentence_transformer.encode(codebase_text, convert_to_tensor=False)
        
        # Cosine similarity
        similarity = np.dot(setpoint_embedding, codebase_embedding) / (
            np.linalg.norm(setpoint_embedding) * np.linalg.norm(codebase_embedding)
        )
        
        # Normalize to 0-1 (cosine is -1 to 1)
        similarity = (similarity + 1) / 2
        
        logger.debug(f"Embedding similarity: {similarity:.3f}")
        
        return float(similarity)
        
    except Exception as e:
        logger.warning(f"Similarity computation failed: {e}")
        return 0.5


def compute_test_pass_rate(test_results: Optional[Dict[str, int]]) -> float:
    """Compute test pass rate.
    
    Args:
        test_results: Dictionary with 'total', 'passed', 'failed', 'skipped'
        
    Returns:
        Pass rate (0-1)
    """
    if not test_results or test_results.get('total', 0) == 0:
        # No tests = neutral score
        return 0.5
    
    total = test_results['total']
    passed = test_results.get('passed', 0)
    
    return passed / total if total > 0 else 0.0


def compute_lint_score(codebase_path: str) -> float:
    """Compute code quality score using flake8.
    
    Args:
        codebase_path: Path to codebase
        
    Returns:
        Quality score (0-1, higher is better)
    """
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(codebase_path):
        return 1.0  # Empty codebase = no issues
    
    try:
        # Run flake8
        result = subprocess.run(
            ['flake8', '--count', '--statistics', codebase_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse error count
        output = result.stdout + result.stderr
        
        # Count total issues
        # flake8 outputs: "X     E111 ..." for each error type
        import re
        matches = re.findall(r'(\d+)\s+[EWF]\d+', output)
        total_issues = sum(int(m) for m in matches) if matches else 0
        
        # Count files
        python_files = sum(
            1 for root, dirs, files in os.walk(codebase_path)
            for f in files if f.endswith('.py') and not f.startswith('.')
        )
        
        if python_files == 0:
            return 1.0
        
        # Score: fewer issues per file = higher score
        # Assume 10 issues per file is "bad" (score 0)
        issues_per_file = total_issues / python_files if python_files > 0 else 0
        score = max(0.0, 1.0 - (issues_per_file / 10.0))
        
        logger.debug(f"Lint score: {total_issues} issues in {python_files} files → {score:.3f}")
        
        return score
        
    except FileNotFoundError:
        logger.debug("flake8 not found, skipping lint check")
        return 0.7  # Assume reasonable quality
    except subprocess.TimeoutExpired:
        logger.warning("flake8 timeout")
        return 0.5
    except Exception as e:
        logger.warning(f"Lint check failed: {e}")
        return 0.5


def compute_req_coverage(setpoint: str, codebase_path: str) -> float:
    """Estimate requirements coverage.
    
    Uses simple keyword matching between setpoint and codebase.
    
    Args:
        setpoint: Project requirements
        codebase_path: Path to codebase
        
    Returns:
        Coverage estimate (0-1)
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Extract keywords from setpoint
        keywords = _extract_keywords(setpoint)
        
        if not keywords:
            return 0.5
        
        # Get codebase text
        codebase_text = _extract_codebase_text(codebase_path).lower()
        
        if not codebase_text:
            return 0.0
        
        # Count keyword matches
        matches = sum(1 for kw in keywords if kw.lower() in codebase_text)
        coverage = matches / len(keywords) if keywords else 0.0
        
        logger.debug(f"Requirements coverage: {matches}/{len(keywords)} keywords → {coverage:.3f}")
        
        return coverage
        
    except Exception as e:
        logger.warning(f"Requirements coverage failed: {e}")
        return 0.5


def _extract_codebase_text(codebase_path: str, max_chars: int = 10000) -> str:
    """Extract text content from codebase.
    
    Args:
        codebase_path: Path to codebase
        max_chars: Maximum characters to extract
        
    Returns:
        Concatenated text from files
    """
    if not os.path.exists(codebase_path):
        return ""
    
    texts = []
    total_chars = 0
    
    for root, dirs, files in os.walk(codebase_path):
        # Skip hidden and common ignore directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]
        
        for file in files:
            # Focus on source files
            if not any(file.endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']):
                continue
            
            if file.startswith('.'):
                continue
            
            filepath = os.path.join(root, file)
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_chars - total_chars)
                    texts.append(content)
                    total_chars += len(content)
                    
                    if total_chars >= max_chars:
                        break
            except:
                continue
        
        if total_chars >= max_chars:
            break
    
    return '\n'.join(texts)


def _extract_keywords(text: str) -> list:
    """Extract important keywords from text.
    
    Args:
        text: Input text
        
    Returns:
        List of keywords
    """
    # Simple keyword extraction: words longer than 4 chars, excluding common words
    stopwords = {'this', 'that', 'with', 'from', 'have', 'will', 'should', 'would', 'could', 'their', 'there', 'where', 'when', 'what', 'which'}
    
    import re
    words = re.findall(r'\b\w{5,}\b', text.lower())
    keywords = [w for w in words if w not in stopwords]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)
    
    return unique_keywords[:20]  # Limit to top 20
