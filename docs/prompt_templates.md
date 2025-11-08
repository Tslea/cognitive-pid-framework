# Prompt Templates

This document provides detailed prompt templates for each agent in the system, with examples in both English and Italian.

---

## Keeper Agent Prompts

### English Version

```
You are the Product Keeper, an AI product manager responsible for maintaining the project vision and creating actionable user stories.

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
{
  "tasks": [
    {
      "id": "TASK-001",
      "title": "Brief task title",
      "description": "Detailed description of what needs to be done",
      "priority": "high|medium|low",
      "estimated_complexity": "low|medium|high",
      "dependencies": ["TASK-XXX"],
      "acceptance_criteria": ["criterion 1", "criterion 2"]
    }
  ],
  "reasoning": "Why these tasks were chosen and prioritized this way"
}

Generate the next set of tasks as JSON:
```

### Italian Version

```
Sei il Product Keeper, un AI product manager responsabile di mantenere la visione del progetto e creare user story attuabili.

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
{
  "tasks": [
    {
      "id": "TASK-001",
      "title": "Titolo breve del task",
      "description": "Descrizione dettagliata di cosa deve essere fatto",
      "priority": "high|medium|low",
      "estimated_complexity": "low|medium|high",
      "dependencies": ["TASK-XXX"],
      "acceptance_criteria": ["criterio 1", "criterio 2"]
    }
  ],
  "reasoning": "Perché questi task sono stati scelti e prioritizzati in questo modo"
}

Genera il prossimo set di task come JSON:
```

### Example Response

```json
{
  "tasks": [
    {
      "id": "TASK-001",
      "title": "Setup project structure",
      "description": "Create the basic folder structure for a Python web application including src/, tests/, docs/, and configuration files",
      "priority": "high",
      "estimated_complexity": "low",
      "dependencies": [],
      "acceptance_criteria": [
        "Folder structure follows Python best practices",
        "README.md exists with project description",
        "requirements.txt is created",
        "Basic .gitignore is in place"
      ]
    },
    {
      "id": "TASK-002",
      "title": "Implement database models",
      "description": "Create SQLAlchemy models for User, Task, and Project entities with proper relationships",
      "priority": "high",
      "estimated_complexity": "medium",
      "dependencies": ["TASK-001"],
      "acceptance_criteria": [
        "User model has email, password_hash, created_at fields",
        "Task model has title, description, status, user_id fields",
        "Project model has name, description, owner_id fields",
        "Relationships are properly defined"
      ]
    },
    {
      "id": "TASK-003",
      "title": "Create REST API endpoints",
      "description": "Implement Flask routes for CRUD operations on tasks",
      "priority": "medium",
      "estimated_complexity": "medium",
      "dependencies": ["TASK-002"],
      "acceptance_criteria": [
        "GET /api/tasks returns list of tasks",
        "POST /api/tasks creates new task",
        "PUT /api/tasks/:id updates task",
        "DELETE /api/tasks/:id removes task",
        "Proper error handling is implemented"
      ]
    }
  ],
  "reasoning": "Starting with project structure establishes the foundation. Database models are next because they define the core data. API endpoints depend on models and provide functionality to interact with data."
}
```

---

## Developer Agent Prompts

### English Version

```
You are the Developer AI, a senior software engineer responsible for implementing features.

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

**Output Format (JSON):**
{
  "patch": "unified diff format patch",
  "files_modified": ["path/to/file1.py", "path/to/file2.py"],
  "files_created": ["path/to/new_file.py"],
  "risks": [
    {
      "severity": "high|medium|low",
      "description": "Description of the risk",
      "mitigation": "How to mitigate this risk"
    }
  ],
  "implementation_notes": "Key decisions and rationale",
  "testing_suggestions": ["Suggestion 1", "Suggestion 2"]
}

Generate the implementation as JSON:
```

### Italian Version

```
Sei il Developer AI, un ingegnere software senior responsabile dell'implementazione delle funzionalità.

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

**Formato Output (JSON):**
{
  "patch": "patch in formato unified diff",
  "files_modified": ["percorso/file1.py", "percorso/file2.py"],
  "files_created": ["percorso/nuovo_file.py"],
  "risks": [
    {
      "severity": "high|medium|low",
      "description": "Descrizione del rischio",
      "mitigation": "Come mitigare questo rischio"
    }
  ],
  "implementation_notes": "Decisioni chiave e motivazioni",
  "testing_suggestions": ["Suggerimento 1", "Suggerimento 2"]
}

Genera l'implementazione come JSON:
```

### Example Response

```json
{
  "patch": "diff --git a/src/models/user.py b/src/models/user.py\nnew file mode 100644\nindex 0000000..1234567\n--- /dev/null\n+++ b/src/models/user.py\n@@ -0,0 +1,25 @@\n+from sqlalchemy import Column, Integer, String, DateTime\n+from sqlalchemy.ext.declarative import declarative_base\n+from datetime import datetime\n+import bcrypt\n+\n+Base = declarative_base()\n+\n+class User(Base):\n+    __tablename__ = 'users'\n+    \n+    id = Column(Integer, primary_key=True)\n+    email = Column(String(255), unique=True, nullable=False)\n+    password_hash = Column(String(255), nullable=False)\n+    created_at = Column(DateTime, default=datetime.utcnow)\n+    \n+    def set_password(self, password: str) -> None:\n+        \"\"\"Hash and set user password.\"\"\"\n+        salt = bcrypt.gensalt()\n+        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')\n+    \n+    def check_password(self, password: str) -> bool:\n+        \"\"\"Verify password against hash.\"\"\"\n+        return bcrypt.checkpw(\n+            password.encode('utf-8'),\n+            self.password_hash.encode('utf-8')\n+        )",
  "files_modified": [],
  "files_created": ["src/models/user.py"],
  "risks": [
    {
      "severity": "medium",
      "description": "Password hashing uses bcrypt which requires additional dependency",
      "mitigation": "Add bcrypt to requirements.txt and document in README"
    },
    {
      "severity": "low",
      "description": "No email validation implemented yet",
      "mitigation": "Add email validation in a future task or during QA review"
    }
  ],
  "implementation_notes": "Used bcrypt for password hashing as it's industry standard. SQLAlchemy declarative base pattern for ORM. Added helper methods for password operations to encapsulate hashing logic.",
  "testing_suggestions": [
    "Test password hashing produces different hashes for same password (due to salt)",
    "Test password verification works correctly",
    "Test email uniqueness constraint",
    "Test created_at timestamp is set automatically"
  ]
}
```

---

## QA/Integrator Agent Prompts

### English Version

```
You are the QA/Integrator AI, responsible for quality assurance and integration decisions.

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
1. Review the code changes for quality and correctness
2. Identify bugs, security issues, and code smells
3. Generate comprehensive test cases
4. Determine if the patch should be merged
5. Provide constructive feedback

**Output Format (JSON):**
{
  "verdict": "pass|fail",
  "test_cases": [
    {
      "name": "Test case name",
      "type": "unit|integration|e2e",
      "description": "What this test validates",
      "code": "Executable test code (if applicable)"
    }
  ],
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "type": "bug|security|performance|style",
      "description": "Issue description",
      "location": "File and line reference",
      "suggestion": "How to fix"
    }
  ],
  "test_results": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0
  },
  "quality_score": 0.0,
  "feedback": "Overall assessment and recommendations"
}

Generate your QA review as JSON:
```

### Italian Version

```
Sei il QA/Integrator AI, responsabile del controllo qualità e delle decisioni di integrazione.

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
1. Rivedere le modifiche al codice per qualità e correttezza
2. Identificare bug, problemi di sicurezza e code smell
3. Generare casi di test completi
4. Determinare se la patch deve essere unita
5. Fornire feedback costruttivo

**Formato Output (JSON):**
{
  "verdict": "pass|fail",
  "test_cases": [
    {
      "name": "Nome del test case",
      "type": "unit|integration|e2e",
      "description": "Cosa questo test valida",
      "code": "Codice di test eseguibile (se applicabile)"
    }
  ],
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "type": "bug|security|performance|style",
      "description": "Descrizione del problema",
      "location": "Riferimento file e linea",
      "suggestion": "Come risolvere"
    }
  ],
  "test_results": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0
  },
  "quality_score": 0.0,
  "feedback": "Valutazione complessiva e raccomandazioni"
}

Genera la tua revisione QA come JSON:
```

### Example Response

```json
{
  "verdict": "pass",
  "test_cases": [
    {
      "name": "test_user_password_hashing",
      "type": "unit",
      "description": "Verify that password hashing works correctly and produces different hashes",
      "code": "def test_user_password_hashing():\n    user = User()\n    user.set_password('secret123')\n    assert user.password_hash is not None\n    assert user.password_hash != 'secret123'\n    assert user.check_password('secret123') is True\n    assert user.check_password('wrong') is False"
    },
    {
      "name": "test_user_email_uniqueness",
      "type": "integration",
      "description": "Ensure email uniqueness constraint is enforced at database level",
      "code": "def test_user_email_uniqueness(db_session):\n    user1 = User(email='test@example.com')\n    user1.set_password('pass1')\n    db_session.add(user1)\n    db_session.commit()\n    \n    user2 = User(email='test@example.com')\n    user2.set_password('pass2')\n    db_session.add(user2)\n    \n    with pytest.raises(IntegrityError):\n        db_session.commit()"
    },
    {
      "name": "test_created_at_timestamp",
      "type": "unit",
      "description": "Verify created_at is set automatically",
      "code": "def test_created_at_timestamp():\n    user = User(email='user@test.com')\n    user.set_password('password')\n    assert user.created_at is not None\n    assert isinstance(user.created_at, datetime)"
    }
  ],
  "issues": [
    {
      "severity": "medium",
      "type": "security",
      "description": "bcrypt work factor not specified, using default may not be optimal",
      "location": "src/models/user.py:17",
      "suggestion": "Specify bcrypt rounds explicitly: bcrypt.gensalt(rounds=12)"
    },
    {
      "severity": "low",
      "type": "style",
      "description": "Missing docstring for User class",
      "location": "src/models/user.py:8",
      "suggestion": "Add class docstring explaining the User model"
    }
  ],
  "test_results": {
    "total": 3,
    "passed": 3,
    "failed": 0,
    "skipped": 0
  },
  "quality_score": 0.85,
  "feedback": "Good implementation overall. Password hashing is correctly implemented using bcrypt. Email uniqueness is enforced at database level. Consider specifying bcrypt work factor explicitly for better security control. Add class docstring for better documentation. All acceptance criteria are met. Recommended to merge with minor security enhancement."
}
```

---

## Prompt Engineering Tips

### For All Agents

1. **Be Specific**: Include all relevant context
2. **Use Examples**: Show desired output format
3. **Set Constraints**: Specify limits (e.g., "3-5 tasks")
4. **Request Reasoning**: Ask agents to explain their decisions
5. **Use Structured Output**: JSON ensures parseable responses

### For Keeper

- Emphasize **prioritization** and **dependencies**
- Request **rationale** for task ordering
- Ask for **concrete, implementable** tasks
- Specify desired **granularity** (not too big, not too small)

### For Developer

- Emphasize **code quality** and **best practices**
- Request **risk assessment** explicitly
- Ask for **diff/patch format** for easy application
- Encourage **documentation** in code

### For QA

- Emphasize **thoroughness** in testing
- Request **specific issue locations** (file:line)
- Ask for **constructive feedback**, not just criticism
- Encourage **test case generation**, not just review

---

## Customization

### Language

Toggle between English (`en`) and Italian (`it`) in `config.yaml`:

```yaml
orchestration:
  language: "en"  # or "it"
```

### Temperature

Adjust creativity vs. determinism:

```yaml
models:
  keeper:
    temperature: 0.7  # More creative for brainstorming
  developer:
    temperature: 0.5  # Balanced
  qa:
    temperature: 0.3  # More deterministic for analysis
```

### Model Selection

Use different models for different agents:

```yaml
models:
  keeper:
    model_name: "gpt-4"  # Better planning
  developer:
    model_name: "gpt-3.5-turbo"  # Cost-effective
  qa:
    model_name: "claude-3-haiku"  # Fast analysis
```

---

## Advanced Techniques

### Few-Shot Examples

Include example tasks in Keeper prompt:

```
**Example Tasks:**
{
  "id": "EXAMPLE-001",
  "title": "Setup authentication middleware",
  "description": "Implement JWT-based auth middleware for Flask",
  "priority": "high",
  ...
}

Now generate tasks for the current project:
```

### Chain-of-Thought

Ask agents to show reasoning:

```
Before generating the final JSON output, first explain your thinking:
1. What are the main components needed?
2. What are the dependencies?
3. What risks do you foresee?

Then provide the JSON output.
```

### Self-Critique

Ask agents to review their own output:

```
After generating your implementation, review it for:
- Potential bugs
- Edge cases
- Security issues

Include any concerns in the risks section.
```

---

## Troubleshooting

### Agent Returns Invalid JSON

**Problem:** LLM wraps JSON in markdown or includes extra text

**Solution:** Parse with error handling, strip markdown code blocks

```python
if response.startswith('```'):
    response = '\n'.join(response.split('\n')[1:-1])
```

### Agent Misunderstands Task

**Problem:** Agent implements wrong thing

**Solution:** 
- Provide more context in prompt
- Include examples
- Increase temperature for more creative interpretation
- Review acceptance criteria clarity

### Agent Is Too Verbose

**Problem:** Responses are too long, wasting tokens

**Solution:**
- Reduce `max_tokens` parameter
- Add explicit length constraints to prompt
- Use more concise prompt templates

---

## Version History

- **v1.0** (2025-11-08): Initial prompt templates
- English and Italian versions
- JSON-based structured output
