# 🐛 Known Issues & Limitations

**Last Updated:** November 8, 2025

This document tracks known issues, limitations, and areas for improvement in the Cognitive PID Framework.

---

## 🔴 Critical Issues

### 1. Patch Application Not Fully Automated
**Status:** In Progress  
**Impact:** High

**Problem:**
- Developer agent generates code patches successfully
- Patches are not automatically applied to workspace files
- `_apply_patch()` function is a placeholder

**Workaround:**
- Manually copy code from checkpoints to workspace
- Check `checkpoints/checkpoint_iterXXX/codebase/` for generated files

**Fix Needed:**
- Implement proper git-style patch application
- Add file creation/modification logic
- Handle merge conflicts gracefully

---

### 2. PV (Process Variable) Calculation Inaccurate
**Status:** Needs Investigation  
**Impact:** Medium-High

**Problem:**
- Similarity metrics sometimes return unexpected values
- PV can be stuck at low values (e.g., 0.29) even with good code
- sentence-transformers embeddings may not capture code quality well

**Current Formula:**
```python
PV = 0.4 * similarity + 0.3 * test_pass_rate + 0.2 * lint_score + 0.1 * req_coverage
```

**Issues:**
- `similarity` between setpoint and code is hard to measure
- `req_coverage` always 0 (not implemented)
- Weights may not be optimal

**Fix Needed:**
- Rethink similarity calculation (code-specific embeddings?)
- Implement proper requirements coverage tracking
- Tune weights based on empirical data
- Consider alternative PV calculation methods

---

## 🟡 Medium Priority Issues

### 3. Stagnation Detection Too Aggressive
**Status:** Partially Fixed (window increased 5 → 10)  
**Impact:** Medium

**Problem:**
- System stops too early when PV doesn't improve
- May need 20-30 iterations but stops at 10-15

**Workaround:**
- Increase `max_stagnation_iterations` in config.yaml
- Set `--max-iterations` higher

**Further Work:**
- Make stagnation detection smarter (detect trends, not just flat lines)
- Allow "exploration" periods with temporarily lower PV

---

### 4. JSON Parsing Errors
**Status:** Mostly Fixed  
**Impact:** Low (after fix)

**Problem:**
- DeepSeek sometimes adds commentary after JSON
- Causes "Extra data" parse errors

**Fix Applied:**
- Brace-matching algorithm in all agents
- Extracts JSON even with surrounding text

**Remaining:**
- Test with other LLM providers
- Handle nested JSON edge cases

---

### 5. QA Agent Too Strict (Early Iterations)
**Status:** Fixed with Progressive Thresholds  
**Impact:** Low (after fix)

**Problem:**
- QA rejected all code in iterations 1-5
- Expected production-ready code from first iteration

**Fix Applied:**
- Progressive quality thresholds (2.5 → 4.5 → 6.5)
- Adaptive prompt instructions based on iteration

**Monitoring:**
- Verify threshold tuning with real projects
- May need further adjustment

---

## 🟢 Low Priority / Enhancement

### 6. Checkpoint Rollback Edge Cases
**Status:** Needs Testing  
**Impact:** Low

**Problem:**
- Rollback not tested with complex workspace states
- May fail with partial file writes
- No validation after rollback

**Fix Needed:**
- Comprehensive rollback testing
- Add post-rollback validation
- Handle file permission errors

---

### 7. Human Review Not Implemented
**Status:** Placeholder Code  
**Impact:** Low

**Problem:**
- `human_review_threshold` exists but does nothing
- System just logs and continues

**Fix Needed:**
- Implement pause-for-review mechanism
- Add CLI/UI for human intervention
- Track review decisions

---

### 8. Test Coverage Limited
**Status:** Ongoing  
**Impact:** Medium

**Coverage:**
- ✅ DeepSeek integration: 18 tests
- ✅ Basic controller logic: 5 tests
- ⚠️ Agent interactions: minimal
- ❌ End-to-end: none

**Fix Needed:**
- Add integration tests
- Mock LLM responses for faster testing
- Add E2E test with simple project

---

## 📊 Performance Issues

### 9. Slow Execution with DeepSeek
**Status:** Improvement Possible  
**Impact:** Medium

**Problem:**
- 30 iterations can take 30-40 minutes
- Each LLM call has network latency

**Solutions:**
- Use faster providers (Groq: 500+ tok/s)
- Parallel agent execution (future)
- Local models with Ollama

---

### 10. No Progress Visibility
**Status:** Enhancement  
**Impact:** Low

**Problem:**
- Only log files show progress
- No real-time dashboard

**Planned:**
- Web UI for monitoring
- Real-time PV graphs
- Task completion tracker

---

## 🎯 Architectural Limitations

### 11. Single-Threaded Execution
**Status:** By Design (for now)  
**Impact:** Medium

**Limitation:**
- Agents run sequentially
- No parallel task execution

**Future:**
- Parallel developer instances for multiple tasks
- Async agent calls

---

### 12. No Multi-Project Support
**Status:** Not Implemented  
**Impact:** Low

**Limitation:**
- One workspace at a time
- No project isolation

**Future:**
- Multiple workspace management
- Project switching

---

## 📝 Documentation Gaps

### 13. Missing API Documentation
- No docstring standards enforced
- Some functions undocumented
- Type hints incomplete

### 14. Incomplete User Guide
- Advanced configuration not explained
- Troubleshooting section minimal
- No video tutorials

---

## 🚧 How to Report Issues

Found a new issue? Please report it on GitHub:

1. Check if issue already exists
2. Provide minimal reproduction steps
3. Include log snippets (remove API keys!)
4. Specify Python version and OS

---

## 💡 Contributing Fixes

Want to help? Priorities:

1. **High Impact:** Fix patch application (#1)
2. **Medium Impact:** Improve PV calculation (#2)
3. **Easy Wins:** Add more tests (#8)
4. **Polish:** Improve documentation

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
