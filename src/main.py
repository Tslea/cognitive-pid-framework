"""
Cognitive PID Framework - Main Orchestrator

This module implements the main control loop that coordinates the three-agent
system (Keeper, Developer, QA) using PID feedback control.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import yaml
from dotenv import load_dotenv

from controller import PIDController
from agent_keeper import call_keeper
from agent_developer import call_developer
from agent_qa import call_qa
from measure import compute_pv, initialize_metrics
from checkpoint import (
    initialize_checkpoint_system,
    create_checkpoint,
    rollback_to_checkpoint,
    get_best_checkpoint,
)
from utils import setup_logging, log_iteration, detect_stagnation


class CognitivePIDOrchestrator:
    """Main orchestrator for the Cognitive PID Framework."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the orchestrator with configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config = self._load_config(config_path)
        self.logger = setup_logging(self.config)
        self.pid_controller = PIDController(self.config)
        
        # State tracking
        self.iteration = 0
        self.total_cost = 0.0
        self.pv_history = []
        self.best_pv = 0.0
        self.best_iteration = 0
        self.stagnation_counter = 0
        
        # Initialize systems
        initialize_metrics(self.config)
        initialize_checkpoint_system(self.config)
        
        self.logger.info("Cognitive PID Orchestrator initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            Configuration dictionary
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    
    def _get_min_quality_threshold(self, iteration: int) -> float:
        """Calculate minimum quality score based on iteration number.
        
        Progressive thresholds allow early iterations to have lower quality
        while requiring higher quality in later iterations.
        
        Args:
            iteration: Current iteration number
            
        Returns:
            Minimum quality score threshold
        """
        if not self.config['safety'].get('quality_progression_enabled', False):
            return self.config['safety'].get('min_quality_score', 5.0)
        
        if iteration <= 5:
            return self.config['safety'].get('min_quality_score_initial', 2.5)
        elif iteration <= 15:
            return self.config['safety'].get('min_quality_score_mid', 4.5)
        else:
            return self.config['safety'].get('min_quality_score_final', 6.5)

    def run(self, setpoint: str, max_iterations: Optional[int] = None) -> Dict[str, Any]:
        """Execute the main orchestration loop.
        
        Args:
            setpoint: Project description/goal
            max_iterations: Maximum iterations (overrides config if provided)
            
        Returns:
            Dictionary with final results and statistics
        """
        # Override max iterations if provided
        if max_iterations:
            self.config['safety']['max_iterations'] = max_iterations
        
        max_iter = self.config['safety']['max_iterations']
        setpoint_quality = self.config['pid']['setpoint']
        
        self.logger.info(f"Starting orchestration loop")
        self.logger.info(f"Setpoint: {setpoint}")
        self.logger.info(f"Target quality: {setpoint_quality}")
        self.logger.info(f"Max iterations: {max_iter}")
        
        # Store setpoint for agents
        state = {
            'setpoint': setpoint,
            'codebase_path': self.config['repository']['base_path'],
            'iteration': 0,
            'current_tasks': [],
            'completed_tasks': [],
        }
        
        # Main control loop
        while self.iteration < max_iter:
            self.iteration += 1
            state['iteration'] = self.iteration
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"ITERATION {self.iteration}/{max_iter}")
            self.logger.info(f"{'='*60}")
            
            try:
                # Execute agent sequence
                iteration_result = self._execute_iteration(state, setpoint_quality)
                
                # Check safety guards
                if not self._check_safety_guards(iteration_result):
                    break
                
                # Update state
                state = iteration_result['state']
                
            except Exception as e:
                self.logger.error(f"Iteration {self.iteration} failed: {e}", exc_info=True)
                # Decide whether to continue or abort
                if self._should_abort_on_error():
                    break
                continue
        
        # Finalize and return results
        return self._finalize(state)

    def _execute_iteration(self, state: Dict[str, Any], setpoint_quality: float) -> Dict[str, Any]:
        """Execute a single iteration of the control loop.
        
        Args:
            state: Current system state
            setpoint_quality: Target quality metric
            
        Returns:
            Dictionary with iteration results
        """
        # Step 1: Keeper generates tasks
        self.logger.info("Step 1: Calling Keeper agent...")
        keeper_params = self._get_agent_params('keeper')
        keeper_output = call_keeper(state, keeper_params)
        
        self.logger.info(f"Keeper generated {len(keeper_output['tasks'])} tasks")
        state['current_tasks'] = keeper_output['tasks']
        
        # Step 2: Developer implements next task
        if not state['current_tasks']:
            self.logger.warning("No tasks from Keeper, ending iteration")
            return self._create_iteration_result(state, 0.0, "No tasks available")
        
        current_task = state['current_tasks'][0]
        self.logger.info(f"Step 2: Calling Developer agent for task: {current_task['title']}")
        
        developer_params = self._get_agent_params('developer')
        developer_output = call_developer(
            current_task,
            state['codebase_path'],
            developer_params
        )
        
        self.logger.info(f"Developer generated patch with {len(developer_output['risks'])} risks")
        
        # Step 3: QA validates patch
        self.logger.info("Step 3: Calling QA agent...")
        qa_params = self._get_agent_params('qa')
        # Pass full developer output context to QA
        qa_params['files_modified'] = developer_output.get('files_modified', [])
        qa_params['files_created'] = developer_output.get('files_created', [])
        qa_params['risks'] = developer_output.get('risks', [])
        qa_params['testing_suggestions'] = developer_output.get('testing_suggestions', [])
        qa_output = call_qa(
            developer_output['patch'],
            state['codebase_path'],
            qa_params
        )
        
        self.logger.info(f"QA result: {qa_output['verdict']} ({len(qa_output['issues'])} issues)")
        
        # Step 4: Get previous PV for control calculation (before applying patch)
        prev_pv = self.pv_history[-1] if self.pv_history else 0.0
        
        # Step 5: Compute PID control value using previous PV
        self.logger.info("Step 5: Computing PID control (using previous PV)...")
        control_value = self.pid_controller.compute(setpoint_quality, prev_pv)
        
        self.logger.info(f"Control value: {control_value:.4f}")
        self.logger.info(f"Error: {self.pid_controller.error:.4f}")
        self.logger.info(f"Integral: {self.pid_controller.integral:.4f}")
        self.logger.info(f"Derivative: {self.pid_controller.derivative:.4f}")
        
        # Step 6: Adjust strategies based on control
        self._adjust_strategies(control_value)
        
        # Step 7: Decide on merge/rollback (using previous PV and QA output)
        decision = self._make_merge_decision(prev_pv, qa_output, control_value)
        self.logger.info(f"Decision: {decision['action']} - {decision['reason']}")
        
        # Step 8: Apply patch BEFORE measuring PV (so PV reflects new codebase)
        # This ensures files are created and PV is calculated on updated code
        if decision['action'] in ['merge', 'skip', 'human_review']:
            # Apply patch to allow progress even if decision is 'skip' or 'human_review'
            # In early iterations, also apply on 'reject' to allow learning
            should_apply = decision['action'] in ['merge', 'skip', 'human_review']
            if decision['action'] == 'reject' and self.iteration <= 3:
                should_apply = True
                self.logger.info("Early iteration: applying patch despite reject to allow learning")
            
            if should_apply:
                self.logger.info("Step 8: Applying patch to codebase...")
                self._apply_patch(
                    developer_output['patch'],
                    developer_output.get('files_modified', []),
                    developer_output.get('files_created', []),
                    state['codebase_path']
                )
                if decision['action'] == 'merge':
                    state['completed_tasks'].append(current_task)
                    state['current_tasks'].pop(0)
            else:
                self.logger.warning(f"Patch not applied due to decision: {decision['action']}")
        elif decision['action'] == 'rollback':
            best_checkpoint = get_best_checkpoint()
            if best_checkpoint:
                self.logger.info("Step 8: Rolling back to best checkpoint...")
                rollback_to_checkpoint(best_checkpoint, state['codebase_path'])
        
        # Step 9: Measure process variable (PV) AFTER patch application
        # This ensures PV reflects the actual state of the codebase
        self.logger.info("Step 9: Computing process variable (PV) on updated codebase...")
        pv = compute_pv(
            setpoint=state['setpoint'],
            codebase_path=state['codebase_path'],
            test_results=qa_output['test_results'],
            config=self.config
        )
        
        self.logger.info(f"PV = {pv:.4f} (target: {setpoint_quality:.4f})")
        
        # If we rolled back, PV might have changed - update it
        if decision['action'] == 'rollback':
            self.logger.info("PV recalculated after rollback")
        
        self.pv_history.append(pv)
        
        # Step 10: Checkpoint if needed
        if self.iteration % self.config['orchestration']['checkpoint_frequency'] == 0:
            create_checkpoint(state['codebase_path'], pv, self.iteration)
        
        # Track best state
        if pv > self.best_pv:
            self.best_pv = pv
            self.best_iteration = self.iteration
            create_checkpoint(state['codebase_path'], pv, self.iteration, is_best=True)
        
        # Log iteration
        log_iteration(
            self.iteration,
            pv,
            self.best_pv,
            control_value,
            self._get_all_agent_params(),
            decision,
            self.config
        )
        
        return self._create_iteration_result(state, pv, decision['action'])

    def _get_agent_params(self, agent_type: str) -> Dict[str, Any]:
        """Get parameters for a specific agent.
        
        Args:
            agent_type: 'keeper', 'developer', or 'qa'
            
        Returns:
            Agent parameters dictionary
        """
        base_params = self.config['models'][agent_type].copy()
        base_params['language'] = self.config['orchestration']['language']
        base_params['iteration'] = self.iteration  # Add current iteration for adaptive prompts
        return base_params

    def _get_all_agent_params(self) -> Dict[str, Any]:
        """Get parameters for all agents."""
        return {
            'keeper': self._get_agent_params('keeper'),
            'developer': self._get_agent_params('developer'),
            'qa': self._get_agent_params('qa'),
        }

    def _adjust_strategies(self, control_value: float) -> None:
        """Adjust agent strategies based on control value.
        
        Args:
            control_value: Current PID control value
        """
        # Positive control = increase effort/quality
        # Negative control = reduce effort/cost
        
        # Adjust developer temperature (lower = more deterministic)
        base_temp = self.config['models']['developer']['temperature']
        if control_value > 2.0:
            # Quality too low, make code more conservative
            self.config['models']['developer']['temperature'] = max(0.1, base_temp - 0.2)
        elif control_value < -2.0:
            # Quality too high, can be more creative
            self.config['models']['developer']['temperature'] = min(1.0, base_temp + 0.2)
        
        # Adjust QA frequency
        if control_value > 3.0:
            # Quality too low, run QA every iteration
            self.config['orchestration']['qa_frequency'] = 1
        elif control_value < -1.0:
            # Quality stable, can reduce QA frequency
            self.config['orchestration']['qa_frequency'] = 2
        
        self.logger.debug(f"Adjusted strategies: temp={self.config['models']['developer']['temperature']:.2f}, qa_freq={self.config['orchestration']['qa_frequency']}")

    def _make_merge_decision(self, pv: float, qa_output: Dict[str, Any], control_value: float) -> Dict[str, str]:
        """Decide whether to merge, rollback, or require human review.
        
        Args:
            pv: Current process variable
            qa_output: QA agent output
            control_value: PID control value
            
        Returns:
            Decision dictionary with 'action' and 'reason'
        """
        # Get progressive quality threshold
        min_quality = self._get_min_quality_threshold(self.iteration)
        quality_score = qa_output.get('quality_score', 0)
        
        self.logger.info(f"Quality check: score={quality_score:.2f}, threshold={min_quality:.2f} (iteration {self.iteration})")
        
        # Check if human review needed
        if pv < self.config['safety']['human_review_threshold']:
            return {'action': 'human_review', 'reason': f'PV {pv:.3f} below threshold'}
        
        # Check QA verdict and progressive quality threshold
        if qa_output['verdict'] == 'fail' and quality_score < min_quality:
            return {'action': 'reject', 'reason': f'QA score {quality_score:.2f} < threshold {min_quality:.2f}'}
        
        # Allow merge if quality meets progressive threshold (even if verdict is fail but score is acceptable)
        if quality_score >= min_quality:
            return {'action': 'merge', 'reason': f'Quality {quality_score:.2f} >= threshold {min_quality:.2f}'}
        
        # Check for rollback condition
        if pv < self.config['safety']['rollback_threshold']:
            return {'action': 'rollback', 'reason': f'PV {pv:.3f} too low, rolling back'}
        
        # Auto-merge if configured and QA passes
        if self.config['orchestration']['auto_merge'] and qa_output['verdict'] == 'pass':
            return {'action': 'merge', 'reason': 'QA passed, auto-merging'}
        
        # Default to merge if control suggests improvement
        if control_value >= 0:
            return {'action': 'merge', 'reason': 'Control suggests improvement'}
        
        # Even with negative control, allow progress in early iterations
        if self.iteration <= 5:
            return {'action': 'merge', 'reason': 'Early iteration, allowing progress despite negative control'}
        
        # In later iterations, be more cautious but still allow skip (patch will be applied)
        return {'action': 'skip', 'reason': 'Negative control, but allowing patch application for progress'}

    def _validate_patch(
        self,
        patch: str,
        files_created: List[str],
        files_modified: List[str]
    ) -> bool:
        """Validate patch before applying.
        
        Args:
            patch: Patch string
            files_created: List of files to create
            files_modified: List of files to modify
            
        Returns:
            True if patch is valid, False otherwise
        """
        # Check for basic structure
        if not patch or not patch.strip():
            self.logger.warning("Patch is empty")
            return False
        
        # Check that we have file information
        if not files_created and not files_modified:
            self.logger.warning("No files specified in patch")
            return False
        
        # Check for suspicious patterns (e.g., system file paths)
        suspicious_patterns = ['/etc/', '/usr/', '/bin/', 'C:\\Windows', 'C:\\System']
        all_files = files_created + files_modified
        for file_path in all_files:
            for pattern in suspicious_patterns:
                if pattern in file_path:
                    self.logger.error(f"Suspicious file path detected: {file_path}")
                    return False
        
        # Basic sanity check: patch should contain some code
        code_indicators = ['def ', 'class ', 'import ', 'from ', 'return ', 'if ', 'for ', 'while ']
        has_code = any(indicator in patch for indicator in code_indicators)
        
        if not has_code and len(patch) > 100:
            self.logger.warning("Patch doesn't appear to contain code")
            # Don't fail, might be config files or other content
        
        return True

    def _apply_patch(
        self,
        patch: str,
        files_modified: List[str],
        files_created: List[str],
        codebase_path: str
    ) -> None:
        """Apply a code patch to the codebase.
        
        Args:
            patch: Patch/diff string (unified diff format)
            files_modified: List of modified file paths
            files_created: List of created file paths
            codebase_path: Path to codebase
        """
        import re
        import os
        
        self.logger.info(f"Applying patch to {codebase_path}")
        self.logger.debug(f"Files to modify: {files_modified}")
        self.logger.debug(f"Files to create: {files_created}")
        
        # Ensure codebase directory exists
        os.makedirs(codebase_path, exist_ok=True)
        
        # Validate patch before applying
        if not self._validate_patch(patch, files_created, files_modified):
            self.logger.error("Patch validation failed, skipping application")
            return
        
        # Parse unified diff and apply changes
        if not patch.strip():
            self.logger.warning("Empty patch, nothing to apply")
            return
        
        # Try multiple methods to ensure files are created
        files_created_successfully = False
        
        # Method 1: Try to parse and apply unified diff
        try:
            self._apply_unified_diff(patch, codebase_path)
            files_created_successfully = True
            self.logger.info("Successfully applied unified diff")
        except Exception as e:
            self.logger.warning(f"Failed to apply unified diff: {e}, trying alternative methods")
        
        # Method 2: If unified diff failed or files are missing, try direct creation from patch
        if not files_created_successfully or not self._verify_files_exist(files_created + files_modified, codebase_path):
            try:
                self.logger.info("Attempting direct file creation from patch content...")
                self._apply_patch_fallback(patch, files_created, files_modified, codebase_path)
                files_created_successfully = True
            except Exception as e:
                self.logger.warning(f"Fallback method failed: {e}")
        
        # Method 3: If still no files, try extracting code blocks from patch
        if not files_created_successfully or not self._verify_files_exist(files_created, codebase_path):
            self.logger.info("Attempting to extract and create files from code blocks...")
            self._create_files_from_code_blocks(patch, files_created, codebase_path)
    
    def _apply_unified_diff(self, patch: str, codebase_path: str) -> None:
        """Apply unified diff format patch.
        
        Args:
            patch: Unified diff string
            codebase_path: Path to codebase
        """
        import re
        import os
        
        lines = patch.split('\n')
        current_file = None
        current_mode = None  # 'create' or 'modify'
        file_lines = []
        hunk_started = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Detect file header (+++ or ---)
            if line.startswith('---'):
                # Old file path
                old_path = line[4:].strip()
                if old_path.startswith('a/'):
                    old_path = old_path[2:]
                # Write previous file if exists
                if current_file and file_lines:
                    self._write_file_lines(current_file, file_lines, codebase_path)
                    file_lines = []
                # If old_path is /dev/null, it's a new file
                if old_path == '/dev/null':
                    current_mode = 'create'
                    # Don't set current_file yet, wait for +++
                else:
                    current_file = old_path
                    current_mode = 'modify'
                hunk_started = False
                
            elif line.startswith('+++'):
                # New file path
                new_path = line[4:].strip()
                if new_path.startswith('b/'):
                    new_path = new_path[2:]
                if new_path != '/dev/null':
                    # If we were in create mode (--- /dev/null), this is definitely a new file
                    file_path = os.path.join(codebase_path, new_path)
                    if current_mode == 'create':
                        # Already in create mode from --- /dev/null
                        current_mode = 'create'
                    else:
                        # Check if file exists
                        current_mode = 'create' if not os.path.exists(file_path) else 'modify'
                    current_file = new_path
                    hunk_started = False
                    
            elif line.startswith('@@'):
                # Hunk header
                hunk_started = True
                # Try to load existing file if modifying
                if current_file and current_mode == 'modify' and not file_lines:
                    file_path = os.path.join(codebase_path, current_file)
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            file_lines = f.readlines()
                            # Remove trailing newlines for processing
                            file_lines = [l.rstrip('\n\r') for l in file_lines]
                    else:
                        file_lines = []
                        current_mode = 'create'
                        
            elif hunk_started and current_file:
                if line.startswith('+') and not line.startswith('+++'):
                    # Added line - always add for new files, or append for existing
                    content = line[1:]
                    if current_mode == 'create':
                        # For new files, add all + lines
                        file_lines.append(content)
                    else:
                        # For existing files, append + lines
                        file_lines.append(content)
                elif line.startswith('-') and not line.startswith('---'):
                    # Removed line - skip it (already handled by not including in file_lines)
                    if current_mode == 'modify':
                        # In modify mode, we need to track line numbers
                        # For simplicity, we'll just skip removed lines
                        pass
                elif line.startswith(' '):
                    # Context line - keep existing or add
                    content = line[1:]
                    if current_mode == 'create':
                        # For new files, include context lines too
                        file_lines.append(content)
                    else:
                        # In modify mode, context lines should match existing
                        # If they don't match, we might be out of sync, but continue anyway
                        if not file_lines or file_lines[-1] != content:
                            # Context doesn't match - might be a problem, but continue
                            pass
                # Lines starting with \ are continuation (ignore for now)
            
            i += 1
        
        # Write last file
        if current_file and file_lines:
            self._write_file_lines(current_file, file_lines, codebase_path)
    
    def _apply_patch_fallback(
        self,
        patch: str,
        files_created: List[str],
        files_modified: List[str],
        codebase_path: str
    ) -> None:
        """Fallback method: extract code blocks from patch and create files.
        
        Args:
            patch: Patch string
            files_created: List of files to create
            files_modified: List of files to modify
            codebase_path: Path to codebase
        """
        import re
        import os
        
        # Try to extract code from patch using simple heuristics
        # Look for code blocks between file markers
        all_files = set(files_created + files_modified)
        
        for file_path in all_files:
            # Try to find file content in patch
            pattern = rf'(?:^|\n)(?:---|\+\+\+).*{re.escape(file_path)}.*\n(.*?)(?=\n(?:---|\+\+\+)|$)'
            match = re.search(pattern, patch, re.DOTALL | re.MULTILINE)
            
            if match:
                content = match.group(1)
                # Clean up: remove diff markers
                lines = content.split('\n')
                cleaned_lines = []
                for line in lines:
                    if line.startswith('+') and not line.startswith('+++'):
                        cleaned_lines.append(line[1:])
                    elif line.startswith(' ') or line.startswith('-'):
                        # Context or removed - for new files, include context
                        if file_path in files_created:
                            cleaned_lines.append(line[1:] if line.startswith((' ', '-')) else line)
                
                if cleaned_lines:
                    full_path = os.path.join(codebase_path, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(cleaned_lines))
                    self.logger.info(f"Created/modified file: {file_path}")
    
    def _write_file_lines(self, file_path: str, lines: List[str], codebase_path: str) -> None:
        """Write lines to a file.
        
        Args:
            file_path: Relative file path
            lines: List of lines to write
            codebase_path: Base codebase path
        """
        import os
        
        full_path = os.path.join(codebase_path, file_path)
        dir_path = os.path.dirname(full_path)
        if dir_path:  # Only create directory if path is not empty
            os.makedirs(dir_path, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            if lines:
                f.write('\n'.join(lines))
                f.write('\n')  # Add trailing newline
            # If lines is empty, create empty file
        
        self.logger.info(f"Applied changes to: {file_path}")
    
    def _verify_files_exist(self, file_paths: List[str], codebase_path: str) -> bool:
        """Verify that files exist in the codebase.
        
        Args:
            file_paths: List of file paths to check
            codebase_path: Base codebase path
            
        Returns:
            True if all files exist, False otherwise
        """
        import os
        
        if not file_paths:
            return True
        
        for file_path in file_paths:
            full_path = os.path.join(codebase_path, file_path)
            if not os.path.exists(full_path):
                self.logger.debug(f"File not found: {file_path}")
                return False
        
        return True
    
    def _create_files_from_code_blocks(self, patch: str, files_created: List[str], codebase_path: str) -> None:
        """Create files by extracting code blocks from patch.
        
        This method tries to extract complete file content from the patch,
        even if it's not in proper unified diff format.
        
        Args:
            patch: Patch string (may contain code blocks)
            files_created: List of files to create
            codebase_path: Base codebase path
        """
        import re
        import os
        
        if not files_created:
            self.logger.warning("No files to create from code blocks")
            return
        
        # Try to find code blocks for each file
        for file_path in files_created:
            full_path = os.path.join(codebase_path, file_path)
            
            # Skip if file already exists
            if os.path.exists(full_path):
                continue
            
            # Try multiple patterns to extract file content
            content = None
            
            # Pattern 1: Look for file path followed by code block
            pattern1 = rf'(?:^|\n).*{re.escape(file_path)}.*\n(.*?)(?=\n(?:---|\+\+\+|\Z))'
            match = re.search(pattern1, patch, re.DOTALL | re.MULTILINE)
            if match:
                content = match.group(1)
            
            # Pattern 2: Look for code blocks with file extension
            if not content:
                ext = os.path.splitext(file_path)[1]
                if ext:
                    # Look for code blocks that might contain this file
                    code_block_pattern = rf'```(?:python|{ext[1:]})?\n(.*?)```'
                    matches = re.findall(code_block_pattern, patch, re.DOTALL)
                    if matches:
                        # Use the longest match (likely the complete file)
                        content = max(matches, key=len)
            
            # Pattern 3: Extract all lines starting with + (added lines in diff)
            if not content:
                lines = patch.split('\n')
                code_lines = []
                in_file_context = False
                for line in lines:
                    if file_path in line and ('+++' in line or '---' in line):
                        in_file_context = True
                        continue
                    if in_file_context:
                        if line.startswith('+') and not line.startswith('+++'):
                            code_lines.append(line[1:])
                        elif line.startswith('@@'):
                            continue
                        elif line.startswith('---') or line.startswith('+++'):
                            if code_lines:
                                break
                            in_file_context = False
                if code_lines:
                    content = '\n'.join(code_lines)
            
            # If we found content, write the file
            if content:
                # Clean up content: remove diff markers, code block markers, etc.
                content_lines = content.split('\n')
                cleaned_lines = []
                for line in content_lines:
                    # Skip diff markers
                    if line.startswith(('---', '+++', '@@', 'diff --git')):
                        continue
                    # Remove leading + or - from diff lines
                    if line.startswith(('+', '-')) and not line.startswith(('+++', '---')):
                        cleaned_lines.append(line[1:])
                    # Keep context lines and regular code
                    elif line.startswith(' ') or not line.startswith(('+', '-')):
                        cleaned_lines.append(line)
                
                if cleaned_lines:
                    dir_path = os.path.dirname(full_path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(cleaned_lines))
                        f.write('\n')
                    
                    self.logger.info(f"Created file from code block: {file_path}")
            else:
                self.logger.warning(f"Could not extract content for file: {file_path}")

    def _check_safety_guards(self, iteration_result: Dict[str, Any]) -> bool:
        """Check safety guards and return whether to continue.
        
        Args:
            iteration_result: Results from current iteration
            
        Returns:
            True to continue, False to stop
        """
        pv = iteration_result['pv']
        
        # Check budget
        if self.total_cost >= self.config['safety']['max_budget_usd']:
            self.logger.warning(f"Budget limit reached: ${self.total_cost:.2f}")
            return False
        
        # Check stagnation
        is_stagnant = detect_stagnation(
            self.pv_history,
            self.config['safety']['stagnation_threshold'],
            self.config['safety']['stagnation_window']
        )
        
        if is_stagnant:
            self.stagnation_counter += 1
            self.logger.warning(f"Stagnation detected ({self.stagnation_counter} times)")
            if self.stagnation_counter >= 3:
                self.logger.error("Persistent stagnation, stopping")
                return False
        else:
            self.stagnation_counter = 0
        
        # Check oscillation
        if self.pid_controller.is_oscillating():
            self.logger.warning("Oscillation detected in control system")
            # Don't stop, but log warning
        
        return True

    def _should_abort_on_error(self) -> bool:
        """Determine if execution should abort after an error.
        
        Returns:
            True to abort, False to continue
        """
        # For now, continue unless critical error
        # TODO: Implement more sophisticated error handling
        return False

    def _create_iteration_result(self, state: Dict[str, Any], pv: float, action: str) -> Dict[str, Any]:
        """Create iteration result dictionary.
        
        Args:
            state: Current state
            pv: Process variable
            action: Action taken
            
        Returns:
            Iteration result dictionary
        """
        return {
            'state': state,
            'pv': pv,
            'action': action,
            'iteration': self.iteration,
        }

    def _finalize(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize orchestration and return results.
        
        Args:
            state: Final state
            
        Returns:
            Results dictionary
        """
        self.logger.info(f"\n{'='*60}")
        self.logger.info("ORCHESTRATION COMPLETE")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Total iterations: {self.iteration}")
        self.logger.info(f"Best PV: {self.best_pv:.4f} at iteration {self.best_iteration}")
        self.logger.info(f"Final PV: {self.pv_history[-1] if self.pv_history else 0:.4f}")
        self.logger.info(f"Total cost: ${self.total_cost:.2f}")
        self.logger.info(f"Tasks completed: {len(state['completed_tasks'])}")
        
        # Rollback to best checkpoint
        best_checkpoint = get_best_checkpoint()
        if best_checkpoint:
            self.logger.info(f"Rolling back to best checkpoint: {best_checkpoint}")
            rollback_to_checkpoint(best_checkpoint, state['codebase_path'])
        
        return {
            'iterations': self.iteration,
            'best_pv': self.best_pv,
            'best_iteration': self.best_iteration,
            'final_pv': self.pv_history[-1] if self.pv_history else 0,
            'total_cost': self.total_cost,
            'pv_history': self.pv_history,
            'completed_tasks': state['completed_tasks'],
            'codebase_path': state['codebase_path'],
        }


def main():
    """Main entry point for the orchestrator."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Cognitive PID Framework Orchestrator')
    parser.add_argument('--setpoint', type=str, required=True,
                        help='Project description/goal')
    parser.add_argument('--max-iterations', type=int,
                        help='Maximum iterations (overrides config)')
    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Path to configuration file')
    parser.add_argument('--workspace', type=str,
                        help='Workspace directory path')
    parser.add_argument('--checkpoint-dir', type=str,
                        help='Checkpoint directory path')
    parser.add_argument('--log-level', type=str,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level')
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = CognitivePIDOrchestrator(args.config)
    
    # Override config if arguments provided
    if args.workspace:
        orchestrator.config['repository']['base_path'] = args.workspace
    if args.checkpoint_dir:
        orchestrator.config['repository']['checkpoint_path'] = args.checkpoint_dir
    if args.log_level:
        orchestrator.config['orchestration']['log_level'] = args.log_level
        orchestrator.logger.setLevel(args.log_level)
    
    # Run orchestration
    try:
        results = orchestrator.run(args.setpoint, args.max_iterations)
        
        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"Iterations: {results['iterations']}")
        print(f"Best PV: {results['best_pv']:.4f} (iteration {results['best_iteration']})")
        print(f"Final PV: {results['final_pv']:.4f}")
        print(f"Tasks completed: {len(results['completed_tasks'])}")
        print(f"Codebase: {results['codebase_path']}")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        print("\n\nOrchestration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nOrchestration failed: {e}")
        logging.exception(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
