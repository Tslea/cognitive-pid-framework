# PID Control Equations

## Mathematical Foundation

This document provides the mathematical foundations of the PID controller used in the Cognitive PID Framework.

---

## Continuous-Time PID Equation

In continuous time, a PID controller is defined as:

$$
u(t) = K_p e(t) + K_i \int_0^t e(\tau) \, d\tau + K_d \frac{de(t)}{dt}
$$

Where:
- $u(t)$ = control output at time $t$
- $e(t)$ = error at time $t$ = setpoint - process variable
- $K_p$ = proportional gain
- $K_i$ = integral gain
- $K_d$ = derivative gain

---

## Discrete-Time PID Equation

For implementation in software, we use discrete-time approximations with time step $\Delta t$:

### Error

$$
e(t) = SP - PV(t)
$$

Where:
- $SP$ = setpoint (target quality, typically 0.85)
- $PV(t)$ = process variable (current quality metric)

### Integral Term (with Anti-Windup)

$$
I(t) = I(t-1) + e(t) \cdot \Delta t
$$

With clamping:

$$
I(t) = \begin{cases}
I_{max} & \text{if } I(t) > I_{max} \\
I_{min} & \text{if } I(t) < I_{min} \\
I(t) & \text{otherwise}
\end{cases}
$$

Default limits: $I_{min} = -10$, $I_{max} = 10$

### Derivative Term (with Filtering)

Raw derivative:

$$
D_{raw}(t) = \frac{e(t) - e(t-1)}{\Delta t}
$$

Filtered derivative (low-pass filter):

$$
D(t) = \alpha \cdot D_{raw}(t) + (1 - \alpha) \cdot D(t-1)
$$

Where $\alpha$ is the filter coefficient (typically 0.1).

### Control Output

$$
u(t) = K_p \cdot e(t) + K_i \cdot I(t) + K_d \cdot D(t)
$$

With clamping:

$$
u(t) = \begin{cases}
u_{max} & \text{if } u(t) > u_{max} \\
u_{min} & \text{if } u(t) < u_{min} \\
u(t) & \text{otherwise}
\end{cases}
$$

Default limits: $u_{min} = -5$, $u_{max} = 5$

---

## Component Analysis

### Proportional Term: $K_p \cdot e(t)$

**Purpose:** Provide immediate response proportional to current error

**Characteristics:**
- Larger $K_p$ → faster response
- Too large → overshoot, instability
- Zero steady-state error only if $e(t) = 0$

**Effect on System:**
- Positive error (PV < SP) → positive control → increase effort
- Negative error (PV > SP) → negative control → reduce effort

**Tuning:**
- Start with $K_p = 1.0$
- Increase if response is too slow
- Decrease if oscillations occur

### Integral Term: $K_i \cdot I(t)$

**Purpose:** Eliminate steady-state error

**Characteristics:**
- Accumulates past errors
- Forces long-term error to zero
- Can cause overshoot and instability

**Effect on System:**
- Persistent low quality → integral grows → sustained high effort
- Quality reaches setpoint → integral stops growing

**Tuning:**
- Start with $K_i = 0.1$
- Increase to eliminate steady-state error faster
- Decrease if overshoot is excessive

**Anti-Windup:**

Problem: If error is large for extended time, integral term can grow unbounded ("windup"), causing massive overshoot.

Solution: Clamp integral between $I_{min}$ and $I_{max}$

$$
I(t) = \max(I_{min}, \min(I_{max}, I(t)))
$$

### Derivative Term: $K_d \cdot D(t)$

**Purpose:** Predict future error and dampen oscillations

**Characteristics:**
- Responds to rate of change of error
- Provides "look-ahead" control
- Sensitive to noise in measurement

**Effect on System:**
- Rapid quality improvement → derivative negative → reduce effort
- Rapid quality degradation → derivative positive → increase effort

**Tuning:**
- Start with $K_d = 0.05$
- Increase to reduce overshoot
- Decrease if system is too sluggish

**Derivative Filtering:**

Problem: Derivative of noisy signal is very noisy.

Solution: Apply low-pass filter

$$
D(t) = \alpha \cdot D_{raw}(t) + (1 - \alpha) \cdot D(t-1)
$$

Where $\alpha \in [0, 1]$ controls filtering strength (lower = more filtering).

---

## Advanced Features

### Oscillation Detection

Detect if the system is oscillating by counting zero-crossings in the error signal.

**Algorithm:**

1. Maintain window of recent errors: $[e(t-n), ..., e(t-1), e(t)]$
2. Count sign changes (zero-crossings):

$$
\text{crossings} = \sum_{i=1}^{n} \mathbb{1}[e(t-i) \cdot e(t-i+1) < 0]
$$

3. If crossings $\geq n/2$ and error amplitude $> \theta$, oscillation detected

**Parameters:**
- Window size: $n = 5$
- Amplitude threshold: $\theta = 0.15$

**Action:**
- Log warning
- Optionally reduce $K_p$ and $K_i$
- May trigger human review

### Hysteresis (Deadband)

To reduce chattering when error is small, apply deadband:

$$
u_{hyst}(t) = \begin{cases}
0 & \text{if } |u(t)| < \epsilon \\
u(t) & \text{otherwise}
\end{cases}
$$

Default: $\epsilon = 0.05$

---

## Tuning Methods

### Ziegler-Nichols Method (Open-Loop)

1. Set $K_i = 0$, $K_d = 0$
2. Increase $K_p$ until system oscillates with period $T_u$
3. Record ultimate gain $K_u$
4. Set:
   - $K_p = 0.6 K_u$
   - $K_i = 1.2 K_u / T_u$
   - $K_d = 0.075 K_u T_u$

### Manual Tuning

1. Start with $K_p = 1.0$, $K_i = 0$, $K_d = 0$
2. Increase $K_p$ until response is fast but not oscillating
3. Add $K_i$ to eliminate steady-state error
4. Add $K_d$ to reduce overshoot

### Adaptive Tuning

Adjust gains based on system behavior:

```python
if oscillating:
    K_p *= 0.9  # Reduce proportional gain
    K_i *= 0.9  # Reduce integral gain
elif stagnant:
    K_p *= 1.1  # Increase proportional gain
```

---

## Transfer Function

In the Laplace domain, the PID controller has transfer function:

$$
C(s) = K_p + \frac{K_i}{s} + K_d s
$$

For a plant with transfer function $G(s)$, the closed-loop transfer function is:

$$
\frac{Y(s)}{R(s)} = \frac{C(s)G(s)}{1 + C(s)G(s)}
$$

**Stability Analysis:**

For stability, all poles of closed-loop transfer function must have negative real parts (Routh-Hurwitz criterion).

---

## Practical Considerations

### Time Step Selection

$\Delta t$ should be small enough to capture dynamics but not so small as to amplify noise.

**Recommendation:** $\Delta t = 1$ (one iteration)

### Initial Conditions

Start with:
- $I(0) = 0$ (no accumulated error)
- $e(-1) = 0$ (no previous error)
- $D(0) = 0$ (no initial derivative)

### Setpoint Changes

When setpoint changes abruptly:
- Error jumps → large proportional response
- Derivative spike → can cause control spike
- Consider ramping setpoint gradually

---

## Example Calculation

**Given:**
- $SP = 0.85$ (target quality)
- $PV(t) = 0.60$ (current quality)
- $PV(t-1) = 0.55$
- $I(t-1) = 0.5$
- $\Delta t = 1.0$
- $K_p = 1.0$, $K_i = 0.1$, $K_d = 0.05$
- $\alpha = 0.1$ (filter coefficient)
- $D(t-1) = 0.1$

**Step 1: Compute error**

$$
e(t) = 0.85 - 0.60 = 0.25
$$

$$
e(t-1) = 0.85 - 0.55 = 0.30
$$

**Step 2: Update integral**

$$
I(t) = 0.5 + 0.25 \cdot 1.0 = 0.75
$$

(No clamping needed if $|0.75| < 10$)

**Step 3: Compute derivative**

Raw:
$$
D_{raw}(t) = \frac{0.25 - 0.30}{1.0} = -0.05
$$

Filtered:
$$
D(t) = 0.1 \cdot (-0.05) + 0.9 \cdot 0.1 = -0.005 + 0.09 = 0.085
$$

**Step 4: Compute control**

$$
u(t) = 1.0 \cdot 0.25 + 0.1 \cdot 0.75 + 0.05 \cdot 0.085
$$

$$
u(t) = 0.25 + 0.075 + 0.00425 = 0.32925
$$

(No clamping needed if $|0.329| < 5$)

**Interpretation:**
- Positive control $u(t) = 0.329$ suggests increasing effort (quality below target)
- Moderate value suggests system is responding appropriately

---

## References

1. Åström, K. J., & Hägglund, T. (1995). *PID Controllers: Theory, Design, and Tuning*. ISA.
2. Franklin, G. F., Powell, J. D., & Emami-Naeini, A. (2015). *Feedback Control of Dynamic Systems*. Pearson.
3. Ziegler, J. G., & Nichols, N. B. (1942). "Optimum Settings for Automatic Controllers". *Transactions of the ASME*, 64(11).

---

## Appendix: Python Implementation

```python
class PIDController:
    def __init__(self, kp, ki, kd, dt=1.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.dt = dt
        
        self.integral = 0.0
        self.prev_error = 0.0
        self.derivative = 0.0
        
    def compute(self, setpoint, pv):
        # Error
        error = setpoint - pv
        
        # Integral with anti-windup
        self.integral += error * self.dt
        self.integral = max(-10, min(10, self.integral))
        
        # Derivative with filtering
        raw_deriv = (error - self.prev_error) / self.dt
        self.derivative = 0.1 * raw_deriv + 0.9 * self.derivative
        
        # Control
        control = self.kp * error + self.ki * self.integral + self.kd * self.derivative
        control = max(-5, min(5, control))
        
        # Update
        self.prev_error = error
        
        return control
```
