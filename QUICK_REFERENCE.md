# Quick Reference Guide

## Installation & Setup

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux
# Edit .env and add your keys

# 4. Run tests
pytest
```

## Basic Usage

```bash
# Run orchestrator
python src/main.py --setpoint "Build a REST API for task management" --max-iterations 20

# With custom config
python src/main.py --setpoint "Create a calculator app" --config my_config.yaml --max-iterations 30

# With custom workspace
python src/main.py --setpoint "Build web scraper" --workspace ./my_project --log-level DEBUG
```

## Configuration Quick Reference

### PID Parameters (config.yaml)

```yaml
pid:
  kp: 1.0      # Proportional gain (response speed)
  ki: 0.1      # Integral gain (eliminate steady-state error)
  kd: 0.05     # Derivative gain (dampen oscillations)
  setpoint: 0.85  # Target quality (0-1)
```

**Tuning Tips:**
- **Slow convergence?** Increase `kp` and `ki`
- **Oscillating?** Decrease `kp` and `ki`, increase `kd`
- **Overshooting?** Increase `kd`

### Model Configuration

```yaml
models:
  keeper:
    model_name: "gpt-3.5-turbo"  # or "gpt-4"
    temperature: 0.7             # Higher = more creative
  developer:
    model_name: "gpt-3.5-turbo"
    temperature: 0.5
  qa:
    model_name: "gpt-3.5-turbo"
    temperature: 0.3             # Lower = more deterministic
```

### Metric Weights

```yaml
metrics:
  weights:
    similarity: 0.4      # Code matches vision
    test_pass_rate: 0.3  # Tests pass
    lint_score: 0.2      # Code quality
    req_coverage: 0.1    # Requirements met
```

### Safety Guards

```yaml
safety:
  max_iterations: 50              # Stop after N iterations
  stagnation_threshold: 0.01      # Min improvement required
  stagnation_window: 5            # Iterations without improvement
  max_budget_usd: 10.0            # API cost limit
  human_review_threshold: 0.3     # PV triggers review
  rollback_threshold: 0.5         # PV triggers rollback
```

## Python API

### Using as Library

```python
from src.main import CognitivePIDOrchestrator

# Create orchestrator
orchestrator = CognitivePIDOrchestrator('config.yaml')

# Run
results = orchestrator.run(
    setpoint="Build a web application",
    max_iterations=20
)

print(f"Best PV: {results['best_pv']}")
print(f"Final PV: {results['final_pv']}")
```

### Custom PID Controller

```python
from src.controller import PIDController

config = {
    'pid': {
        'kp': 1.0, 'ki': 0.1, 'kd': 0.05,
        'dt': 1.0,
        'integral_min': -10, 'integral_max': 10,
        'control_min': -5, 'control_max': 5,
        'oscillation_window': 5,
        'oscillation_threshold': 0.15
    }
}

controller = PIDController(config)

# Compute control
control = controller.compute(setpoint=0.85, process_variable=0.60)
```

### Custom Metrics

```python
from src.measure import compute_pv

config = {
    'metrics': {
        'weights': {
            'similarity': 0.4,
            'test_pass_rate': 0.3,
            'lint_score': 0.2,
            'req_coverage': 0.1
        }
    }
}

pv = compute_pv(
    setpoint="Build calculator",
    codebase_path="./workspace",
    test_results={'total': 10, 'passed': 8, 'failed': 2, 'skipped': 0},
    config=config
)
```

## Testing

```bash
# All tests
pytest

# Specific test file
pytest tests/test_controller.py

# Specific test
pytest tests/test_controller.py::test_pid_initialization

# With coverage
pytest --cov=src --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Debugging

### Enable Debug Logging

```bash
python src/main.py --setpoint "..." --log-level DEBUG
```

Or in `config.yaml`:
```yaml
orchestration:
  log_level: "DEBUG"
```

### Check Logs

```bash
# Latest log
ls logs/ | sort | tail -1

# View log
cat logs/orchestrator_YYYYMMDD_HHMMSS.log

# Watch in real-time (Windows)
Get-Content logs/orchestrator_*.log -Wait -Tail 50

# Watch in real-time (Linux/macOS)
tail -f logs/orchestrator_*.log
```

### Iteration History

```bash
# View iteration details (JSONL format)
cat logs/iterations.jsonl | jq '.'
```

## Common Issues

### "OPENAI_API_KEY not found"

**Solution:** Edit `.env` and add your API key:
```
OPENAI_API_KEY=sk-your-key-here
```

### "sentence-transformers not installed"

**Solution:** Install dependencies:
```bash
pip install sentence-transformers
```

### Tests fail with API errors

**Solution:** Tests that call actual APIs are expected to fail without keys. Use `pytest -k "not integration"` to skip integration tests.

### PID oscillating

**Solution:** Reduce gains in `config.yaml`:
```yaml
pid:
  kp: 0.5  # Reduce from 1.0
  ki: 0.05 # Reduce from 0.1
```

## File Locations

| Purpose | Location |
|---------|----------|
| Main script | `src/main.py` |
| Configuration | `config.yaml` |
| API keys | `.env` |
| Logs | `logs/` |
| Checkpoints | `checkpoints/` |
| Generated code | `workspace/` |
| Documentation | `docs/` |

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...
# Or
ANTHROPIC_API_KEY=sk-ant-...

# Optional
CONFIG_PATH=./config.yaml
LOG_LEVEL=DEBUG
```

## Command-Line Arguments

```
--setpoint TEXT          Project description (required)
--max-iterations N       Maximum iterations
--config PATH            Config file path
--workspace PATH         Workspace directory
--checkpoint-dir PATH    Checkpoint directory
--log-level LEVEL        DEBUG|INFO|WARNING|ERROR
```

## Monitoring Progress

Watch PV improvement:
```bash
# Extract PV values from logs
grep "PV =" logs/orchestrator_*.log

# Plot with Python
python -c "
import json
with open('logs/iterations.jsonl') as f:
    pvs = [json.loads(line)['pv'] for line in f]
    print(pvs)
"
```

## Best Practices

1. **Start Small:** Test with simple projects first
2. **Monitor Costs:** Set reasonable `max_budget_usd`
3. **Tune Conservatively:** Start with default PID parameters
4. **Review Logs:** Check logs after each run
5. **Use Checkpoints:** Enable frequent checkpoints
6. **Iterate:** Adjust based on results

## Support

- **Documentation:** See `docs/` directory
- **Examples:** Check `README.md`
- **Issues:** Open on GitHub
- **Contributing:** See `CONTRIBUTING.md`

## Quick Links

- [README](README.md) - Overview and quick start
- [Architecture](docs/architecture.md) - System design
- [PID Equations](docs/pid_equations.md) - Control theory
- [Prompts](docs/prompt_templates.md) - Agent templates
- [Contributing](CONTRIBUTING.md) - Development guide

---

**Need help?** Check the documentation or open an issue!
