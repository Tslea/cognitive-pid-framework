"""
QA/Integrator Agent

The QA agent validates changes, runs tests, and decides on integration.
Acts as a quality assurance engineer and integration manager.
"""

import json
import logging
import subprocess
from typing import Dict, Any, List


from llm_client import call_llm


def _get_tolerance_instruction(iteration: int, language: str = 'en') -> str:
    """Get adaptive tolerance instruction based on iteration number.
    
    Args:
        iteration: Current iteration number
        language: Language for prompt ('en' or 'it')
        
    Returns:
        Tolerance instruction string
    """
    if language == 'it':
        if iteration <= 5:
            return """
⚠️ IMPORTANTE: Siamo nelle PRIME ITERAZIONI (1-5) di sviluppo iterativo.
- Valuta con TOLLERANZA ALTA: è normale avere setup incompleti
- Score 2.5-4/10 è ACCETTABILE per codice iniziale/setup
- Focus su: struttura base corretta, no errori critici di sintassi
- NON penalizzare: mancanza test completi, implementazione parziale, documentazione minima
- Accetta file anche se solo con struttura base (es. classi vuote con docstring)
"""
        elif iteration <= 15:
            return """
📊 Siamo a MID-DEVELOPMENT (6-15). 
- Valuta con TOLLERANZA MEDIA
- Score 4.5-7/10 è il target
- Richiedi: test base presenti, funzionalità core implementate
- Permetti: refactoring in corso, alcuni test mancanti
"""
        else:
            return """
🎯 Siamo in fase FINALE/POLISH (16+).
- Valuta con STANDARD PROFESSIONALI
- Score 6.5-9/10 richiesto
- Zero tolerance per: bug evidenti, test mancanti, code smell gravi
"""
    else:  # English
        if iteration <= 5:
            return """
⚠️ IMPORTANT: We are in EARLY ITERATIONS (1-5) of iterative development.
- Evaluate with HIGH TOLERANCE: incomplete setup is normal
- Score 2.5-4/10 is ACCEPTABLE for initial code/setup
- Focus on: basic structure correct, no critical syntax errors
- DO NOT penalize: missing complete tests, partial implementation, minimal documentation
- Accept files even if only with basic structure (e.g., empty classes with docstrings)
"""
        elif iteration <= 15:
            return """
📊 We are at MID-DEVELOPMENT (6-15).
- Evaluate with MEDIUM TOLERANCE
- Score 4.5-7/10 is the target
- Require: basic tests present, core functionality implemented
- Allow: ongoing refactoring, some missing tests
"""
        else:
            return """
🎯 We are in FINAL/POLISH phase (16+).
- Evaluate with PROFESSIONAL STANDARDS
- Score 6.5-9/10 required
- Zero tolerance for: obvious bugs, missing tests, serious code smells
"""


# Prompt templates
QA_PROMPT_EN = """You are the QA/Integrator AI, responsible for quality assurance and integration decisions.

{tolerance_instruction}

**Patch to Review:**
{patch_summary}

**Files Modified:**
{files_modified}

**Files Created:**
{files_created}

**Developer's Risk Assessment:**
{risks}

**Developer's Testing Suggestions:**
{testing_suggestions}

**Current Codebase State:**
{codebase_summary}

**Your Responsibilities:**
1. Review the code changes for quality and correctness (with tolerance appropriate to iteration phase)
2. Identify bugs, security issues, and code smells
3. Generate comprehensive test cases
4. Determine if the patch should be merged
5. Provide constructive feedback

**Output Format (JSON):**
{{
  "verdict": "pass|fail",
  "test_cases": [
    {{
      "name": "Test case name",
      "type": "unit|integration|e2e",
      "description": "What this test validates",
      "code": "Executable test code (if applicable)"
    }}
  ],
  "issues": [
    {{
      "severity": "critical|high|medium|low",
      "type": "bug|security|performance|style",
      "description": "Issue description",
      "location": "File and line reference",
      "suggestion": "How to fix"
    }}
  ],
  "test_results": {{
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0
  }},
  "quality_score": 0.0,
  "feedback": "Overall assessment and recommendations"
}}

Generate your QA review as JSON:"""


QA_PROMPT_IT = """Sei il QA/Integrator AI, responsabile del controllo qualità e delle decisioni di integrazione.

{tolerance_instruction}

**Patch da Revisionare:**
{patch_summary}

**File Modificati:**
{files_modified}

**File Creati:**
{files_created}

**Valutazione dei Rischi dello Sviluppatore:**
{risks}

**Suggerimenti di Testing dello Sviluppatore:**
{testing_suggestions}

**Stato Attuale della Codebase:**
{codebase_summary}

**Le Tue Responsabilità:**
1. Rivedere le modifiche al codice per qualità e correttezza (con tolleranza appropriata alla fase)
2. Identificare bug, problemi di sicurezza e code smell
3. Generare casi di test completi
4. Determinare se la patch deve essere unita
5. Fornire feedback costruttivo

**Formato Output (JSON):**
{{
  "verdict": "pass|fail",
  "test_cases": [
    {{
      "name": "Nome del test case",
      "type": "unit|integration|e2e",
      "description": "Cosa questo test valida",
      "code": "Codice di test eseguibile (se applicabile)"
    }}
  ],
  "issues": [
    {{
      "severity": "critical|high|medium|low",
      "type": "bug|security|performance|style",
      "description": "Descrizione del problema",
      "location": "Riferimento file e linea",
      "suggestion": "Come risolvere"
    }}
  ],
  "test_results": {{
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0
  }},
  "quality_score": 0.0,
  "feedback": "Valutazione complessiva e raccomandazioni"
}}

Genera la tua revisione QA come JSON:"""


def call_qa(
    patch: str,
    codebase_path: str,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """Call the QA agent to validate a patch.
    
    Args:
        patch: Unified diff patch to review
        codebase_path: Path to codebase
        params: Agent parameters containing:
            - model_name: LLM model to use
            - temperature: Sampling temperature
            - max_tokens: Maximum tokens
            - language: 'en' or 'it'
            - iteration: Current iteration number (for adaptive tolerance)
            
    Returns:
        Dictionary containing:
            - verdict: 'pass' or 'fail'
            - test_cases: List of test case dictionaries
            - issues: List of issue dictionaries
            - test_results: Dictionary with test statistics
            - quality_score: Quality score (0-1)
            - feedback: Overall feedback
    """
    logger = logging.getLogger(__name__)
    logger.info("QA agent called")
    
    # Select prompt template based on language
    language = params.get('language', 'en')
    iteration = params.get('iteration', 1)
    
    # Get adaptive tolerance instruction
    tolerance_instruction = _get_tolerance_instruction(iteration, language)
    
    prompt_template = QA_PROMPT_IT if language == 'it' else QA_PROMPT_EN
    
    # Extract patch info (passed via context)
    # In real implementation, this would come from developer output
    patch_summary = _summarize_patch(patch)
    
    # Build prompt with adaptive tolerance
    prompt = prompt_template.format(
        tolerance_instruction=tolerance_instruction,
        patch_summary=patch_summary,
        files_modified=params.get('files_modified', []),
        files_created=params.get('files_created', []),
        risks=_format_risks(params.get('risks', [])),
        testing_suggestions=_format_suggestions(params.get('testing_suggestions', [])),
        codebase_summary=_get_codebase_summary(codebase_path)
    )
    
    logger.debug(f"QA prompt length: {len(prompt)} chars (iteration {iteration})")
    
    # Call LLM
    try:
        response = call_llm(
            prompt=prompt,
            model=params.get('model_name', 'gpt-3.5-turbo'),
            temperature=params.get('temperature', 0.3),
            max_tokens=params.get('max_tokens', 2500),
            provider=params.get('provider', 'openai')
        )
        
        logger.debug(f"QA response length: {len(response)} chars")
        
        # Parse JSON response
        output = _parse_qa_output(response)
        
        # Run actual tests if possible
        if codebase_path:
            actual_test_results = _run_tests(codebase_path)
            if actual_test_results:
                output['test_results'] = actual_test_results
        
        logger.info(
            f"QA verdict: {output['verdict']}, "
            f"{len(output['issues'])} issues, "
            f"quality_score: {output['quality_score']:.2f}"
        )
        
        return output
        
    except Exception as e:
        logger.error(f"QA agent failed: {e}", exc_info=True)
        # Return fail verdict on error
        return {
            'verdict': 'fail',
            'test_cases': [],
            'issues': [
                {
                    'severity': 'critical',
                    'type': 'bug',
                    'description': f'QA agent error: {str(e)}',
                    'location': 'N/A',
                    'suggestion': 'Manual review required'
                }
            ],
            'test_results': {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0},
            'quality_score': 0.0,
            'feedback': f'QA failed: {str(e)}'
        }


def _summarize_patch(patch: str, max_lines: int = 50) -> str:
    """Summarize a patch for the prompt.
    
    Args:
        patch: Unified diff patch
        max_lines: Maximum lines to include
        
    Returns:
        Patch summary
    """
    if not patch:
        return "Empty patch - no changes"
    
    lines = patch.split('\n')
    
    if len(lines) <= max_lines:
        return patch
    
    # Truncate and add note
    truncated = '\n'.join(lines[:max_lines])
    return f"{truncated}\n... (patch truncated, {len(lines)} total lines)"


def _format_risks(risks: List[Dict[str, Any]]) -> str:
    """Format risks for prompt.
    
    Args:
        risks: List of risk dictionaries
        
    Returns:
        Formatted string
    """
    if not risks:
        return "No risks identified by developer"
    
    lines = []
    for risk in risks:
        lines.append(
            f"- [{risk.get('severity', 'unknown')}] {risk.get('description', 'N/A')}\n"
            f"  Mitigation: {risk.get('mitigation', 'None specified')}"
        )
    
    return "\n".join(lines)


def _format_suggestions(suggestions: List[str]) -> str:
    """Format testing suggestions for prompt.
    
    Args:
        suggestions: List of suggestion strings
        
    Returns:
        Formatted string
    """
    if not suggestions:
        return "No specific suggestions"
    
    return "\n".join([f"- {s}" for s in suggestions])


def _get_codebase_summary(codebase_path: str) -> str:
    """Get codebase summary.
    
    Args:
        codebase_path: Path to codebase
        
    Returns:
        Summary string
    """
    # Reuse from agent_keeper
    from agent_keeper import _get_codebase_summary
    return _get_codebase_summary(codebase_path)


def _parse_qa_output(response: str) -> Dict[str, Any]:
    """Parse QA LLM response.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Parsed output dictionary
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Try to extract JSON from response
        response_clean = response.strip()
        
        # Remove markdown code blocks if present
        if response_clean.startswith('```'):
            lines = response_clean.split('\n')
            response_clean = '\n'.join(lines[1:-1])
            if response_clean.startswith('json'):
                response_clean = response_clean[4:].strip()
        
        # Find JSON boundaries (handles extra text after JSON)
        json_start = response_clean.find('{')
        if json_start == -1:
            raise ValueError("No JSON object found in response")
        
        # Find matching closing brace
        brace_count = 0
        json_end = -1
        for i, char in enumerate(response_clean[json_start:], start=json_start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break
        
        if json_end == -1:
            raise ValueError("No matching closing brace found")
        
        response_clean = response_clean[json_start:json_end]
        
        # Parse JSON
        output = json.loads(response_clean)
        
        # Validate and set defaults
        if 'verdict' not in output:
            logger.warning("Missing 'verdict' in QA output, defaulting to 'fail'")
            output['verdict'] = 'fail'
        
        # Ensure verdict is valid
        if output['verdict'] not in ['pass', 'fail']:
            output['verdict'] = 'fail'
        
        if 'test_cases' not in output:
            output['test_cases'] = []
        
        if 'issues' not in output:
            output['issues'] = []
        else:
            # Validate issues
            for issue in output['issues']:
                if 'severity' not in issue:
                    issue['severity'] = 'medium'
                if 'type' not in issue:
                    issue['type'] = 'bug'
                if 'description' not in issue:
                    issue['description'] = 'No description'
                if 'location' not in issue:
                    issue['location'] = 'Unknown'
                if 'suggestion' not in issue:
                    issue['suggestion'] = 'No suggestion'
        
        if 'test_results' not in output:
            output['test_results'] = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
        
        if 'quality_score' not in output:
            # Estimate based on issues
            critical_count = sum(1 for i in output['issues'] if i['severity'] == 'critical')
            high_count = sum(1 for i in output['issues'] if i['severity'] == 'high')
            
            if critical_count > 0:
                output['quality_score'] = 0.0
            elif high_count > 2:
                output['quality_score'] = 0.4
            elif output['verdict'] == 'pass':
                output['quality_score'] = 0.8
            else:
                output['quality_score'] = 0.5
        
        if 'feedback' not in output:
            output['feedback'] = 'No feedback provided'
        
        return output
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse QA JSON output: {e}")
        logger.debug(f"Raw response: {response[:500]}")
        
        # Return fail verdict
        return {
            'verdict': 'fail',
            'test_cases': [],
            'issues': [{'severity': 'critical', 'type': 'bug', 'description': f'JSON parse error: {str(e)}', 'location': 'N/A', 'suggestion': 'Manual review'}],
            'test_results': {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0},
            'quality_score': 0.0,
            'feedback': f'Parse error: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Unexpected error parsing QA output: {e}")
        return {
            'verdict': 'fail',
            'test_cases': [],
            'issues': [{'severity': 'critical', 'type': 'bug', 'description': f'Parse error: {str(e)}', 'location': 'N/A', 'suggestion': 'Manual review'}],
            'test_results': {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0},
            'quality_score': 0.0,
            'feedback': f'Error: {str(e)}'
        }


def _run_tests(codebase_path: str) -> Dict[str, int]:
    """Run actual tests on the codebase.
    
    Args:
        codebase_path: Path to codebase
        
    Returns:
        Dictionary with test results or None if tests can't be run
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Try to run pytest
        result = subprocess.run(
            ['pytest', '--tb=short', '--quiet'],
            cwd=codebase_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Parse output
        # pytest output format: "X passed, Y failed in Z.XXs"
        output = result.stdout + result.stderr
        
        passed = 0
        failed = 0
        skipped = 0
        
        # Simple parsing (could be improved)
        if 'passed' in output:
            import re
            match = re.search(r'(\d+) passed', output)
            if match:
                passed = int(match.group(1))
        
        if 'failed' in output:
            import re
            match = re.search(r'(\d+) failed', output)
            if match:
                failed = int(match.group(1))
        
        if 'skipped' in output:
            import re
            match = re.search(r'(\d+) skipped', output)
            if match:
                skipped = int(match.group(1))
        
        total = passed + failed + skipped
        
        logger.info(f"Tests run: {total} total, {passed} passed, {failed} failed, {skipped} skipped")
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped
        }
        
    except subprocess.TimeoutExpired:
        logger.warning("Test execution timeout")
        return None
    except FileNotFoundError:
        logger.debug("pytest not found, skipping test execution")
        return None
    except Exception as e:
        logger.warning(f"Could not run tests: {e}")
        return None
