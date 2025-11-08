# 🧠 Cognitive PID Framework

> *Autonomous AI-driven software development using PID feedback control*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status: Experimental](https://img.shields.io/badge/Status-Experimental-orange.svg)](https://github.com)

## ⚠️ **Project Status: Experimental / Work in Progress**

**This project is in active development and NOT production-ready.**

### Known Limitations:
- 🔧 **Patch application not fully implemented** - code generation works but automatic merging needs work
- 🎯 **Quality metrics need tuning** - PV calculations sometimes inaccurate
- 📊 **Stagnation detection too aggressive** - may stop prematurely
- 🧪 **Limited testing coverage** - more edge cases need handling
- 📝 **Documentation incomplete** - some features undocumented

### What Works:
- ✅ DeepSeek API integration (cost-effective LLM)
- ✅ Three-agent orchestration (Keeper, Developer, QA)
- ✅ PID controller with adaptive thresholds
- ✅ Progressive quality gates (tolerant early, strict later)
- ✅ Checkpoint and rollback system
- ✅ Comprehensive logging and metrics

**Contributions welcome!** See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 🎯 Elevator Pitch

**Transform software development into a self-correcting, autonomous process where three specialized AI agents collaborate under PID control to incrementally build applications that converge toward your vision.**

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution Overview](#-solution-overview)
- [Architecture](#-architecture)
- [Technical Stack](#-technical-stack)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 Problem Statement

Traditional software development faces critical challenges:

- **Manual iteration cycles** are slow and expensive
- **Quality feedback loops** are disconnected from development
- **AI code generation** lacks coherent direction and quality control
- **Incremental improvement** requires constant human supervision

**What if we could automate the entire develop-test-refine cycle with intelligent feedback control?**

---

## 💡 Solution Overview

The **Cognitive PID Framework** implements a revolutionary three-agent AI orchestration system that:

1. **Keeper Agent**: Maintains product vision and generates prioritized user stories
2. **Developer Agent**: Implements features as code patches with risk assessment
3. **QA/Integrator Agent**: Validates changes, runs tests, and decides on integration

An **orchestrator** manages the control loop:
- Measures alignment to quality setpoint (target metrics)
- Computes PID control parameters (Proportional, Integral, Derivative)
- Adjusts agent strategies dynamically
- Enforces safety guards (budget, stagnation, rollback)
- Auto-merges validated changes

### Key Innovation: PID Feedback Control

By treating software quality as a **process variable (PV)** and applying classical control theory, the system:
- **Converges toward quality targets** automatically
- **Detects and corrects drift** in real-time
- **Prevents oscillation** and instability
- **Optimizes resource usage** adaptively

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator (main.py)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ PID Controller (controller.py)                         │ │
│  │  • Compute error: e(t) = SP - PV(t)                    │ │
│  │  • Update integral (with anti-windup)                  │ │
│  │  • Compute derivative                                  │ │
│  │  • Control: u(t) = Kp·e + Ki·I + Kd·D                  │ │
│  │  • Detect oscillation & apply hysteresis               │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   Keeper     │  │  Developer   │  │   QA/Integr  │
    │   Agent      │─▶│    Agent     │─▶│     Agent    │
    │              │  │              │  │              │
    │ • Vision     │  │ • Code gen   │  │ • Testing    │
    │ • Stories    │  │ • Patches    │  │ • Validation │
    │ • Priorities │  │ • Risk list  │  │ • Pass/Fail  │
    └──────────────┘  └──────────────┘  └──────────────┘
                                                │
                    ┌───────────────────────────┘
                    ▼
        ┌───────────────────────┐
        │  Measurement System   │
        │   (measure.py)        │
        │                       │
        │ PV = 0.4·similarity + │
        │      0.3·test_rate  + │
        │      0.2·lint       + │
        │      0.1·req_cov      │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Checkpoint & Rollback │
        │   (checkpoint.py)     │
        │                       │
        │ • Snapshot codebase   │
        │ • Track best state    │
        │ • Rollback on failure │
        └───────────────────────┘
```

### Control Flow

1. **Initialize**: Load config, setpoint, create workspace
2. **Loop** (until convergence or max iterations):
   - Keeper generates next task
   - Developer implements task as patch
   - QA validates and tests patch
   - Measure PV (quality metrics)
   - Compute PID control value
   - Adjust strategies based on control
   - Safety checks (budget, stagnation)
   - Merge or rollback
   - Checkpoint if needed
3. **Finalize**: Report results, save best state

---

## 🛠️ Technical Stack

- **Language**: Python 3.8+
- **LLM APIs**: DeepSeek (default), OpenAI, Anthropic (configurable)
  - **DeepSeek**: Cost-effective ($0.14/$0.28 per 1M tokens) with specialized code model
  - **Models**: deepseek-chat, deepseek-coder
- **Version Control**: GitPython for automated commits/rollbacks
- **Testing**: pytest with coverage reporting
- **Code Quality**: flake8 for linting
- **Embeddings**: sentence-transformers for semantic similarity
- **Configuration**: YAML-based config management
- **Logging**: Structured logging with rotation

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Git installed
- DeepSeek API key (get free at [platform.deepseek.com](https://platform.deepseek.com))
- OpenAI or Anthropic API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/cognitive-pid-framework.git
   cd cognitive-pid-framework
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys**
   ```bash
   # Copy environment template
   copy .env.example .env  # Windows
   # cp .env.example .env  # macOS/Linux
   
   # Edit .env and add your API keys
   ```

5. **Review configuration** (optional)
   ```bash
   # Edit config.yaml to adjust PID parameters, models, etc.
   ```

### First Run

```bash
python src/main.py --setpoint "Create a simple calculator web app" --max-iterations 20
```

---

## 📖 Usage

### Basic Usage

```bash
python src/main.py --setpoint "Your project description" [options]
```

### Options

- `--setpoint TEXT`: Project description/goal (required)
- `--max-iterations N`: Maximum loop iterations (default: from config)
- `--config PATH`: Path to config file (default: config.yaml)
- `--workspace PATH`: Workspace directory (default: ./workspace)
- `--checkpoint-dir PATH`: Checkpoint storage (default: ./checkpoints)
- `--log-level LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Example: Web Application

```bash
python src/main.py \
  --setpoint "Build a REST API for task management with user auth" \
  --max-iterations 30 \
  --log-level INFO
```

### Example: Data Pipeline

```bash
python src/main.py \
  --setpoint "Create ETL pipeline to process CSV files and load to SQLite" \
  --max-iterations 25
```

### Monitoring Progress

Logs are saved to `./logs/` with timestamps. Monitor in real-time:

```bash
tail -f logs/orchestrator_YYYYMMDD_HHMMSS.log
```

### Viewing Results

After completion, check:
- `workspace/`: Final codebase
- `checkpoints/`: Saved snapshots
- `logs/`: Detailed execution logs with PV history

---

## ⚙️ Configuration

Edit `config.yaml` to customize:

### PID Tuning

```yaml
pid:
  kp: 1.0   # Increase for faster response to errors
  ki: 0.1   # Increase to eliminate steady-state error
  kd: 0.05  # Increase to reduce overshoot
  setpoint: 0.85  # Target quality (0-1)
```

### Model Selection

```yaml
models:
  keeper:
    model_name: "gpt-4"  # Upgrade for better planning
  developer:
    temperature: 0.3     # Lower for more deterministic code
```

### Safety Limits

```yaml
safety:
  max_iterations: 50
  max_budget_usd: 10.0
  stagnation_window: 5
```

---

## 📚 Documentation

- [Architecture Details](docs/architecture.md) - In-depth system design
- [PID Equations](docs/pid_equations.md) - Mathematical foundations
- [Prompt Templates](docs/prompt_templates.md) - Agent prompt examples
- [Contributing Guide](CONTRIBUTING.md) - Development guidelines

---

## 🧪 Testing

Run the test suite:

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_controller.py -v
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Code style guidelines (PEP 8)
- How to add new agents
- PID tuning best practices
- Submitting pull requests

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by classical control theory and modern AI orchestration
- Built on top of excellent open-source LLM APIs
- Community-driven development

---

## 📬 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/cognitive-pid-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cognitive-pid-framework/discussions)

---

**Made with 🧠 and ⚙️ by the Cognitive PID Framework Team**
