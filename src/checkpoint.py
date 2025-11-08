"""
Checkpoint and Rollback System

Manages codebase snapshots for recovery and tracking best states.
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import git


# Global checkpoint state
_checkpoint_dir = None
_best_checkpoint = None
_checkpoint_history = []


def initialize_checkpoint_system(config: Dict[str, Any]) -> None:
    """Initialize checkpoint system.
    
    Args:
        config: Configuration dictionary
    """
    global _checkpoint_dir
    
    logger = logging.getLogger(__name__)
    
    _checkpoint_dir = config['repository']['checkpoint_path']
    
    # Create checkpoint directory
    os.makedirs(_checkpoint_dir, exist_ok=True)
    
    logger.info(f"Checkpoint system initialized: {_checkpoint_dir}")


def create_checkpoint(
    codebase_path: str,
    pv: float,
    iteration: int,
    is_best: bool = False
) -> str:
    """Create a checkpoint of the current codebase.
    
    Args:
        codebase_path: Path to codebase
        pv: Process variable value
        iteration: Iteration number
        is_best: Whether this is the best checkpoint so far
        
    Returns:
        Checkpoint ID
    """
    global _best_checkpoint, _checkpoint_history
    
    logger = logging.getLogger(__name__)
    
    # Generate checkpoint ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_id = f"checkpoint_iter{iteration:03d}_{timestamp}_pv{pv:.3f}"
    
    checkpoint_path = os.path.join(_checkpoint_dir, checkpoint_id)
    
    try:
        # Create checkpoint directory
        os.makedirs(checkpoint_path, exist_ok=True)
        
        # Copy codebase (if exists)
        if os.path.exists(codebase_path):
            shutil.copytree(
                codebase_path,
                os.path.join(checkpoint_path, 'codebase'),
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('*.pyc', '__pycache__', '.git', 'node_modules', 'venv')
            )
        
        # Save metadata
        metadata = {
            'checkpoint_id': checkpoint_id,
            'iteration': iteration,
            'pv': pv,
            'timestamp': timestamp,
            'is_best': is_best,
            'codebase_path': codebase_path
        }
        
        with open(os.path.join(checkpoint_path, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update best checkpoint
        if is_best:
            _best_checkpoint = checkpoint_id
            logger.info(f"New best checkpoint: {checkpoint_id} (PV={pv:.3f})")
        
        # Add to history
        _checkpoint_history.append(metadata)
        
        logger.info(f"Checkpoint created: {checkpoint_id}")
        
        return checkpoint_id
        
    except Exception as e:
        logger.error(f"Failed to create checkpoint: {e}")
        return None


def rollback_to_checkpoint(checkpoint_id: str, target_path: str) -> bool:
    """Rollback codebase to a specific checkpoint.
    
    Args:
        checkpoint_id: Checkpoint ID to restore
        target_path: Where to restore the codebase
        
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    checkpoint_path = os.path.join(_checkpoint_dir, checkpoint_id)
    
    if not os.path.exists(checkpoint_path):
        logger.error(f"Checkpoint not found: {checkpoint_id}")
        return False
    
    try:
        # Load metadata
        with open(os.path.join(checkpoint_path, 'metadata.json'), 'r') as f:
            metadata = json.load(f)
        
        logger.info(
            f"Rolling back to checkpoint: {checkpoint_id} "
            f"(iteration={metadata['iteration']}, PV={metadata['pv']:.3f})"
        )
        
        # Clear target directory
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        
        # Copy checkpoint codebase to target
        checkpoint_codebase = os.path.join(checkpoint_path, 'codebase')
        if os.path.exists(checkpoint_codebase):
            shutil.copytree(checkpoint_codebase, target_path)
        else:
            os.makedirs(target_path, exist_ok=True)
        
        logger.info(f"Rollback successful to {checkpoint_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to rollback: {e}")
        return False


def get_best_checkpoint() -> Optional[str]:
    """Get the ID of the best checkpoint.
    
    Returns:
        Best checkpoint ID or None
    """
    return _best_checkpoint


def get_checkpoint_history() -> list:
    """Get list of all checkpoints.
    
    Returns:
        List of checkpoint metadata dictionaries
    """
    return _checkpoint_history.copy()


def cleanup_old_checkpoints(keep_last_n: int = 10) -> None:
    """Remove old checkpoints, keeping only the most recent.
    
    Args:
        keep_last_n: Number of checkpoints to keep
    """
    logger = logging.getLogger(__name__)
    
    if len(_checkpoint_history) <= keep_last_n:
        return
    
    # Sort by iteration
    sorted_checkpoints = sorted(_checkpoint_history, key=lambda x: x['iteration'])
    
    # Keep best + last N
    to_keep = set()
    if _best_checkpoint:
        to_keep.add(_best_checkpoint)
    
    for checkpoint in sorted_checkpoints[-keep_last_n:]:
        to_keep.add(checkpoint['checkpoint_id'])
    
    # Remove others
    removed_count = 0
    for checkpoint in sorted_checkpoints:
        checkpoint_id = checkpoint['checkpoint_id']
        if checkpoint_id not in to_keep:
            checkpoint_path = os.path.join(_checkpoint_dir, checkpoint_id)
            if os.path.exists(checkpoint_path):
                try:
                    shutil.rmtree(checkpoint_path)
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove checkpoint {checkpoint_id}: {e}")
    
    if removed_count > 0:
        logger.info(f"Cleaned up {removed_count} old checkpoints")


def create_git_checkpoint(
    repo_path: str,
    message: str,
    tag: Optional[str] = None
) -> bool:
    """Create a Git commit checkpoint.
    
    Alternative to filesystem checkpoints, uses Git for version control.
    
    Args:
        repo_path: Path to Git repository
        message: Commit message
        tag: Optional tag name
        
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        repo = git.Repo(repo_path)
        
        # Stage all changes
        repo.git.add(A=True)
        
        # Commit
        repo.index.commit(message)
        
        logger.info(f"Git checkpoint created: {message}")
        
        # Create tag if specified
        if tag:
            repo.create_tag(tag)
            logger.info(f"Git tag created: {tag}")
        
        return True
        
    except git.exc.InvalidGitRepositoryError:
        logger.warning(f"Not a Git repository: {repo_path}")
        return False
    except Exception as e:
        logger.error(f"Git checkpoint failed: {e}")
        return False


def rollback_git_checkpoint(repo_path: str, tag_or_commit: str) -> bool:
    """Rollback to a Git tag or commit.
    
    Args:
        repo_path: Path to Git repository
        tag_or_commit: Tag name or commit hash
        
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        repo = git.Repo(repo_path)
        
        # Reset to specified commit
        repo.git.reset('--hard', tag_or_commit)
        
        logger.info(f"Git rollback successful to {tag_or_commit}")
        
        return True
        
    except Exception as e:
        logger.error(f"Git rollback failed: {e}")
        return False
