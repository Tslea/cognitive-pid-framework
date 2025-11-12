"""
Utility Functions

Common utilities for logging, file operations, and helper functions.
"""

import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Any, List, Optional


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """Setup structured logging with file rotation.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured logger
    """
    # Get log level from config
    log_level = config.get('orchestration', {}).get('log_level', 'INFO')
    log_path = config.get('repository', {}).get('log_path', './logs')
    
    # Create log directory
    os.makedirs(log_path, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_path, f'orchestrator_{timestamp}.log')
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)  # Always debug in file
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized: {log_file}")
    
    return logger


def log_iteration(
    iteration: int,
    pv: float,
    best_pv: float,
    control_value: float,
    agent_params: Dict[str, Any],
    decision: Dict[str, str],
    config: Dict[str, Any]
) -> None:
    """Log iteration details to structured file.
    
    Args:
        iteration: Iteration number
        pv: Process variable
        best_pv: Best PV so far
        control_value: PID control value
        agent_params: Agent parameters
        decision: Decision made
        config: Configuration
    """
    log_path = config.get('repository', {}).get('log_path', './logs')
    iteration_log_file = os.path.join(log_path, 'iterations.jsonl')
    
    # Create log entry
    log_entry = {
        'iteration': iteration,
        'timestamp': datetime.now().isoformat(),
        'pv': pv,
        'best_pv': best_pv,
        'control_value': control_value,
        'agent_params': agent_params,
        'decision': decision,
    }
    
    # Append to JSONL file
    with open(iteration_log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


def detect_stagnation(
    pv_history: List[float],
    threshold: float,
    window: int
) -> bool:
    """Detect if the system is stagnant (not improving).
    
    Args:
        pv_history: List of PV values
        threshold: Minimum improvement required
        window: Number of iterations to check
        
    Returns:
        True if stagnant, False otherwise
    """
    if len(pv_history) < window:
        return False
    
    recent = pv_history[-window:]
    
    # Check if improvement is below threshold
    improvement = max(recent) - min(recent)
    
    return improvement < threshold


def ensure_directory(path: str) -> None:
    """Ensure a directory exists.
    
    Args:
        path: Directory path
    """
    os.makedirs(path, exist_ok=True)


def read_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Read JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Dictionary or None if error
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to read JSON file {filepath}: {e}")
        return None


def write_json_file(filepath: str, data: Dict[str, Any]) -> bool:
    """Write JSON file.
    
    Args:
        filepath: Path to JSON file
        data: Data to write
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to write JSON file {filepath}: {e}")
        return False


def count_files_by_extension(directory: str) -> Dict[str, int]:
    """Count files by extension in a directory.
    
    Args:
        directory: Directory to scan
        
    Returns:
        Dictionary mapping extension to count
    """
    counts = {}
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden and ignored directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]
        
        for file in files:
            if file.startswith('.'):
                continue
            
            ext = os.path.splitext(file)[1] or 'no_ext'
            counts[ext] = counts.get(ext, 0) + 1
    
    return counts


def count_lines_of_code(directory: str) -> int:
    """Count total lines of code in a directory.
    
    Args:
        directory: Directory to scan
        
    Returns:
        Total line count
    """
    total = 0
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]
        
        for file in files:
            if not any(file.endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']):
                continue
            
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    total += sum(1 for _ in f)
            except (IOError, OSError, UnicodeDecodeError):
                # Skip files that can't be read
                pass
    
    return total


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def truncate_string(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate string to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


class ProgressTracker:
    """Track progress of multi-step operations."""
    
    def __init__(self, total_steps: int):
        """Initialize progress tracker.
        
        Args:
            total_steps: Total number of steps
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = datetime.now()
    
    def step(self, message: str = "") -> None:
        """Increment step counter.
        
        Args:
            message: Optional progress message
        """
        self.current_step += 1
        percentage = (self.current_step / self.total_steps) * 100
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if self.current_step > 0:
            eta = (elapsed / self.current_step) * (self.total_steps - self.current_step)
        else:
            eta = 0
        
        progress_msg = f"Progress: {self.current_step}/{self.total_steps} ({percentage:.1f}%) - ETA: {format_duration(eta)}"
        
        if message:
            progress_msg += f" - {message}"
        
        logging.getLogger(__name__).info(progress_msg)
    
    def finish(self) -> None:
        """Mark progress as finished."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logging.getLogger(__name__).info(f"Completed in {format_duration(elapsed)}")
