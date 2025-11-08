"""
PID Controller Implementation

This module implements a PID (Proportional-Integral-Derivative) controller
with anti-windup, derivative filtering, and oscillation detection for
controlling the software development process.
"""

import logging
from typing import Dict, Any, Optional, List
from collections import deque


class PIDController:
    """PID Controller for process control.
    
    Implements a discrete PID controller with:
    - Anti-windup (integral clamping)
    - Derivative filtering
    - Oscillation detection
    - Hysteresis
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize PID controller with configuration.
        
        Args:
            config: Configuration dictionary with PID parameters
        """
        self.logger = logging.getLogger(__name__)
        
        # PID gains
        self.kp = config['pid']['kp']
        self.ki = config['pid']['ki']
        self.kd = config['pid']['kd']
        self.dt = config['pid']['dt']
        
        # Integral limits (anti-windup)
        self.integral_min = config['pid']['integral_min']
        self.integral_max = config['pid']['integral_max']
        
        # Control limits
        self.control_min = config['pid']['control_min']
        self.control_max = config['pid']['control_max']
        
        # Oscillation detection
        self.oscillation_window = config['pid']['oscillation_window']
        self.oscillation_threshold = config['pid']['oscillation_threshold']
        
        # State variables
        self.integral = 0.0
        self.prev_error = 0.0
        self.error = 0.0
        self.derivative = 0.0
        self.control = 0.0
        
        # History for oscillation detection
        self.error_history: deque = deque(maxlen=self.oscillation_window)
        self.control_history: deque = deque(maxlen=self.oscillation_window)
        
        # Derivative filter (low-pass)
        self.derivative_alpha = 0.1  # Filter coefficient
        self.filtered_derivative = 0.0
        
        self.logger.info(f"PID Controller initialized: Kp={self.kp}, Ki={self.ki}, Kd={self.kd}")

    def compute(self, setpoint: float, process_variable: float) -> float:
        """Compute PID control value.
        
        Args:
            setpoint: Target value (SP)
            process_variable: Current value (PV)
            
        Returns:
            Control value u(t)
        """
        # Compute error
        self.error = setpoint - process_variable
        
        # Proportional term
        p_term = self.kp * self.error
        
        # Integral term with anti-windup
        self.integral += self.error * self.dt
        self.integral = self._clamp(self.integral, self.integral_min, self.integral_max)
        i_term = self.ki * self.integral
        
        # Derivative term with filtering
        raw_derivative = (self.error - self.prev_error) / self.dt if self.dt > 0 else 0.0
        self.filtered_derivative = (
            self.derivative_alpha * raw_derivative +
            (1 - self.derivative_alpha) * self.filtered_derivative
        )
        self.derivative = self.filtered_derivative
        d_term = self.kd * self.derivative
        
        # Compute control value
        self.control = p_term + i_term + d_term
        
        # Clamp control value
        self.control = self._clamp(self.control, self.control_min, self.control_max)
        
        # Update history
        self.error_history.append(self.error)
        self.control_history.append(self.control)
        
        # Store for next iteration
        self.prev_error = self.error
        
        self.logger.debug(
            f"PID: e={self.error:.4f}, P={p_term:.4f}, I={i_term:.4f}, "
            f"D={d_term:.4f}, u={self.control:.4f}"
        )
        
        return self.control

    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value between min and max.
        
        Args:
            value: Value to clamp
            min_val: Minimum value
            max_val: Maximum value
            
        Returns:
            Clamped value
        """
        return max(min_val, min(max_val, value))

    def is_oscillating(self) -> bool:
        """Detect if the system is oscillating.
        
        Uses zero-crossing detection on error signal.
        
        Returns:
            True if oscillation detected, False otherwise
        """
        if len(self.error_history) < self.oscillation_window:
            return False
        
        # Count zero crossings in error signal
        zero_crossings = 0
        errors = list(self.error_history)
        
        for i in range(1, len(errors)):
            if errors[i] * errors[i-1] < 0:  # Sign change
                zero_crossings += 1
        
        # Oscillation if many zero crossings
        oscillation_detected = zero_crossings >= (self.oscillation_window // 2)
        
        if oscillation_detected:
            # Also check amplitude
            error_range = max(errors) - min(errors)
            if error_range > self.oscillation_threshold:
                self.logger.warning(
                    f"Oscillation detected: {zero_crossings} crossings, "
                    f"range={error_range:.4f}"
                )
                return True
        
        return False

    def apply_hysteresis(self, threshold: float = 0.05) -> float:
        """Apply hysteresis to control value to reduce chattering.
        
        Args:
            threshold: Hysteresis threshold
            
        Returns:
            Control value with hysteresis applied
        """
        if abs(self.control) < threshold:
            return 0.0
        return self.control

    def reset(self) -> None:
        """Reset controller state."""
        self.integral = 0.0
        self.prev_error = 0.0
        self.error = 0.0
        self.derivative = 0.0
        self.filtered_derivative = 0.0
        self.control = 0.0
        self.error_history.clear()
        self.control_history.clear()
        self.logger.info("PID Controller reset")

    def get_state(self) -> Dict[str, Any]:
        """Get current controller state.
        
        Returns:
            Dictionary with controller state
        """
        return {
            'error': self.error,
            'integral': self.integral,
            'derivative': self.derivative,
            'control': self.control,
            'error_history': list(self.error_history),
            'control_history': list(self.control_history),
        }

    def tune(self, kp: Optional[float] = None, ki: Optional[float] = None, 
             kd: Optional[float] = None) -> None:
        """Dynamically tune PID parameters.
        
        Args:
            kp: New proportional gain (if provided)
            ki: New integral gain (if provided)
            kd: New derivative gain (if provided)
        """
        if kp is not None:
            self.kp = kp
            self.logger.info(f"Tuned Kp to {kp}")
        if ki is not None:
            self.ki = ki
            self.logger.info(f"Tuned Ki to {ki}")
        if kd is not None:
            self.kd = kd
            self.logger.info(f"Tuned Kd to {kd}")


def compute_pid_with_limits(
    error: float,
    integral: float,
    prev_error: float,
    kp: float,
    ki: float,
    kd: float,
    dt: float,
    integral_limits: tuple = (-10.0, 10.0),
    control_limits: tuple = (-5.0, 5.0),
) -> tuple:
    """Standalone PID computation function.
    
    Args:
        error: Current error
        integral: Current integral value
        prev_error: Previous error
        kp: Proportional gain
        ki: Integral gain
        kd: Derivative gain
        dt: Time step
        integral_limits: (min, max) for integral
        control_limits: (min, max) for control
        
    Returns:
        Tuple of (control_value, new_integral, derivative)
    """
    # Update integral with clamping
    new_integral = integral + error * dt
    new_integral = max(integral_limits[0], min(integral_limits[1], new_integral))
    
    # Compute derivative
    derivative = (error - prev_error) / dt if dt > 0 else 0.0
    
    # Compute control
    control = kp * error + ki * new_integral + kd * derivative
    
    # Clamp control
    control = max(control_limits[0], min(control_limits[1], control))
    
    return control, new_integral, derivative


def detect_oscillation(error_history: List[float], threshold: float = 0.15) -> bool:
    """Detect oscillation in error signal.
    
    Args:
        error_history: List of recent error values
        threshold: Oscillation amplitude threshold
        
    Returns:
        True if oscillating, False otherwise
    """
    if len(error_history) < 4:
        return False
    
    # Count zero crossings
    crossings = 0
    for i in range(1, len(error_history)):
        if error_history[i] * error_history[i-1] < 0:
            crossings += 1
    
    # Check amplitude
    amplitude = max(error_history) - min(error_history)
    
    return crossings >= len(error_history) // 2 and amplitude > threshold


def apply_deadband(value: float, deadband: float = 0.05) -> float:
    """Apply deadband (hysteresis) to reduce small oscillations.
    
    Args:
        value: Input value
        deadband: Deadband width
        
    Returns:
        Value with deadband applied
    """
    if abs(value) < deadband:
        return 0.0
    return value
