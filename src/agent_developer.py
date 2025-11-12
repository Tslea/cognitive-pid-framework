"""
Developer Agent

The Developer agent implements features as code patches with risk assessment.
Acts as a senior developer who writes clean, tested code.
"""

import json
import logging
import os
from typing import Dict, Any, List


from llm_client import call_llm


# Prompt templates
DEVELOPER_PROMPT_EN = """You are the Developer AI, a senior software engineer responsible for implementing features.

**Task to Implement:**
ID: {task_id}
Title: {task_title}
Description: {task_description}
Priority: {task_priority}
Complexity: {task_complexity}

**Acceptance Criteria:**
{acceptance_criteria}

**Current Codebase:**
{codebase_files}

**Your Responsibilities:**
1. Analyze the task and plan the implementation
2. Write clean, maintainable, well-documented code
3. Follow best practices and coding standards
4. Identify potential risks and edge cases
5. Generate a unified diff/patch that can be applied

⚠️ **CRITICAL REQUIREMENTS - CODE QUALITY STANDARDS:**
- Write COMPLETE, FUNCTIONAL code - NOT just stubs, placeholders, or TODOs
- Every file must contain FULL implementation with working logic
- Include proper error handling, validation, and edge case management
- Add comprehensive docstrings (Google or NumPy style) and inline comments where needed
- Minimum 50 lines of actual code for main implementation files
- DO NOT create empty files or files with just "pass" statements
- Every function/method must have a real implementation - NO placeholder code
- Include type hints throughout the code (Python 3.8+ style)
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Write self-documenting code with clear logic flow
- Include input validation and error messages
- Handle edge cases and provide meaningful error messages
- DO NOT write code that just raises NotImplementedError or contains "TODO" comments
- Ensure code is production-ready, not experimental or incomplete

**Output Format (JSON):**
{{
  "patch": "unified diff format patch OR complete file content",
  "files_modified": ["path/to/file1.py", "path/to/file2.py"],
  "files_created": ["path/to/new_file.py"],
  "risks": [
    {{
      "severity": "high|medium|low",
      "description": "Description of the risk",
      "mitigation": "How to mitigate this risk"
    }}
  ],
  "implementation_notes": "Key decisions and rationale",
  "testing_suggestions": ["Suggestion 1", "Suggestion 2"]
}}

**IMPORTANT - Patch Format:**
- For NEW files: Include COMPLETE file content in the patch (not just diff)
- Use unified diff format: start with "--- /dev/null" and "+++ path/to/new_file.py"
- Include ALL code lines with "+" prefix (added lines)
- For existing files: Use proper unified diff with context lines
- Ensure the patch contains the FULL implementation, not just snippets
- Example for new file:
  --- /dev/null
  +++ path/to/new_file.py
  @@ -0,0 +1,50 @@
  +[complete file content here, each line prefixed with +]

Generate the implementation as JSON:"""


DEVELOPER_PROMPT_IT = """Sei il Developer AI, un ingegnere software senior responsabile dell'implementazione delle funzionalità.

**Task da Implementare:**
ID: {task_id}
Titolo: {task_title}
Descrizione: {task_description}
Priorità: {task_priority}
Complessità: {task_complexity}

**Criteri di Accettazione:**
{acceptance_criteria}

**Codebase Attuale:**
{codebase_files}

**Le Tue Responsabilità:**
1. Analizzare il task e pianificare l'implementazione
2. Scrivere codice pulito, manutenibile e ben documentato
3. Seguire le best practice e gli standard di codifica
4. Identificare potenziali rischi e casi limite
5. Generare una patch in formato diff unificato che può essere applicata

⚠️ **REQUISITI CRITICI - STANDARD DI QUALITÀ DEL CODICE:**
- Scrivi codice COMPLETO e FUNZIONANTE - NON solo stub, placeholder o TODO
- Ogni file deve contenere implementazione COMPLETA con logica funzionante
- Includi gestione errori, validazione e gestione casi limite
- Aggiungi docstring complete (stile Google o NumPy) e commenti inline dove necessario
- Minimo 50 righe di codice reale per file di implementazione principali
- NON creare file vuoti o file con solo "pass"
- Ogni funzione/metodo deve avere implementazione reale - NO codice placeholder
- Includi type hints in tutto il codice (stile Python 3.8+)
- Segui le linee guida PEP 8
- Usa nomi di variabili e funzioni significativi
- Scrivi codice auto-documentante con logica chiara
- Includi validazione degli input e messaggi di errore
- Gestisci casi limite e fornisci messaggi di errore significativi
- NON scrivere codice che solleva solo NotImplementedError o contiene commenti "TODO"
- Assicurati che il codice sia pronto per la produzione, non sperimentale o incompleto

**Formato Output (JSON):**
{{
  "patch": "patch in formato unified diff O contenuto completo del file",
  "files_modified": ["percorso/file1.py", "percorso/file2.py"],
  "files_created": ["percorso/nuovo_file.py"],
  "risks": [
    {{
      "severity": "high|medium|low",
      "description": "Descrizione del rischio",
      "mitigation": "Come mitigare questo rischio"
    }}
  ],
  "implementation_notes": "Decisioni chiave e motivazioni",
  "testing_suggestions": ["Suggerimento 1", "Suggerimento 2"]
}}

**IMPORTANTE - Formato Patch:**
- Per file NUOVI: Includi il CONTENUTO COMPLETO del file nella patch (non solo il diff)
- Usa formato unified diff: inizia con "--- /dev/null" e "+++ percorso/nuovo_file.py"
- Includi TUTTE le righe di codice con prefisso "+" (righe aggiunte)
- Per file esistenti: Usa unified diff corretto con righe di contesto
- Assicurati che la patch contenga l'implementazione COMPLETA, non solo frammenti
- Esempio per file nuovo:
  --- /dev/null
  +++ percorso/nuovo_file.py
  @@ -0,0 +1,50 @@
  +[contenuto completo del file qui, ogni riga con prefisso +]

Genera l'implementazione come JSON:"""


def call_developer(
    task: Dict[str, Any],
    codebase_path: str,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """Call the Developer agent to implement a task.
    
    Args:
        task: Task dictionary with:
            - id: Task ID
            - title: Task title
            - description: Detailed description
            - priority: Priority level
            - estimated_complexity: Complexity estimate
            - acceptance_criteria: List of criteria
        codebase_path: Path to codebase
        params: Agent parameters containing:
            - model_name: LLM model to use
            - temperature: Sampling temperature
            - max_tokens: Maximum tokens
            - language: 'en' or 'it'
            
    Returns:
        Dictionary containing:
            - patch: Unified diff patch
            - files_modified: List of modified file paths
            - files_created: List of created file paths
            - risks: List of risk dictionaries
            - implementation_notes: Implementation notes
            - testing_suggestions: List of testing suggestions
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Developer agent called for task: {task.get('id', 'N/A')}")
    
    # Select prompt template based on language
    language = params.get('language', 'en')
    prompt_template = DEVELOPER_PROMPT_IT if language == 'it' else DEVELOPER_PROMPT_EN
    
    # Prepare context
    acceptance_criteria = _format_acceptance_criteria(task.get('acceptance_criteria', []))
    codebase_files = _get_codebase_files(codebase_path)
    
    # Build prompt
    prompt = prompt_template.format(
        task_id=task.get('id', 'N/A'),
        task_title=task.get('title', 'Untitled'),
        task_description=task.get('description', 'No description'),
        task_priority=task.get('priority', 'medium'),
        task_complexity=task.get('estimated_complexity', 'medium'),
        acceptance_criteria=acceptance_criteria,
        codebase_files=codebase_files
    )
    
    logger.debug(f"Developer prompt length: {len(prompt)} chars")
    
    # Call LLM
    try:
        response = call_llm(
            prompt=prompt,
            model=params.get('model_name', 'gpt-3.5-turbo'),
            temperature=params.get('temperature', 0.5),
            max_tokens=params.get('max_tokens', 3000),
            provider=params.get('provider', 'openai')
        )
        
        logger.debug(f"Developer response length: {len(response)} chars")
        
        # Parse JSON response
        output = _parse_developer_output(response)
        
        logger.info(
            f"Developer generated patch: "
            f"{len(output['files_modified'])} modified, "
            f"{len(output['files_created'])} created, "
            f"{len(output['risks'])} risks"
        )
        
        return output
        
    except Exception as e:
        logger.error(f"Developer agent failed: {e}", exc_info=True)
        # Return empty patch on failure
        return {
            'patch': '',
            'files_modified': [],
            'files_created': [],
            'risks': [{'severity': 'high', 'description': f'Error: {str(e)}', 'mitigation': 'Manual review required'}],
            'implementation_notes': f'Failed: {str(e)}',
            'testing_suggestions': []
        }


def _format_acceptance_criteria(criteria: List[str]) -> str:
    """Format acceptance criteria for prompt.
    
    Args:
        criteria: List of criteria strings
        
    Returns:
        Formatted string
    """
    if not criteria:
        return "None specified"
    
    return "\n".join([f"- {c}" for c in criteria])


def _get_codebase_files(codebase_path: str, max_files: int = 20) -> str:
    """Get listing of codebase files.
    
    Args:
        codebase_path: Path to codebase
        max_files: Maximum number of files to include
        
    Returns:
        Formatted file listing
    """
    if not os.path.exists(codebase_path):
        return "Empty - no codebase exists yet. You're starting from scratch."
    
    try:
        files = []
        for root, dirs, filenames in os.walk(codebase_path):
            # Skip hidden and common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]
            
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                
                filepath = os.path.join(root, filename)
                relpath = os.path.relpath(filepath, codebase_path)
                
                # Get file size
                size = os.path.getsize(filepath)
                files.append((relpath, size))
        
        # Sort by path
        files.sort()
        
        # Limit number of files
        if len(files) > max_files:
            files = files[:max_files]
            truncated = True
        else:
            truncated = False
        
        # Format output
        lines = [f"- {path} ({size} bytes)" for path, size in files]
        
        if truncated:
            lines.append(f"... and {len(files) - max_files} more files")
        
        return "\n".join(lines) if lines else "Empty directory"
        
    except Exception as e:
        return f"Error reading codebase: {e}"


def _parse_developer_output(response: str) -> Dict[str, Any]:
    """Parse Developer LLM response.
    
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
        if 'patch' not in output:
            logger.warning("Missing 'patch' in Developer output")
            output['patch'] = ''
        
        if 'files_modified' not in output:
            output['files_modified'] = []
        
        if 'files_created' not in output:
            output['files_created'] = []
        
        if 'risks' not in output:
            output['risks'] = []
        else:
            # Validate risks
            for risk in output['risks']:
                if 'severity' not in risk:
                    risk['severity'] = 'medium'
                if 'description' not in risk:
                    risk['description'] = 'No description'
                if 'mitigation' not in risk:
                    risk['mitigation'] = 'No mitigation specified'
        
        if 'implementation_notes' not in output:
            output['implementation_notes'] = 'No notes provided'
        
        if 'testing_suggestions' not in output:
            output['testing_suggestions'] = []
        
        return output
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Developer JSON output: {e}")
        logger.debug(f"Raw response: {response[:500]}")
        
        # Return fallback
        return {
            'patch': '',
            'files_modified': [],
            'files_created': [],
            'risks': [{'severity': 'high', 'description': f'JSON parse error: {str(e)}', 'mitigation': 'Manual review'}],
            'implementation_notes': f'Parse error: {str(e)}',
            'testing_suggestions': []
        }
    except Exception as e:
        logger.error(f"Unexpected error parsing Developer output: {e}")
        return {
            'patch': '',
            'files_modified': [],
            'files_created': [],
            'risks': [{'severity': 'high', 'description': f'Parse error: {str(e)}', 'mitigation': 'Manual review'}],
            'implementation_notes': f'Error: {str(e)}',
            'testing_suggestions': []
        }


def estimate_patch_impact(patch: str) -> Dict[str, int]:
    """Estimate the impact of a patch.
    
    Args:
        patch: Unified diff patch
        
    Returns:
        Dictionary with impact metrics
    """
    lines = patch.split('\n')
    
    additions = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
    
    return {
        'additions': additions,
        'deletions': deletions,
        'net_change': additions - deletions,
        'total_changes': additions + deletions
    }
