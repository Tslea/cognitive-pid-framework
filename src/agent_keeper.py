"""
Keeper Agent

The Keeper agent maintains product vision and generates prioritized user stories.
Acts as the product owner, understanding requirements and breaking them into tasks.
"""

import json
import logging
from typing import Dict, Any, List
import os

from llm_client import call_llm


# Prompt templates
KEEPER_PROMPT_EN = """You are the Product Keeper, an AI product manager responsible for maintaining the project vision and creating actionable user stories.

**Project Goal:**
{setpoint}

**Current Iteration:** {iteration}

**Completed Tasks:**
{completed_tasks}

**Current Codebase State:**
{codebase_summary}

**Your Responsibilities:**
1. Understand the overall project vision
2. Break down the goal into concrete, implementable user stories
3. Prioritize tasks based on dependencies and value
4. Generate 3-5 user stories for the next iteration

**Output Format (JSON):**
{{
  "tasks": [
    {{
      "id": "TASK-001",
      "title": "Brief task title",
      "description": "Detailed description of what needs to be done",
      "priority": "high|medium|low",
      "estimated_complexity": "low|medium|high",
      "dependencies": ["TASK-XXX"],
      "acceptance_criteria": ["criterion 1", "criterion 2"]
    }}
  ],
  "reasoning": "Why these tasks were chosen and prioritized this way"
}}

Generate the next set of tasks as JSON:"""


KEEPER_PROMPT_IT = """Sei il Product Keeper, un AI product manager responsabile di mantenere la visione del progetto e creare user story attuabili.

**Obiettivo del Progetto:**
{setpoint}

**Iterazione Corrente:** {iteration}

**Task Completati:**
{completed_tasks}

**Stato Attuale della Codebase:**
{codebase_summary}

**Le Tue Responsabilità:**
1. Comprendere la visione complessiva del progetto
2. Suddividere l'obiettivo in user story concrete e implementabili
3. Dare priorità ai task in base a dipendenze e valore
4. Generare 3-5 user story per la prossima iterazione

**Formato Output (JSON):**
{{
  "tasks": [
    {{
      "id": "TASK-001",
      "title": "Titolo breve del task",
      "description": "Descrizione dettagliata di cosa deve essere fatto",
      "priority": "high|medium|low",
      "estimated_complexity": "low|medium|high",
      "dependencies": ["TASK-XXX"],
      "acceptance_criteria": ["criterio 1", "criterio 2"]
    }}
  ],
  "reasoning": "Perché questi task sono stati scelti e prioritizzati in questo modo"
}}

Genera il prossimo set di task come JSON:"""


def call_keeper(state: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """Call the Keeper agent to generate user stories.
    
    Args:
        state: Current system state containing:
            - setpoint: Project goal
            - iteration: Current iteration number
            - completed_tasks: List of completed tasks
            - codebase_path: Path to codebase
        params: Agent parameters containing:
            - model_name: LLM model to use
            - temperature: Sampling temperature
            - max_tokens: Maximum tokens
            - language: 'en' or 'it'
            
    Returns:
        Dictionary containing:
            - tasks: List of task dictionaries
            - reasoning: Explanation of prioritization
    """
    logger = logging.getLogger(__name__)
    logger.info("Keeper agent called")
    
    # Select prompt template based on language
    language = params.get('language', 'en')
    prompt_template = KEEPER_PROMPT_IT if language == 'it' else KEEPER_PROMPT_EN
    
    # Prepare context
    completed_summary = _format_completed_tasks(state.get('completed_tasks', []))
    codebase_summary = _get_codebase_summary(state.get('codebase_path', ''))
    
    # Build prompt
    prompt = prompt_template.format(
        setpoint=state['setpoint'],
        iteration=state.get('iteration', 0),
        completed_tasks=completed_summary,
        codebase_summary=codebase_summary
    )
    
    logger.debug(f"Keeper prompt length: {len(prompt)} chars")
    
    # Call LLM
    try:
        response = call_llm(
            prompt=prompt,
            model=params.get('model_name', 'gpt-3.5-turbo'),
            temperature=params.get('temperature', 0.7),
            max_tokens=params.get('max_tokens', 2000),
            provider=params.get('provider', 'openai')
        )
        
        logger.debug(f"Keeper response length: {len(response)} chars")
        
        # Parse JSON response
        output = _parse_keeper_output(response)
        
        logger.info(f"Keeper generated {len(output['tasks'])} tasks")
        
        return output
        
    except Exception as e:
        logger.error(f"Keeper agent failed: {e}", exc_info=True)
        # Return empty task list on failure
        return {
            'tasks': [],
            'reasoning': f'Error: {str(e)}'
        }


def _format_completed_tasks(completed_tasks: List[Dict[str, Any]]) -> str:
    """Format completed tasks for prompt.
    
    Args:
        completed_tasks: List of completed task dictionaries
        
    Returns:
        Formatted string
    """
    if not completed_tasks:
        return "None yet - this is the first iteration."
    
    lines = []
    for task in completed_tasks:
        lines.append(f"- [{task.get('id', 'N/A')}] {task.get('title', 'Untitled')}")
    
    return "\n".join(lines)


def _get_codebase_summary(codebase_path: str) -> str:
    """Get summary of current codebase.
    
    Args:
        codebase_path: Path to codebase directory
        
    Returns:
        Summary string
    """
    if not os.path.exists(codebase_path):
        return "Empty - no codebase exists yet."
    
    try:
        # Count files by extension
        file_counts = {}
        total_lines = 0
        
        for root, dirs, files in os.walk(codebase_path):
            # Skip hidden and common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                ext = os.path.splitext(file)[1] or 'no_ext'
                file_counts[ext] = file_counts.get(ext, 0) + 1
                
                # Count lines
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        total_lines += sum(1 for _ in f)
                except (IOError, OSError, UnicodeDecodeError):
                    # Skip files that can't be read
                    pass
        
        summary_parts = [f"Total files: {sum(file_counts.values())}", f"Total lines: {total_lines}"]
        
        if file_counts:
            file_list = ", ".join([f"{count} {ext}" for ext, count in sorted(file_counts.items())])
            summary_parts.append(f"Files by type: {file_list}")
        
        return " | ".join(summary_parts)
        
    except Exception as e:
        return f"Error reading codebase: {e}"


def _parse_keeper_output(response: str) -> Dict[str, Any]:
    """Parse Keeper LLM response.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Parsed output dictionary
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Try to extract JSON from response
        # Sometimes LLMs wrap JSON in markdown code blocks
        response_clean = response.strip()
        
        # Remove markdown code blocks if present
        if response_clean.startswith('```'):
            lines = response_clean.split('\n')
            # Remove first and last lines (``` markers)
            response_clean = '\n'.join(lines[1:-1])
            # Remove json language marker if present
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
        
        # Validate structure
        if 'tasks' not in output:
            logger.warning("Missing 'tasks' in Keeper output, creating empty list")
            output['tasks'] = []
        
        if 'reasoning' not in output:
            output['reasoning'] = 'No reasoning provided'
        
        # Validate each task
        for task in output['tasks']:
            if 'id' not in task:
                task['id'] = f"TASK-{hash(task.get('title', 'untitled')) % 10000:04d}"
            if 'title' not in task:
                task['title'] = 'Untitled task'
            if 'description' not in task:
                task['description'] = ''
            if 'priority' not in task:
                task['priority'] = 'medium'
            if 'estimated_complexity' not in task:
                task['estimated_complexity'] = 'medium'
            if 'dependencies' not in task:
                task['dependencies'] = []
            if 'acceptance_criteria' not in task:
                task['acceptance_criteria'] = []
        
        return output
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Keeper JSON output: {e}")
        logger.debug(f"Raw response: {response[:500]}")
        
        # Return fallback
        return {
            'tasks': [],
            'reasoning': f'JSON parse error: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Unexpected error parsing Keeper output: {e}")
        return {
            'tasks': [],
            'reasoning': f'Parse error: {str(e)}'
        }


def validate_task(task: Dict[str, Any]) -> bool:
    """Validate a task dictionary.
    
    Args:
        task: Task dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['id', 'title', 'description']
    return all(field in task for field in required_fields)
