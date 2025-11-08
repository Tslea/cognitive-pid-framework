# Contributing to Cognitive PID Framework

Thank you for your interest in contributing to the Cognitive PID Framework! This document provides guidelines and best practices for contributing to the project.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Adding New Features](#adding-new-features)
- [Tuning PID Parameters](#tuning-pid-parameters)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Expected Behavior

- Be respectful and constructive in all interactions
- Welcome newcomers and help them get started
- Accept constructive criticism gracefully
- Focus on what is best for the community and project

### Unacceptable Behavior

- Harassment, discrimination, or derogatory comments
- Trolling, insulting, or personal attacks
- Publishing others' private information without permission
- Any conduct that would be inappropriate in a professional setting

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of:
  - Python programming
  - AI/LLM concepts
  - Control theory (helpful but not required)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/cognitive-pid-framework.git
   cd cognitive-pid-framework
   ```

3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/cognitive-pid-framework.git
   ```

---

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install development dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest pytest-cov flake8 black mypy
```

### 3. Configure API Keys

```bash
# Copy example environment file
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux

# Edit .env and add your API keys
```

### 4. Run Tests

```bash
pytest
```

---

## Coding Standards

### Style Guide

We follow **PEP 8** - the Python style guide.

#### Key Points

- **Indentation:** 4 spaces (no tabs)
- **Line Length:** Maximum 100 characters
- **Naming:**
  - `snake_case` for functions and variables
  - `PascalCase` for classes
  - `UPPERCASE` for constants
- **Imports:**
  - Standard library first
  - Third-party libraries second
  - Local imports last
  - Alphabetically sorted within each group

#### Example

```python
import logging
import os
from typing import Dict, Any, Optional

import yaml
from dotenv import load_dotenv

from src.controller import PIDController
from src.measure import compute_pv


class MyClass:
    """Class docstring."""
    
    CONSTANT_VALUE = 42
    
    def __init__(self, param: str):
        """Initialize with parameter."""
        self.param = param
    
    def my_method(self, value: int) -> bool:
        """Method docstring.
        
        Args:
            value: Input value
            
        Returns:
            Success status
        """
        return value > 0
```

### Type Hints

Use type hints for all function signatures:

```python
def process_data(data: List[Dict[str, Any]], threshold: float = 0.5) -> Optional[str]:
    """Process data with threshold."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_metric(values: List[float], weights: List[float]) -> float:
    """Calculate weighted metric.
    
    Args:
        values: List of metric values
        weights: List of weights (must sum to 1.0)
        
    Returns:
        Weighted average of values
        
    Raises:
        ValueError: If lengths don't match or weights don't sum to 1
        
    Example:
        >>> calculate_metric([0.8, 0.6], [0.7, 0.3])
        0.74
    """
    ...
```

### Code Formatting

Use **black** for automatic formatting:

```bash
black src/ tests/
```

### Linting

Run **flake8** before committing:

```bash
flake8 src/ tests/
```

### Type Checking

Run **mypy** for type checking:

```bash
mypy src/
```

---

## Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/my-new-feature
# or
git checkout -b fix/bug-description
```

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes

### 2. Make Changes

- Write clean, well-documented code
- Follow coding standards
- Add tests for new functionality
- Update documentation as needed

### 3. Commit Changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "Add oscillation detection to PID controller

- Implement zero-crossing detection
- Add configurable threshold
- Update tests
- Document in pid_equations.md"
```

#### Commit Message Format

```
Short summary (50 chars or less)

More detailed explanation if needed (wrap at 72 chars).
Explain what changed and why, not how (code shows how).

- Bullet points are okay
- Use present tense: "Add feature" not "Added feature"
- Reference issues: "Fixes #123"
```

### 4. Push and Create PR

```bash
git push origin feature/my-new-feature
```

Then create a Pull Request on GitHub with:

- **Title:** Clear description of changes
- **Description:** 
  - What changed
  - Why it changed
  - How to test
  - Related issues

### 5. Review Process

- Address reviewer feedback promptly
- Make requested changes in new commits
- Re-request review after updates
- Maintain respectful, constructive dialogue

### 6. Merge

Once approved:
- Squash commits if requested
- Merge via GitHub interface
- Delete branch after merge

---

## Adding New Features

### Adding a New Agent

1. **Create agent module:** `src/agent_newagent.py`

2. **Implement call function:**

```python
def call_newagent(
    input_data: Dict[str, Any],
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """Call the new agent.
    
    Args:
        input_data: Input data for agent
        params: Agent parameters
        
    Returns:
        Agent output dictionary
    """
    # Implementation
    ...
```

3. **Add prompt template** in `docs/prompt_templates.md`

4. **Update orchestrator** to call new agent

5. **Add tests** in `tests/test_agents.py`

6. **Update documentation:**
   - README.md
   - docs/architecture.md

### Adding a New Metric

1. **Add metric function** to `src/measure.py`:

```python
def compute_new_metric(codebase_path: str) -> float:
    """Compute new quality metric.
    
    Args:
        codebase_path: Path to codebase
        
    Returns:
        Metric value (0-1 scale)
    """
    # Implementation
    ...
```

2. **Update PV computation** in `compute_pv()`:

```python
new_metric = compute_new_metric(codebase_path)
pv = (
    weights['similarity'] * similarity +
    weights['test_pass_rate'] * test_pass_rate +
    weights['lint_score'] * lint_score +
    weights['req_coverage'] * req_coverage +
    weights['new_metric'] * new_metric
)
```

3. **Add weight to config:**

```yaml
metrics:
  weights:
    similarity: 0.3      # Adjusted
    test_pass_rate: 0.3
    lint_score: 0.2
    req_coverage: 0.1
    new_metric: 0.1      # New
```

4. **Add tests** in `tests/test_measure.py`

5. **Document** in README and architecture.md

---

## Tuning PID Parameters

### Understanding the Parameters

- **Kp (Proportional):** Immediate response to error
  - Higher → faster response, may overshoot
  - Lower → slower, more stable

- **Ki (Integral):** Eliminates steady-state error
  - Higher → faster elimination, may oscillate
  - Lower → slower, more stable

- **Kd (Derivative):** Dampens oscillations
  - Higher → reduces overshoot, smooths response
  - Lower → less dampening

### Tuning Process

1. **Start Conservative:**
   ```yaml
   pid:
     kp: 1.0
     ki: 0.1
     kd: 0.05
   ```

2. **Observe Behavior:**
   - Run orchestrator with test project
   - Monitor PV over iterations
   - Check for oscillations

3. **Adjust Kp:**
   - If response too slow → increase Kp
   - If oscillating → decrease Kp

4. **Adjust Ki:**
   - If steady-state error persists → increase Ki
   - If overshooting → decrease Ki

5. **Adjust Kd:**
   - If overshooting → increase Kd
   - If too sluggish → decrease Kd

### Example Tuning Scenarios

**Slow Convergence:**
```yaml
# Before
pid:
  kp: 0.5
  ki: 0.05
  kd: 0.02

# After
pid:
  kp: 1.5  # Increased
  ki: 0.1  # Increased
  kd: 0.05
```

**Oscillating:**
```yaml
# Before
pid:
  kp: 2.0
  ki: 0.5
  kd: 0.01

# After
pid:
  kp: 1.0  # Decreased
  ki: 0.1  # Decreased
  kd: 0.1  # Increased (dampening)
```

### Contributing PID Tuning Improvements

If you find better default parameters:

1. Document test scenario
2. Provide before/after metrics
3. Explain reasoning
4. Submit PR with updated config.yaml

---

## Testing Guidelines

### Test Structure

```
tests/
├── __init__.py
├── test_agents.py        # Agent tests
├── test_controller.py    # PID controller tests
├── test_measure.py       # Metrics tests
└── conftest.py           # Shared fixtures
```

### Writing Tests

#### Unit Tests

Test individual functions in isolation:

```python
def test_compute_test_pass_rate():
    """Test test pass rate computation."""
    result = compute_test_pass_rate({
        'total': 10,
        'passed': 8,
        'failed': 2,
        'skipped': 0
    })
    assert result == 0.8
```

#### Integration Tests

Test component interactions:

```python
@patch('src.agent_keeper.call_llm')
def test_keeper_agent_integration(mock_llm):
    """Test Keeper agent end-to-end."""
    mock_llm.return_value = '{"tasks": [...], "reasoning": "..."}'
    
    result = call_keeper(state, params)
    
    assert 'tasks' in result
    assert len(result['tasks']) > 0
```

#### Test Fixtures

Use pytest fixtures for reusable test data:

```python
@pytest.fixture
def mock_config():
    """Provide mock configuration."""
    return {
        'pid': {'kp': 1.0, 'ki': 0.1, 'kd': 0.05},
        ...
    }

def test_with_config(mock_config):
    """Test using fixture."""
    controller = PIDController(mock_config)
    ...
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_controller.py

# Specific test
pytest tests/test_controller.py::test_pid_initialization

# With coverage
pytest --cov=src --cov-report=html

# Verbose
pytest -v

# Stop on first failure
pytest -x
```

### Test Coverage

Aim for >80% coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

---

## Documentation

### What to Document

- **Code:** Docstrings for all public functions/classes
- **Architecture:** System design decisions
- **API:** How to use the framework
- **Examples:** Usage examples
- **Changes:** Update CHANGELOG.md

### Documentation Files

- **README.md:** Overview, quick start, usage
- **docs/architecture.md:** System architecture
- **docs/pid_equations.md:** PID math and theory
- **docs/prompt_templates.md:** Agent prompts
- **CONTRIBUTING.md:** This file

### Updating Documentation

When adding features:

1. Update relevant .md files
2. Add code examples
3. Update diagrams if needed
4. Run spell check
5. Preview locally before committing

---

## Questions?

- **Issues:** Open an issue on GitHub
- **Discussions:** Use GitHub Discussions
- **Email:** [Provide contact if available]

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Cognitive PID Framework!** 🧠⚙️
