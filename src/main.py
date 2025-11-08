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
from typing import Dict, Any, Optional

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
        qa_output = call_qa(
            developer_output['patch'],
            state['codebase_path'],
            qa_params
        )
        
        self.logger.info(f"QA result: {qa_output['verdict']} ({len(qa_output['issues'])} issues)")
        
        # Step 4: Measure process variable (PV)
        self.logger.info("Step 4: Computing process variable (PV)...")
        pv = compute_pv(
            setpoint=state['setpoint'],
            codebase_path=state['codebase_path'],
            test_results=qa_output['test_results'],
            config=self.config
        )
        
        self.logger.info(f"PV = {pv:.4f} (target: {setpoint_quality:.4f})")
        self.pv_history.append(pv)
        
        # Step 5: Compute PID control value
        self.logger.info("Step 5: Computing PID control...")
        control_value = self.pid_controller.compute(setpoint_quality, pv)
        
        self.logger.info(f"Control value: {control_value:.4f}")
        self.logger.info(f"Error: {self.pid_controller.error:.4f}")
        self.logger.info(f"Integral: {self.pid_controller.integral:.4f}")
        self.logger.info(f"Derivative: {self.pid_controller.derivative:.4f}")
        
        # Step 6: Adjust strategies based on control
        self._adjust_strategies(control_value)
        
        # Step 7: Decide on merge/rollback
        decision = self._make_merge_decision(pv, qa_output, control_value)
        self.logger.info(f"Decision: {decision['action']} - {decision['reason']}")
        
        # Step 8: Execute decision
        if decision['action'] == 'merge':
            self._apply_patch(developer_output['patch'], state['codebase_path'])
            state['completed_tasks'].append(current_task)
            state['current_tasks'].pop(0)
        elif decision['action'] == 'rollback':
            best_checkpoint = get_best_checkpoint()
            if best_checkpoint:
                rollback_to_checkpoint(best_checkpoint, state['codebase_path'])
        
        # Step 9: Checkpoint if needed
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
        
        return {'action': 'skip', 'reason': 'Negative control, skipping merge'}

    def _apply_patch(self, patch: str, codebase_path: str) -> None:
        """Apply a code patch to the codebase.
        
        Args:
            patch: Patch/diff string
            codebase_path: Path to codebase
        """
        # TODO: Implement actual patch application
        # This is a placeholder - real implementation should use git apply or similar
        self.logger.info(f"Applying patch to {codebase_path}")
        # For now, just log the patch
        self.logger.debug(f"Patch content:\n{patch}")

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
