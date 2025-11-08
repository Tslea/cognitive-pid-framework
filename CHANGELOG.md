# Changelog

All notable changes to the Cognitive PID Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **DeepSeek Integration** - Full support for DeepSeek LLM API
  - Added `deepseek` provider to LLMClient
  - Integrated deepseek-chat and deepseek-coder models
  - Cost tracking for DeepSeek ($0.14/$0.28 per 1M tokens - 100x cheaper than GPT-4)
  - OpenAI-compatible API implementation
  - Comprehensive test suite (`test_deepseek.py`)
  - Complete integration documentation (`DEEPSEEK_INTEGRATION.md`)
- **Progressive QA Thresholds** - Dynamic quality score requirements
  - Iterations 1-5: min_quality_score = 2.5 (tolerant for initial setup)
  - Iterations 6-15: min_quality_score = 4.5 (moderate requirements)
  - Iterations 16+: min_quality_score = 6.5 (strict professional standards)
  - Implemented in `config.yaml` and `main.py`
- **Adaptive Agent Prompts** - Context-aware prompting
  - QA agent adjusts tolerance instructions based on iteration phase
  - Developer agent receives explicit "CRITICAL REQUIREMENTS" for complete code
  - Iteration number passed to all agents via params
- **Robust JSON Parsing** - Improved LLM response parsing
  - Brace-matching algorithm to extract JSON from mixed content
  - Handles extra text before/after JSON in agent responses
  - Applied to Keeper, Developer, and QA agents
  - Significantly reduces parse errors from DeepSeek

### Changed
- **Default LLM Provider** changed from OpenAI to DeepSeek in `config.yaml`
- **Stagnation Window** increased from 5 to 10 iterations (prevents premature stops)
- **Merge Decision Logic** now uses progressive quality thresholds
- Updated `.env.example` with DeepSeek API key placeholder
- Updated README.md with project status disclaimer and known limitations
- Enhanced `llm_client.py` with multi-provider support
- Developer agent now uses `deepseek-coder` (specialized for code generation)

### Improved
- Better cost estimation and tracking across all providers
- Enhanced error messages for missing API keys
- More detailed logging for LLM API calls and decisions
- Quality gate logic more forgiving in early iterations
- JSON extraction more robust against malformed responses
- Early iterations accept incomplete code to allow progressive refinement

### Fixed
- **JSON parsing errors** when LLM adds commentary after JSON object
- **Stagnation detection** triggering too early (increased window 5 → 10)
- **QA agent** rejecting all early-stage code (was too strict)
- **Developer agent** generating incomplete code (improved explicit prompts)
- **Merge decision** using fixed threshold instead of progressive

### Known Issues
- ⚠️ **Patch application** to workspace not fully automated - code generated but not always merged
- ⚠️ **PV calculation** sometimes inaccurate (similarity metrics need tuning)
- ⚠️ **File generation** works but merge logic needs refinement
- ⚠️ **Checkpoint rollback** some edge cases not handled properly
- ⚠️ **Human review** threshold mechanism not implemented
- ⚠️ **Testing coverage** limited for some components

### Planned
- Parallel agent execution for multiple tasks
- Adaptive PID parameter tuning
- Web UI for monitoring
- Database persistence for checkpoints
- Multi-project support
- Ollama integration for local models

## [0.1.0] - 2025-11-08

### Added
- Initial release of Cognitive PID Framework
- Three-agent orchestration system (Keeper, Developer, QA)
- PID feedback controller with anti-windup and oscillation detection
- Measurement system with four quality metrics:
  - Embedding similarity (sentence transformers)
  - Test pass rate (pytest integration)
  - Lint score (flake8 integration)
  - Requirements coverage (keyword matching)
- Checkpoint and rollback system
- Safety guards (budget, stagnation, iteration limits)
- Comprehensive test suite with pytest
- Full documentation:
  - README with quick start guide
  - Architecture documentation
  - PID equations and control theory
  - Prompt templates (English and Italian)
  - Contributing guidelines
- Configuration via YAML
- Logging with rotation
- LLM client supporting OpenAI and Anthropic APIs
- MIT License

### Features
- Automatic code generation from project description
- Quality-driven development with PID control
- Adaptive strategy adjustment based on control value
- Multi-metric quality assessment
- Automated testing and validation
- Checkpoint-based recovery
- Comprehensive error handling

### Technical Details
- Python 3.8+ support
- Type hints throughout codebase
- PEP 8 compliant code style
- 80%+ test coverage
- Modular architecture
- Extensible agent system

---

## Version History

### Version Numbering

- **MAJOR.MINOR.PATCH** format
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Release Process

1. Update version in `src/__init__.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag -a v0.1.0 -m "Release v0.1.0"`
4. Push tag: `git push origin v0.1.0`

---

## Future Roadmap

### v0.2.0 (Planned)
- Enhanced metrics (cyclomatic complexity, maintainability index)
- Git integration for versioning
- Parallel task execution
- Performance optimizations

### v0.3.0 (Planned)
- Web dashboard for monitoring
- Real-time visualization
- Interactive tuning interface
- Project templates

### v1.0.0 (Planned)
- Production-ready stability
- Complete documentation
- Comprehensive examples
- Tutorial videos
- Community plugins

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

---

## Contact

For questions, issues, or suggestions, please:
- Open an issue on GitHub
- Start a discussion in GitHub Discussions
- Check existing documentation

---

**Maintained by the Cognitive PID Framework Team**
