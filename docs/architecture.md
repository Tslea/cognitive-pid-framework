# Architecture Documentation

## Overview

The Cognitive PID Framework implements a revolutionary approach to automated software development by combining:

1. **Multi-agent AI orchestration** (Keeper, Developer, QA)
2. **PID feedback control** (classical control theory)
3. **Continuous quality measurement**
4. **Automated decision-making** with safety guards

This document provides an in-depth explanation of the system architecture, component interactions, and design decisions.

---

## System Architecture

### High-Level Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    USER / OPERATOR                             │
│  Provides: Setpoint (project goal), Configuration             │
└──────────────────────────┬────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│                 ORCHESTRATOR (main.py)                         │
│  • Manages main control loop                                   │
│  • Coordinates agent execution                                 │
│  • Enforces safety guards                                      │
│  • Makes merge/rollback decisions                              │
└──────────────────────────┬────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────────┐
│   KEEPER     │  │  DEVELOPER   │  │   QA/INTEGR     │
│   AGENT      │─▶│    AGENT     │─▶│     AGENT       │
└──────────────┘  └──────────────┘  └─────────────────┘
                                              │
          ┌───────────────────────────────────┴──────────┐
          ▼                                              ▼
┌────────────────────┐                        ┌──────────────────┐
│ MEASUREMENT        │                        │  CHECKPOINT      │
│ SYSTEM             │                        │  SYSTEM          │
│ (measure.py)       │                        │ (checkpoint.py)  │
│                    │                        │                  │
│ • Similarity       │                        │ • Snapshots      │
│ • Test pass rate   │                        │ • Rollback       │
│ • Lint score       │                        │ • Best state     │
│ • Req coverage     │                        │                  │
│                    │                        │                  │
│ → PV (0-1 scale)   │                        │                  │
└────────────────────┘                        └──────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────────────┐
│                 PID CONTROLLER (controller.py)                  │
│                                                                 │
│  e(t) = SP - PV(t)                    [Error]                  │
│  I(t) = I(t-1) + e(t)·Δt  (clamped)   [Integral]               │
│  D(t) = (e(t) - e(t-1)) / Δt          [Derivative]             │
│  u(t) = Kp·e(t) + Ki·I(t) + Kd·D(t)   [Control]                │
│                                                                 │
│  Features:                                                      │
│  • Anti-windup (integral clamping)                             │
│  • Derivative filtering (low-pass)                             │
│  • Oscillation detection (zero-crossing)                       │
│  • Control limits                                              │
└────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Orchestrator (`main.py`)

**Responsibilities:**
- Initialize system components
- Execute main control loop
- Coordinate agent calls in sequence
- Collect measurements and compute PV
- Invoke PID controller
- Make decisions (merge, rollback, human review)
- Enforce safety guards
- Manage checkpoints

**Control Loop Flow:**

```python
while iteration < max_iterations:
    # 1. Get tasks from Keeper
    tasks = keeper_agent(state)
    
    # 2. Implement task with Developer
    patch = developer_agent(task, codebase)
    
    # 3. Validate with QA
    qa_result = qa_agent(patch, codebase)
    
    # 4. Measure quality (PV)
    pv = measure_system(codebase, tests)
    
    # 5. Compute control
    control = pid_controller(setpoint, pv)
    
    # 6. Adjust strategies
    adjust_agent_params(control)
    
    # 7. Decide action
    if qa_passes and pv_acceptable:
        merge(patch)
    elif pv_too_low:
        rollback()
    
    # 8. Safety checks
    if stagnant or over_budget:
        break
```

### 2. Agent System

#### Keeper Agent (`agent_keeper.py`)

**Role:** Product Owner / Vision Keeper

**Inputs:**
- Project setpoint (goal description)
- Completed tasks
- Current codebase state

**Outputs:**
- List of prioritized user stories/tasks
- Task dependencies
- Acceptance criteria
- Reasoning for prioritization

**Prompt Strategy:**
- Maintains big-picture vision
- Breaks down high-level goals
- Considers dependencies
- Prioritizes by value and risk

#### Developer Agent (`agent_developer.py`)

**Role:** Senior Software Engineer

**Inputs:**
- Task specification
- Current codebase
- Acceptance criteria

**Outputs:**
- Code patch (unified diff)
- Files modified/created
- Risk assessment
- Implementation notes
- Testing suggestions

**Prompt Strategy:**
- Focuses on clean, maintainable code
- Identifies potential risks
- Suggests testing approach
- Documents decisions

#### QA/Integrator Agent (`agent_qa.py`)

**Role:** Quality Assurance Engineer + Integration Manager

**Inputs:**
- Code patch
- Developer's risk assessment
- Current codebase

**Outputs:**
- Pass/fail verdict
- Test cases generated
- Issues found (bugs, security, performance)
- Quality score
- Integration feedback

**Prompt Strategy:**
- Reviews for correctness
- Identifies edge cases
- Generates comprehensive tests
- Assesses security and performance

### 3. PID Controller (`controller.py`)

**Purpose:** Maintain software quality at target setpoint through feedback control

**Mathematical Model:**

```
Error:       e(t) = SP - PV(t)
Integral:    I(t) = I(t-1) + e(t)·Δt
Derivative:  D(t) = (e(t) - e(t-1)) / Δt
Control:     u(t) = Kp·e(t) + Ki·I(t) + Kd·D(t)
```

**Control Terms:**

1. **Proportional (Kp·e)**
   - Immediate response to current error
   - Higher Kp → faster response, but can overshoot
   - Example: If quality is low, increase effort proportionally

2. **Integral (Ki·I)**
   - Eliminates steady-state error
   - Accumulates past errors
   - Higher Ki → eliminates persistent error, but can cause instability
   - **Anti-windup:** Clamp integral to prevent runaway

3. **Derivative (Kd·D)**
   - Predicts future error trend
   - Dampens oscillations
   - Higher Kd → reduces overshoot, but sensitive to noise
   - **Filtering:** Low-pass filter to reduce noise sensitivity

**Features:**

- **Anti-windup:** Prevents integral term from growing unbounded
- **Derivative filtering:** Smooths noisy error signals
- **Oscillation detection:** Monitors zero-crossings in error signal
- **Control clamping:** Limits control output to safe range

**Strategy Adjustment:**

Based on control value `u(t)`:

```python
if u > 2.0:  # Quality too low
    decrease_developer_temperature()  # More conservative code
    increase_qa_frequency()           # More testing
elif u < -2.0:  # Quality too high (over-engineering)
    increase_developer_temperature()  # More creative
    decrease_qa_frequency()           # Less overhead
```

### 4. Measurement System (`measure.py`)

**Purpose:** Compute Process Variable (PV) - current quality metric

**PV Formula:**

```
PV = w₁·similarity + w₂·test_pass_rate + w₃·lint_score + w₄·req_coverage
```

Default weights: `[0.4, 0.3, 0.2, 0.1]`

**Metrics:**

1. **Embedding Similarity** (0-1)
   - Uses sentence transformers to encode setpoint and codebase
   - Cosine similarity between embeddings
   - Measures: "Is the code aligned with the vision?"

2. **Test Pass Rate** (0-1)
   - Ratio: passed_tests / total_tests
   - Measures: "Does the code work?"

3. **Lint Score** (0-1)
   - Based on flake8 output
   - Formula: `max(0, 1 - issues_per_file/10)`
   - Measures: "Is the code clean?"

4. **Requirements Coverage** (0-1)
   - Keyword matching between setpoint and codebase
   - Measures: "Are requirements implemented?"

**PV Range:** Always normalized to [0, 1]

### 5. Checkpoint System (`checkpoint.py`)

**Purpose:** Snapshot codebase for recovery and tracking best states

**Features:**

1. **Filesystem Checkpoints**
   - Copy entire codebase to checkpoint directory
   - Include metadata (iteration, PV, timestamp)
   - Track best checkpoint

2. **Git Checkpoints** (alternative)
   - Create git commits with tags
   - Lightweight and integrated with version control

3. **Rollback**
   - Restore codebase from any checkpoint
   - Automatic rollback when PV drops too low

4. **Cleanup**
   - Remove old checkpoints (keep best + recent N)

---

## Control Flow Diagram

```
START
  │
  ▼
Initialize(config, setpoint)
  │
  ▼
┌─────────────────────────┐
│   ITERATION LOOP        │◄───────────────┐
│   (until converge or    │                │
│    max iterations)      │                │
└─────────┬───────────────┘                │
          │                                │
          ▼                                │
    ┌─────────────┐                        │
    │ KEEPER      │                        │
    │ Generate    │                        │
    │ Tasks       │                        │
    └──────┬──────┘                        │
           │                               │
           ▼                               │
    ┌─────────────┐                        │
    │ DEVELOPER   │                        │
    │ Implement   │                        │
    │ Task        │                        │
    └──────┬──────┘                        │
           │                               │
           ▼                               │
    ┌─────────────┐                        │
    │ QA          │                        │
    │ Validate &  │                        │
    │ Test        │                        │
    └──────┬──────┘                        │
           │                               │
           ▼                               │
    ┌─────────────┐                        │
    │ MEASURE     │                        │
    │ Compute PV  │                        │
    └──────┬──────┘                        │
           │                               │
           ▼                               │
    ┌─────────────┐                        │
    │ PID         │                        │
    │ Compute     │                        │
    │ Control     │                        │
    └──────┬──────┘                        │
           │                               │
           ▼                               │
    ┌─────────────┐                        │
    │ ADJUST      │                        │
    │ Strategies  │                        │
    └──────┬──────┘                        │
           │                               │
           ▼                               │
    ┌─────────────┐                        │
    │ DECISION    │                        │
    │ Merge/      │                        │
    │ Rollback    │                        │
    └──────┬──────┘                        │
           │                               │
           ▼                               │
    ┌─────────────┐                        │
    │ SAFETY      │                        │
    │ CHECKS      │                        │
    └──────┬──────┘                        │
           │                               │
           ├─ Continue? ───────────────────┘
           │
           ▼ No
    ┌─────────────┐
    │ FINALIZE    │
    │ Report      │
    │ Results     │
    └──────┬──────┘
           │
           ▼
         END
```

---

## Safety Mechanisms

### 1. Budget Limits
- Track API costs
- Stop if budget exceeded
- Configurable limit (e.g., $10)

### 2. Stagnation Detection
- Monitor PV improvement over window
- Stop if no progress for N iterations
- Configurable threshold

### 3. Oscillation Detection
- Count zero-crossings in error signal
- Detect if system is unstable
- Trigger parameter adjustment or human review

### 4. Human Review Triggers
- PV below critical threshold
- Too many rollbacks
- Persistent issues

### 5. Rollback Logic
- Automatic rollback if PV drops significantly
- Restore to best known state
- Continue from checkpoint

### 6. Iteration Limits
- Maximum iterations enforced
- Prevents infinite loops

---

## Design Decisions

### Why Three Agents?

1. **Separation of Concerns**
   - Each agent has distinct expertise
   - Mimics real development teams

2. **Quality Control**
   - QA agent provides independent validation
   - Prevents Keeper and Developer from agreeing on poor solutions

3. **Flexibility**
   - Can use different models for each role
   - Can adjust parameters independently

### Why PID Control?

1. **Proven Methodology**
   - PID has decades of success in process control
   - Well-understood tuning methods

2. **Adaptive Behavior**
   - Automatically adjusts to changing conditions
   - No manual intervention needed

3. **Stability Guarantees**
   - Anti-windup prevents runaway
   - Oscillation detection ensures stability

4. **Interpretability**
   - Control value has clear meaning
   - Easy to debug and tune

### Why Multiple Metrics for PV?

1. **Holistic Quality**
   - Single metric can be gamed
   - Multiple metrics capture different aspects

2. **Balance Trade-offs**
   - Code can be clean but not functional
   - Tests can pass but miss requirements

3. **Weighted Priorities**
   - Adjust weights based on project needs
   - Flexibility for different contexts

---

## Extensibility

### Adding New Agents

1. Create new agent module (e.g., `agent_security.py`)
2. Implement `call_security(...)` function
3. Add to orchestration sequence
4. Update PV metrics if needed

### Custom Metrics

1. Add metric function to `measure.py`
2. Update PV formula with new weight
3. Configure weight in `config.yaml`

### Alternative Controllers

1. Implement new controller (e.g., `adaptive_controller.py`)
2. Replace PIDController in orchestrator
3. Maintain same interface: `compute(setpoint, pv)`

---

## Performance Considerations

### LLM API Costs

- Use cheaper models (gpt-3.5-turbo, claude-haiku)
- Cache repetitive prompts
- Batch operations where possible

### Checkpoint Storage

- Checkpoints can be large
- Implement cleanup policy
- Consider git-based checkpoints

### Measurement Speed

- Embedding computation can be slow
- Cache embeddings for unchanged files
- Use lightweight models

---

## Future Enhancements

1. **Parallel Agent Execution**
   - Run multiple developers on different tasks
   - Merge changes incrementally

2. **Reinforcement Learning**
   - Learn optimal PID parameters
   - Adapt to project characteristics

3. **Multi-Objective Optimization**
   - Pareto frontier for competing metrics
   - User preference learning

4. **Continuous Integration**
   - Integrate with CI/CD pipelines
   - Automatic deployment

5. **Human-in-the-Loop**
   - Interactive task prioritization
   - Approval gates for critical changes

---

## Conclusion

The Cognitive PID Framework represents a novel approach to automated software development by treating it as a control problem. By combining AI agents with classical control theory, the system achieves:

- **Autonomous operation** with minimal human intervention
- **Quality convergence** toward target metrics
- **Safety** through multiple guard mechanisms
- **Adaptability** to changing project needs

The architecture is modular, extensible, and grounded in proven engineering principles.
