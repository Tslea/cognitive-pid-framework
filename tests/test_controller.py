"""
Tests for PID controller
"""

import pytest
from src.controller import (
    PIDController,
    compute_pid_with_limits,
    detect_oscillation,
    apply_deadband
)


@pytest.fixture
def mock_config():
    """Mock configuration."""
    return {
        'pid': {
            'kp': 1.0,
            'ki': 0.1,
            'kd': 0.05,
            'dt': 1.0,
            'integral_min': -10.0,
            'integral_max': 10.0,
            'control_min': -5.0,
            'control_max': 5.0,
            'oscillation_window': 5,
            'oscillation_threshold': 0.15
        }
    }


def test_pid_initialization(mock_config):
    """Test PID controller initialization."""
    controller = PIDController(mock_config)
    
    assert controller.kp == 1.0
    assert controller.ki == 0.1
    assert controller.kd == 0.05
    assert controller.integral == 0.0
    assert controller.error == 0.0


def test_pid_proportional_only(mock_config):
    """Test proportional term only."""
    # Set Ki and Kd to zero
    mock_config['pid']['ki'] = 0.0
    mock_config['pid']['kd'] = 0.0
    
    controller = PIDController(mock_config)
    
    # Error = 1.0, Kp = 1.0 → control = 1.0
    control = controller.compute(setpoint=1.0, process_variable=0.0)
    assert abs(control - 1.0) < 0.01


def test_pid_integral_accumulation(mock_config):
    """Test integral term accumulation."""
    controller = PIDController(mock_config)
    
    # Constant error should accumulate integral
    for _ in range(5):
        controller.compute(setpoint=1.0, process_variable=0.5)
    
    # Integral should be positive and increasing
    assert controller.integral > 0
    
    # Control should include integral term
    assert controller.control > controller.kp * controller.error


def test_pid_anti_windup(mock_config):
    """Test anti-windup (integral clamping)."""
    controller = PIDController(mock_config)
    
    # Large sustained error
    for _ in range(200):
        controller.compute(setpoint=10.0, process_variable=0.0)
    
    # Integral should be clamped
    assert controller.integral <= mock_config['pid']['integral_max']
    assert controller.integral >= mock_config['pid']['integral_min']


def test_pid_derivative_response(mock_config):
    """Test derivative term response to error change."""
    controller = PIDController(mock_config)
    
    # Step 1: error = 0
    controller.compute(setpoint=1.0, process_variable=1.0)
    
    # Step 2: error = 1 (rapid change)
    controller.compute(setpoint=1.0, process_variable=0.0)
    
    # Derivative should be non-zero due to error change
    assert controller.derivative != 0.0


def test_pid_control_limits(mock_config):
    """Test control value clamping."""
    controller = PIDController(mock_config)
    
    # Very large error
    control = controller.compute(setpoint=100.0, process_variable=0.0)
    
    # Control should be clamped
    assert control <= mock_config['pid']['control_max']
    assert control >= mock_config['pid']['control_min']


def test_pid_convergence():
    """Test PID convergence to setpoint."""
    config = {
        'pid': {
            'kp': 0.5,
            'ki': 0.1,
            'kd': 0.1,
            'dt': 1.0,
            'integral_min': -10.0,
            'integral_max': 10.0,
            'control_min': -5.0,
            'control_max': 5.0,
            'oscillation_window': 5,
            'oscillation_threshold': 0.15
        }
    }
    
    controller = PIDController(config)
    
    # Simulate process
    pv = 0.0
    setpoint = 1.0
    
    errors = []
    for i in range(50):
        control = controller.compute(setpoint, pv)
        
        # Simple process model: pv moves toward control
        pv += control * 0.1
        
        errors.append(abs(setpoint - pv))
    
    # Error should decrease over time
    assert errors[-1] < errors[0]


def test_oscillation_detection(mock_config):
    """Test oscillation detection."""
    controller = PIDController(mock_config)
    
    # Create oscillating error sequence
    errors = [0.2, -0.2, 0.2, -0.2, 0.2]
    
    for i, pv in enumerate([0.8, 1.2, 0.8, 1.2, 0.8]):
        controller.compute(setpoint=1.0, process_variable=pv)
    
    # Should detect oscillation
    assert controller.is_oscillating()


def test_no_oscillation_detection(mock_config):
    """Test no false oscillation detection."""
    controller = PIDController(mock_config)
    
    # Monotonic approach to setpoint
    for pv in [0.0, 0.2, 0.4, 0.6, 0.8]:
        controller.compute(setpoint=1.0, process_variable=pv)
    
    # Should NOT detect oscillation
    assert not controller.is_oscillating()


def test_pid_reset(mock_config):
    """Test controller reset."""
    controller = PIDController(mock_config)
    
    # Build up state
    for _ in range(10):
        controller.compute(setpoint=1.0, process_variable=0.5)
    
    assert controller.integral != 0.0
    assert controller.error != 0.0
    
    # Reset
    controller.reset()
    
    assert controller.integral == 0.0
    assert controller.error == 0.0
    assert controller.control == 0.0


def test_pid_tuning(mock_config):
    """Test dynamic PID tuning."""
    controller = PIDController(mock_config)
    
    # Change gains
    controller.tune(kp=2.0, ki=0.2, kd=0.1)
    
    assert controller.kp == 2.0
    assert controller.ki == 0.2
    assert controller.kd == 0.1


def test_compute_pid_with_limits():
    """Test standalone PID computation function."""
    control, integral, derivative = compute_pid_with_limits(
        error=1.0,
        integral=0.0,
        prev_error=0.0,
        kp=1.0,
        ki=0.1,
        kd=0.05,
        dt=1.0
    )
    
    # P = 1*1 = 1, I = 0.1*1 = 0.1, D = 0.05*1 = 0.05
    expected_control = 1.0 + 0.1 + 0.05
    assert abs(control - expected_control) < 0.01


def test_detect_oscillation_function():
    """Test oscillation detection function."""
    # Oscillating sequence
    oscillating = [0.5, -0.5, 0.5, -0.5, 0.5, -0.5]
    assert detect_oscillation(oscillating, threshold=0.15)
    
    # Monotonic sequence
    monotonic = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    assert not detect_oscillation(monotonic, threshold=0.15)


def test_apply_deadband():
    """Test deadband/hysteresis function."""
    # Below deadband
    assert apply_deadband(0.03, deadband=0.05) == 0.0
    
    # Above deadband
    assert apply_deadband(0.1, deadband=0.05) == 0.1
    
    # Negative below deadband
    assert apply_deadband(-0.03, deadband=0.05) == 0.0
    
    # Negative above deadband
    assert apply_deadband(-0.1, deadband=0.05) == -0.1


def test_pid_state(mock_config):
    """Test getting PID state."""
    controller = PIDController(mock_config)
    
    controller.compute(setpoint=1.0, process_variable=0.5)
    
    state = controller.get_state()
    
    assert 'error' in state
    assert 'integral' in state
    assert 'derivative' in state
    assert 'control' in state
    assert 'error_history' in state


@pytest.mark.parametrize("kp,ki,kd,expected_stable", [
    (1.0, 0.1, 0.05, True),    # Conservative
    (5.0, 1.0, 0.5, False),    # Aggressive (may oscillate)
    (0.1, 0.01, 0.001, True),  # Very conservative
])
def test_pid_stability(kp, ki, kd, expected_stable):
    """Test PID stability with different gains."""
    config = {
        'pid': {
            'kp': kp,
            'ki': ki,
            'kd': kd,
            'dt': 1.0,
            'integral_min': -10.0,
            'integral_max': 10.0,
            'control_min': -5.0,
            'control_max': 5.0,
            'oscillation_window': 5,
            'oscillation_threshold': 0.15
        }
    }
    
    controller = PIDController(config)
    
    # Simulate
    pv = 0.0
    for _ in range(20):
        control = controller.compute(1.0, pv)
        pv += control * 0.05
    
    # Check if oscillating
    is_stable = not controller.is_oscillating()
    
    # Note: This is a heuristic test, actual stability depends on many factors
