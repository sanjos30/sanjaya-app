# Sanjaya Autopilot — Implementation Design Document

**Last Updated**: December 2024  
**Version**: v0.6 (Project Questionnaire System)

This document tracks the current implementation state of the Sanjaya Autopilot platform, including what has been built, how it works, and what remains to be implemented.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current Implementation Status](#current-implementation-status)
3. [Project Questionnaire System](#project-questionnaire-system)
4. [API Endpoints](#api-endpoints)
5. [Agent Implementations](#agent-implementations)
6. [File Structure & Conventions](#file-structure--conventions)
7. [Path Handling](#path-handling)
8. [Data Models](#data-models)
9. [Workflow Flow](#workflow-flow)
10. [What's Working](#whats-working)
11. [What's Stubbed](#whats-stubbed)
12. [Usage Examples](#usage-examples)
13. [Golden Path: example-project Reference Implementation](#golden-path-example-project-reference-implementation)

---

## Project Overview

Sanjaya Autopilot is a **multi-agent, multi-project, stack-agnostic SDLC and operations assistant** that operates under strict human-in-the-loop (HITL) principles.

**Core Philosophy**: "Sanjaya proposes → YOU approve"

- All changes go through Pull Request workflow
- Human approval required for all operations
- Document-driven feature development
- Project isolation and stack-agnostic design

---

## Current Implementation Status

### ✅ Implemented (v0.3)

1. **API Service** (`autopilot_core/main_service/api.py`)
   - FastAPI service with multiple endpoints
   - Request/Response models using Pydantic
   - Error handling with HTTPException
   - Project registration endpoint

2. **OrchestratorAgent** (`agents/orchestrator/orchestrator_agent.py`)
   - Loads project configurations (GitHub repos or local paths)
   - Validates design contract files
   - Runs codegen/tests/PR flow when requested (flags on `/workflows/run`)
   - Generates workflow IDs
   - Works with both remote and local projects

3. **ProductAgent** (`agents/product/product_agent.py`)
   - Creates feature design contracts from structured input (v0)
   - **NEW**: LLM-powered feature contract generation from simple ideas
   - Slugifies feature names for filesystem safety
   - Writes markdown files with comprehensive template
   - Works with GitHub repos and local paths
   - Supports OpenAI and Anthropic LLM providers

4. **CodegenAgent** (`agents/codegen/codegen_agent.py`)
   - Parses design contracts (lightweight markdown parsing)
   - LLM-driven for all stacks (Python/FastAPI, Node/Next.js, PHP, etc.)
   - Stack-aware file naming (API routes/handlers/tests)
   - Prompts include stack/runtime/dirs from `autopilot.yaml`
   - Writes deterministic scaffolds for known stacks when files are missing:
     - FastAPI: `app/main.py` (with `/health` endpoint), `app/api/routes.py`, `app/core/config.py`, `app/core/db.py`, `requirements.txt`, `.env.example`, `tests/test_health.py`
     - Next.js: `package.json`, `next.config.mjs`, `tsconfig.json`, `app/page.tsx`, `app/api/health/route.ts` (or `pages/api/health.ts`), `.env.local.example`, sample frontend test
     - PHP: `public/index.php` (with `/health` handler), `src/config.php`, `src/db/mysql.php`, `src/db/mongo.php`, `composer.json`, `.env.example`, `tests/phpunit.xml`, `tests/HealthTest.php`
   - Writes code + tests via RepoClient
   - Respects dry-run (skips generation)

5. **BugfixAgent** (`agents/bugfix/bugfix_agent.py`) - NEW
   - LLM-powered bugfix suggestions for test failures
   - Analyzes test output (stdout, stderr, exit code)
   - Generates unified diff patches
   - Provides retry commands and explanatory notes
   - Called automatically by Orchestrator when tests fail and `run_bugfix=true`
   - Patches are returned in workflow response (not auto-applied)

6. **GovernanceAgent** (`agents/governance/governance_agent.py`) - NEW
   - Rule-based policy enforcement
   - Checks forbidden paths (e.g., `.env`, secrets)
   - Requires tests for code changes (configurable)
   - Validates allowed dependencies (if configured)
   - Evaluates diffs before PR creation
   - Returns violations (errors/warnings) but does not block PRs in MVP

7. **ConfigLoader** (`autopilot_core/config/loader.py`)
   - Loads per-project `autopilot.yaml` configurations
   - Supports GitHub repos (clones and caches)
   - Supports local paths (for development/testing)
   - YAML parsing with error handling

8. **ProjectRegistry** (`autopilot_core/config/project_registry.py`) - NEW
   - Tracks registered projects
   - Stores repo URLs and metadata
   - JSON-based persistence

9. **RepoClient** (`autopilot_core/clients/repo_client.py`) - NEW
   - Clone GitHub repositories
   - Create branches
   - Commit changes
   - Push branches
   - Read/write files in repos
   - Get unified diffs (`get_diff()`)
   - Git operations via GitPython
   - Create GitHub PRs (real if token/repo provided, stub otherwise)

10. **LLMClient** (`autopilot_core/clients/llm_client.py`) - NEW
   - Generic LLM client supporting multiple providers
   - OpenAI (GPT-4, GPT-3.5) support
   - Anthropic (Claude) support
   - Configurable via environment variables
   - Chat and generate interfaces

11. **MonitorAgent** (`agents/monitor/monitor_agent.py`) - NEW (MVP)
    - On-demand log file analysis
    - Rule-based issue detection (errors, warnings, patterns)
    - Returns structured issues with severity, code, message, line info
    - Accessible via `POST /monitor/check` endpoint
    - **Note**: On-demand only (no background service, no auto-triggers)

### ⏳ Stubbed / Partial

1. **MarketingAgent** - Marketing content generation (stub only)
2. **Pull Request Creation** - Implemented with GitHub API when token/repo info + push_branch=true; falls back to stub on failure/missing token
3. **Test Execution** - Command-based execution (pytest/npm test/phpunit) with stack-aware orchestration via `autopilot.yaml` runtime commands

---

## API Endpoints

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. `GET /health`
**Purpose**: Health check endpoint

**Response**:
```json
{
  "status": "healthy"
}
```

**Status**: ✅ Implemented

---

#### 2. `GET /projects`
**Purpose**: List all registered projects

**Response Model**: `List[ProjectInfo]`
```json
[
  {
    "project_id": "lemonade-stand-app",
    "repo_url": "https://github.com/user/lemonade-stand-app.git",
    "metadata": {}
  }
]
```

**Status**: ✅ Implemented

---

#### 2b. `POST /projects/register`
**Purpose**: Register a new project with Sanjaya

**Request Model**: `ProjectRegisterRequest`
```json
{
  "project_id": "lemonade-stand-app",
  "repo_url": "https://github.com/user/lemonade-stand-app.git",
  "metadata": {}
}
```

**Response Model**: `ProjectRegisterResponse`
```json
{
  "project_id": "lemonade-stand-app",
  "repo_url": "https://github.com/user/lemonade-stand-app.git",
  "message": "Project 'lemonade-stand-app' registered successfully."
}
```

**Status**: ✅ Implemented

---

#### 3. `POST /workflows/run`
**Purpose**: Execute a workflow (feature development, bugfix, etc.)

**Request Model**: `WorkflowRunRequest`
```json
{
  "workflow_type": "feature",  # "feature" or "bugfix"
  "project_id": "example-project",
  "contract_path": "design-contracts/lemonade-stand-planner.md",  # Required for FEATURE, optional for BUGFIX
  "dry_run": true,
  "run_codegen": false,
  "run_tests": false,
  "run_smoke": false,
  "run_bugfix": false,
  "create_pr": false
}
```

**Workflow Types**:
- `"feature"`: Full feature workflow (requires `contract_path`). Runs ProductAgent → CodegenAgent → Tests → Smoke → Governance → PR
- `"bugfix"`: Bugfix-only workflow (no `contract_path` needed). Runs Tests → BugfixAgent suggestions (if tests fail and `run_bugfix=true`). Skips ProductAgent and CodegenAgent.

**Response Model**: `WorkflowRunResponse`
```json
{
  "workflow_id": "wf-example-project-2024-12-08T18:30:00",
  "status": "accepted",  # Legacy status
  "message": "Feature workflow executed",
  "workflow_status": "success",  # New detailed status: "success", "failed_tests", "failed_smoke", "failed_governance", "error"
  "tests_passed": true,
  "smoke_passed": true,
  "governance_ok": true,
  "details": {
    "project_id": "example-project",
    "autopilot_config": {...},
    "design_contract": "design-contracts/lemonade-stand-planner.md",
    "dry_run": false,
    "workflow_steps": [...],
    "test_result": {...},
    "smoke_result": {...},
    "governance": {...}
  }
}
```

**Status**: ✅ Implemented (with status gating)

---

#### 4. `POST /ideas/feature`
**Purpose**: Create a feature design contract from structured feature idea

**Request Model**: `FeatureIdeaRequest`
```json
{
  "project_id": "example-project",
  "feature_name": "Lemonade Stand Planner",
  "summary": "Calculate profit, revenue, and break-even for a lemonade stand",
  "problem": "Need to determine if a lemonade stand business is profitable",
  "user_story": "As a business owner, I want to calculate profitability so that I can make informed decisions",
  "notes": "Initial MVP version"
}
```

**Response Model**: `FeatureIdeaResponse`
```json
{
  "project_id": "example-project",
  "contract_path": "design-contracts/lemonade-stand-planner.md",
  "message": "Feature design contract created."
}
```

**Status**: ✅ Fully Implemented

---

#### 4b. `POST /ideas/feature-from-idea` - NEW
**Purpose**: Create a comprehensive feature design contract from a simple idea using LLM

**Request Model**: `FeatureIdeaSimpleRequest`
```json
{
  "project_id": "example-project",
  "idea": "I want to add a feature that calculates profit margins for products",
  "context": {
    "priority": "high",
    "deadline": "2024-12-31"
  }
}
```

**Response Model**: `FeatureIdeaResponse`
```json
{
  "project_id": "example-project",
  "contract_path": "design-contracts/profit-margin-calculator.md",
  "message": "Feature design contract generated using LLM."
}
```

**Status**: ✅ Fully Implemented (LLM-powered)

---

#### 5. `POST /monitor/check`
**Purpose**: Analyze log files for issues (on-demand monitoring)

**Request Model**: `MonitorCheckRequest`
```json
{
  "log_paths": ["logs/app.log", "/var/log/app/error.log"],
  "max_lines": 2000
}
```

**Response Model**: `MonitorCheckResponse`
```json
{
  "issues": [
    {
      "severity": "error",
      "code": "ERROR_LINE",
      "message": "Detected ERROR_LINE pattern in log",
      "line": "2024-12-08 10:00:00 ERROR: Database connection failed",
      "line_number": 42,
      "file_path": "/path/to/logs/app.log"
    }
  ],
  "summary": "Found 1 issue(s): 1 error(s), 0 warning(s), 0 info"
}
```

**Status**: ✅ Implemented (MVP - rule-based detection)

**Note**: This is on-demand only. It does NOT automatically trigger workflows. For continuous monitoring, trigger this endpoint externally (cron, GitHub Actions, etc.).

**Detection Patterns**:
- `ERROR_LINE`: Lines containing "ERROR" (case-insensitive)
- `WARNING_LINE`: Lines containing "WARNING" (case-insensitive)
- `TIMEOUT_PATTERN`: Lines containing "timeout" or "timed out"
- `EXCEPTION_PATTERN`: Lines containing "Exception" or "Traceback"

---

## Project Questionnaire System

### Overview

The Project Questionnaire is a structured way to capture high-level project intent, making projects like "lemonade-stand" driven by explicit configuration rather than vague names.

**Location**: Each project has a questionnaire at `<project_root>/.sanjaya/questionnaire.yaml`

**Template**: `docs/project_questionnaire_template.yaml` defines the structure and defaults

### Questionnaire Structure

The questionnaire captures:

- **Project Metadata**: Name and description
- **Project Type**: `demo`, `internal_tool`, or `production`
- **Architecture**: 
  - UI type: `none`, `web`, or `mobile`
  - Backend stack: `fastapi`, `node`, or `none`
- **UI Details**: 
  - Framework: `nextjs`, `react`, or `none`
  - Key pages: list of `["landing", "dashboard", "form"]`
- **Authentication**: 
  - Enabled: boolean
  - Providers: list of `["email_password", "oauth_google", "none"]`
- **Data**: 
  - Persistence: `none`, `sqlite`, or `postgres`
  - Multi-user: boolean
- **Constraints**: 
  - Complexity: `toy`, `simple`, or `realistic`
  - Monitoring: boolean
  - Tests required: boolean
  - Out of scope: list of features/domains explicitly forbidden
- **Intent Lock**: 
  - Locked: boolean (if true, prevents ProductAgent from suggesting changes)
- **Confidence**: 
  - Confidence: float (0.0-1.0) in project requirements
  - Min confidence required: float (threshold for proceeding)

### Integration with ConfigLoader

**Method**: `load_project_questionnaire(project_id)` loads `.sanjaya/questionnaire.yaml`

**Flattening**: `_flatten_questionnaire_intent()` converts nested structure to flat dict:

```python
{
    "project_type": "demo",
    "ui": "web",
    "backend": "fastapi",
    "ui_framework": "nextjs",
    "ui_pages": ["landing", "form"],
    "auth_enabled": False,
    "auth_providers": [],
    "persistence": "none",
    "multi_user": False,
    "complexity": "toy",
    "monitoring": True,
    "tests_required": True
}
```

**Automatic Attachment**: `load_project_config()` automatically:
1. Loads questionnaire via `load_project_questionnaire()`
2. Flattens it via `_flatten_questionnaire_intent()`
3. Attaches as `config["intent"]`

**Usage**:
```python
config = config_loader.load_project_config("example-project")
intent = config["intent"]  # Flattened questionnaire answers
```

### Integration with ProductAgent

**Method**: `ensure_project_questionnaire(project_id)`
- Creates questionnaire from template if missing
- Sets `project_meta.name` to `project_id`
- Returns loaded questionnaire dict

**Design Contract Generation**:
- `create_feature_contract_from_idea()` ensures questionnaire exists
- **Checks intent lock**: If `locked == True`, raises `ValueError` (prevents contract creation)
- **Checks confidence**: If `confidence < min_confidence_required`, raises `ValueError`
- Includes intent in LLM prompts with constraints:
  - "NO UI/FRONTEND" if `ui == "none"`
  - "Authentication: DISABLED" if `auth_enabled == False`
  - Complexity level guidance (toy/simple/realistic)
  - **Out of scope guardrail**: Explicitly forbids features in `out_of_scope` list
  - **Locked intent warning**: If locked, tells LLM not to suggest architecture changes
- Adds "Project Intent" section to generated design contracts
- **Snapshots intent**: Adds immutable "Project Intent Snapshot" with hash for verification

**Example Project Intent Section**:
```markdown
## Project Intent

- **Project type**: demo
- **UI**: none
- **Backend**: fastapi
- **Auth**: disabled
- **Persistence**: none
- **Multi-user**: false
- **Complexity**: toy
- **Monitoring**: enabled
- **Tests required**: true
- **Out of scope**: payments, notifications
- **Intent locked**: unlocked
```

**Project Intent Snapshot** (immutable):
```yaml
## Project Intent Snapshot

project_intent_snapshot:
  project_type: demo
  ui: none
  backend: fastapi
  auth_enabled: false
  persistence: none
  multi_user: false
  complexity: toy
  monitoring: true
  tests_required: true
  out_of_scope: []

Snapshot Hash: abc123def456
```

### Integration with CodegenAgent

**Intent-Aware Scaffolding**:
- Only scaffolds UI if `intent["ui"] != "none"` and `intent["ui_framework"]` matches
- Skips auth scaffolding if `intent["auth_enabled"] == False`
- Uses `intent["backend"]` for backend stack decisions
- Respects `intent["persistence"]` for database setup

**Usage in `_ensure_scaffold()`**:
```python
intent = project_config.get("intent", {}) or {}

# Use intent backend if available
if intent.get("backend"):
    backend_stack = intent["backend"]

# Scaffold UI only if intent says so
if intent.get("ui") == "web":
    ui_framework = intent.get("ui_framework", "none")
    if ui_framework == "nextjs":
        self._scaffold_next(dirs)
```

### Benefits

1. **Explicit Intent**: Projects declare architecture upfront
2. **Consistent Decisions**: All agents use the same intent
3. **No Magic Names**: Behavior driven by questionnaire, not naming conventions
4. **Future-Proof**: Easy to extend with new fields
5. **Human-Readable**: YAML format easy to edit manually or via future tools

### Example: example-project Questionnaire

**Location**: `configs/examples/example-project/.sanjaya/questionnaire.yaml`

**Content**:
```yaml
project_meta:
  name: "example-project"
  description: "Internal golden-path FastAPI demo"

project_type:
  value: "demo"

architecture:
  ui:
    value: "none"
  backend:
    value: "fastapi"
# ... (see full file for complete structure)
```

**Resulting Intent**:
```python
{
    "project_type": "demo",
    "ui": "none",
    "backend": "fastapi",
    "ui_framework": "none",
    "auth_enabled": False,
    "persistence": "none",
    "multi_user": False,
    "complexity": "toy",
    "monitoring": True,
    "tests_required": True
}
```

**See Also**: `docs/project_questionnaire_overview.md` for detailed documentation

---

## Agent Implementations

### 1. OrchestratorAgent

**Location**: `agents/orchestrator/orchestrator_agent.py`

**Responsibilities**:
- Coordinates workflows between agents
- Loads project configurations
- Validates design contract files exist
- Returns structured workflow plans

**Key Methods**:

#### `run_feature_workflow(project_id, contract_path, dry_run=True)`
- Generates workflow ID: `wf-{project_id}-{timestamp}`
- Loads project config via `ConfigLoader`
- Validates design contract file exists
- Returns tuple: `(workflow_id, status, message, details)`

**Status**: ✅ Implemented (Step 2 - validation only)

---

### 2. ProductAgent

**Location**: `agents/product/product_agent.py`

**Responsibilities**:
- Creates feature design contracts from structured input (v0)
- **NEW**: Generates comprehensive design contracts from simple ideas using LLM
- Slugifies feature names for filesystem safety
- Writes markdown files with comprehensive template
- Clarifies requirements through LLM dialogue

**Key Methods**:

#### `create_feature_contract(project_id, feature_name, summary, problem, user_story, notes="")`
- Slugifies `feature_name` to create filesystem-safe filename
- Creates `design-contracts` directory if it doesn't exist
- Writes markdown file with standard sections:
  1. Summary
  2. Problem Statement
  3. User Story
  4. Scope
  5. Business Rules
  6. Logging & Monitoring
  7. Acceptance Criteria
  8. Notes
- Returns: `{"project_id": str, "contract_path": str}`

#### `create_feature_contract_from_idea(project_id, idea, context=None)` - NEW
- Takes a simple feature idea string
- Uses LLM to generate comprehensive design contract
- Includes all sections: API Design, Data Model, Logging & Monitoring, Tests, Security, etc.
- Loads project config for context (tech stack, conventions)
- Generates markdown following `feature_design_template.md` structure
- Returns: `{"project_id": str, "contract_path": str}`
- **Requires**: LLM client (OpenAI or Anthropic API key)

#### `clarify_requirements(idea, context=None)` - NEW
- Uses LLM to generate clarifying questions about a feature idea
- Helps refine requirements before design contract creation
- Returns: `{"original_idea": str, "clarifying_questions": str, "context": dict}`

#### `_slugify(text: str) -> str`
- Converts text to filesystem-safe slug
- Lowercase, hyphens instead of spaces
- Removes special characters
- Example: `"Lemonade Stand Planner"` → `"lemonade-stand-planner"`

**LLM Integration**:
- Supports OpenAI (GPT-4, GPT-3.5) and Anthropic (Claude)
- Configured via `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` environment variables
- Uses system prompts to guide LLM output format
- Generates production-ready design contracts

**Project Questionnaire Integration**:
- `ensure_project_questionnaire(project_id)` - Creates questionnaire from template if missing
- Uses questionnaire intent in LLM prompts for design contracts
- Adds "Project Intent" section to generated contracts
- Respects intent constraints (no UI if ui=none, no auth if disabled, etc.)

**Status**: ✅ Fully Implemented (v0 + LLM-powered + Questionnaire)

---

### 3. BugfixAgent

**Location**: `agents/bugfix/bugfix_agent.py`

**Responsibilities**:
- Analyzes test failures and suggests fixes
- Generates unified diff patches
- Provides retry commands and explanatory notes
- LLM-powered analysis of test output

**Key Methods**:

#### `suggest_fixes(request: BugfixRequest) -> BugfixResponse`
- Takes test failure details (command, exit code, stdout, stderr)
- Uses LLM to analyze root cause
- Generates unified diff patches for affected files
- Returns patches, retry command, and notes
- **Requires**: LLM client (OpenAI or Anthropic API key)

**Data Models**:
- `BugfixRequest`: Command, exit code, stdout, stderr, changed files, project config
- `BugfixResponse`: Patches (list), retry command, notes, success flag
- `Patch`: File path, unified diff, notes

**Integration**:
- Called automatically by Orchestrator when tests fail and `run_bugfix=true`
- Patches are returned in workflow response (not auto-applied)
- Human review required before applying fixes

**Status**: ✅ Implemented (LLM-powered)

---

### 4a. Bugfix Workflow

**Location**: `agents/orchestrator/orchestrator_agent.py` → `run_bugfix_workflow()`

**Responsibilities**:
- Runs bugfix-only workflow (no ProductAgent or CodegenAgent)
- Executes tests on current codebase
- Suggests patches via BugfixAgent if tests fail (when `run_bugfix=true`)
- Does NOT auto-apply patches (HITL)

**Key Methods**:

#### `run_bugfix_workflow(project_id, run_tests=True, run_bugfix=False)`
- Skips ProductAgent and CodegenAgent
- Runs test command from `runtime.*.test_command` (or stack defaults)
- If tests fail and `run_bugfix=true`:
  - Calls `BugfixAgent.suggest_fixes()` with test failure details
  - Returns patches in response (not applied)
  - Workflow status remains `FAILED_TESTS` (patches are suggestions only)
- Returns workflow result with `workflow_status`, `tests_passed`, and `bugfix_result`

**Usage**:
```json
POST /workflows/run
{
  "workflow_type": "bugfix",
  "project_id": "example-project",
  "run_tests": true,
  "run_bugfix": true
}
```

**Status**: ✅ Implemented

---

### 4. GovernanceAgent

**Location**: `agents/governance/governance_agent.py`

**Responsibilities**:
- Enforces safety rules and compliance policies
- Checks forbidden paths (secrets, credentials)
- Validates test coverage requirements
- Checks allowed dependencies

**Key Methods**:

#### `evaluate(diff: str, project_config: Dict[str, Any]) -> GovernanceResult`
- Analyzes unified diff for policy violations
- Checks forbidden paths (e.g., `.env`, `**/secrets/**`)
- Requires tests for code changes (if configured)
- Validates dependencies against allowed list (if configured)
- Returns violations (errors/warnings)
- When governance fails, workflow status is set to `FAILED_GOVERNANCE`

**Data Models**:
- `GovernanceRuleViolation`: Rule name, severity, message, file path
- `GovernanceResult`: OK flag, violations list, summary

**Rules**:
1. **Forbidden Paths**: Blocks changes to `.env`, secrets, credentials
2. **Require Tests**: Warns if code changes lack test files
3. **Allowed Dependencies**: Validates new dependencies against whitelist (if configured)

**Integration**:
- Called automatically by Orchestrator before PR creation
- Violations are surfaced in workflow response
- Does not block PR creation in MVP (informational only)

**Status**: ✅ Implemented (rule-based)

**Integration with Workflow Status**:
- When `create_pr=true`, GovernanceAgent runs automatically
- If governance fails, workflow status is set to `FAILED_GOVERNANCE`
- Governance violations are returned in workflow response but do not block PR creation in MVP

---

### 5. ConfigLoader

**Location**: `autopilot_core/config/loader.py`

**Responsibilities**:
- Loads per-project `autopilot.yaml` configurations
- Handles missing config files with proper error handling

**Key Methods**:

#### `load_project_config(project_id: str) -> Dict[str, Any]`
- Loads config from: `configs/examples/{project_id}/.sanjaya/autopilot.yaml`
- Uses `yaml.safe_load()` for parsing
- Returns config dict or empty dict if file is empty
- Raises `FileNotFoundError` if config missing

**Status**: ✅ Fully Implemented

---

### 6. CodegenAgent

**Location**: `agents/codegen/codegen_agent.py`

**Responsibilities**:
- Generates code and tests from design contracts
- LLM-driven for all stacks
- Creates deterministic scaffolds for known stacks
- Stack-aware file naming and structure

**Key Methods**:

#### `generate_artifacts(project_id, repo_path, contract_path, project_config)`
- Parses design contract markdown
- Ensures scaffold exists (creates if missing)
- Generates feature-specific code via LLM
- Generates tests via LLM
- Writes files to repository

**Scaffolds**:
- FastAPI: Includes `/health` endpoint in `app/main.py`
- Next.js: Includes `/api/health` route (App Router or Pages Router)
- PHP: Includes `/health` handler in `public/index.php`

**Project Questionnaire Integration**:
- Reads `config["intent"]` from project config
- Uses intent to decide which scaffolds to create
- Only scaffolds UI if `intent["ui"] != "none"`
- Skips auth scaffolding if `intent["auth_enabled"] == False`
- Uses `intent["backend"]` for backend stack decisions

**Status**: ✅ Fully Implemented (LLM-powered + scaffolds + intent-aware)

---

### 7. MonitorAgent

**Location**: `agents/monitor/monitor_agent.py`

**Responsibilities**:
- Analyzes log files for issues (on-demand)
- Rule-based pattern detection
- Returns structured issue reports

**Key Methods**:

#### `analyze_logs(log_files: List[str], max_lines: int = 2000) -> MonitorResult`
- Reads log files (up to `max_lines` per file)
- Detects issues using predefined patterns:
  - `ERROR_LINE`: Lines containing "ERROR"
  - `WARNING_LINE`: Lines containing "WARNING"
  - `TIMEOUT_PATTERN`: Lines containing "timeout" or "timed out"
  - `EXCEPTION_PATTERN`: Lines containing "Exception" or "Traceback"
- Returns structured issues with severity, code, message, line info

**Data Models**:
- `MonitorIssue`: severity, code, message, line, line_number, file_path
- `MonitorResult`: issues list, summary string

**Integration**:
- Accessible via `POST /monitor/check` endpoint
- On-demand only (no background service)
- Does NOT automatically trigger workflows
- For continuous monitoring, trigger externally (cron, GitHub Actions, etc.)

**Status**: ✅ Implemented (MVP - rule-based detection)

---

## File Structure & Conventions

### Project Structure
```
sanjaya-app/                     # Platform repository
├── autopilot_core/              # Core platform code
│   ├── __init__.py
│   ├── main_service/
│   │   ├── __init__.py
│   │   └── api.py              # FastAPI service
│   ├── config/
│   │   ├── __init__.py
│   │   ├── loader.py           # Config loader (GitHub + local)
│   │   └── project_registry.py # Project registry (NEW)
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── repo_client.py      # Git operations (implemented)
│   │   ├── llm_client.py        # LLM client (NEW - implemented)
│   │   ├── github_client.py    # GitHub API (stubbed)
│   │   └── ...
│   └── workflows/               # Workflow definitions (stubbed)
├── agents/                      # Agent implementations
│   ├── __init__.py
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   └── orchestrator_agent.py
│   ├── product/
│   │   ├── __init__.py
│   │   ├── product_agent.py
│   │   └── prompts.py           # LLM prompt templates
│   ├── codegen/
│   │   ├── __init__.py
│   │   ├── codegen_agent.py
│   │   └── prompts.py           # Codegen prompts
│   ├── bugfix/
│   │   ├── __init__.py
│   │   ├── bugfix_agent.py      # NEW - Bugfix suggestions
│   │   └── prompts.py           # Bugfix prompts
│   ├── governance/
│   │   ├── __init__.py
│   │   ├── governance_agent.py  # NEW - Policy enforcement
│   │   └── prompts.py           # Governance rules
│   └── [other agents - stubbed]
├── configs/
│   ├── global-settings.yaml
│   ├── autopilot-schema.yaml
│   └── examples/                # For local testing only
│       └── example-project/    # ✅ Golden Path Reference Implementation
│           ├── .sanjaya/
│           │   ├── autopilot.yaml
│           │   └── design-contracts/
│           │       └── test-feature.md
│           └── backend/         # ✅ Fully working FastAPI backend
│               ├── app/
│               │   ├── __init__.py
│               │   └── main.py  # FastAPI app with /health and /ping
│               ├── tests/
│               │   ├── __init__.py
│               │   └── test_health.py  # Unit tests (2 tests)
│               └── requirements.txt
├── tests/
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_example_project_golden_path.py  # ✅ Golden path integration tests
│   ├── test_example_project_workflow.py  # Additional workflow tests
│   ├── test_monitor_agent.py
│   └── test_workflows.py
├── .cache/                      # Cached cloned repos (NEW)
│   └── projects/
│       └── [project_id]/
├── .sanjaya/                    # Platform config (NEW)
│   └── project_registry.json    # Registered projects
├── docs/                        # Documentation
│   ├── sanjaya-spec-master.md
│   ├── AGENTS.md
│   ├── approach.md
│   ├── feature_design_template.md
│   └── cursor_design.md         # This file
└── scripts/                      # Utility scripts
    ├── dev-start.sh
    ├── run-tests.sh
    └── sync-project.sh
```

### Separate Project Repositories

Each project is a **separate GitHub repository** with this structure:
```
project-repo/
├── README.md
├── .sanjaya/                    # Sanjaya configuration
│   ├── autopilot.yaml          # Project config
│   └── design-contracts/       # Feature design contracts
│       └── [feature].md
└── [project code]
```

### Project Configuration Structure

Each project under `configs/examples/{project_id}/` must have:
```
.sanjaya/
├── autopilot.yaml              # Project configuration
├── questionnaire.yaml          # Project intent questionnaire (NEW)
└── design-contracts/           # Feature design contracts
    └── {slugified-feature-name}.md
```

**Questionnaire File**:
- Location: `.sanjaya/questionnaire.yaml`
- Template: `docs/project_questionnaire_template.yaml`
- Auto-created by ProductAgent if missing
- Exposed as `config["intent"]` by ConfigLoader

---

## Path Handling

### Path Conventions

1. **Contract Path Format** (relative to `.sanjaya/`):
   ```
   design-contracts/{slugified-feature-name}.md
   ```
   Example: `design-contracts/lemonade-stand-planner.md`

2. **Full Path Construction**:
   - **For GitHub repos**: `.cache/projects/{project_id}/.sanjaya/{contract_path}`
   - **For local projects**: `configs/examples/{project_id}/.sanjaya/{contract_path}`
   
   Example: `.cache/projects/lemonade-stand-app/.sanjaya/design-contracts/lemonade-stand-planner.md`

3. **Config Path**:
   - **For GitHub repos**: `.cache/projects/{project_id}/.sanjaya/autopilot.yaml`
   - **For local projects**: `configs/examples/{project_id}/.sanjaya/autopilot.yaml`

### Project Registration

Projects must be registered before use:
1. Register via `POST /projects/register` with repo URL
2. ConfigLoader clones repo to `.cache/projects/{project_id}/`
3. Agents access project via cached clone
4. Changes are written to cached clone (PR creation coming soon)

### Path Consistency

- **ProductAgent** returns `contract_path` relative to `.sanjaya/`
- **OrchestratorAgent** expects `contract_path` relative to `.sanjaya/`
- Both agents construct full paths using the same pattern
- This ensures compatibility between agents

### Stack & Runtime Configuration (`autopilot.yaml`)

Example fields the agents consume:
```
codebase:
  root: "."
  backend_dir: "backend"
  frontend_dir: "frontend"
  tests_dir: "tests"

stack:
  backend: "fastapi"     # or "nextjs" / "node" / "php"
  frontend: "nextjs"     # optional
  database: "mysql"      # or "mongodb" / "none"

runtime:
  backend_fastapi:
    dev_command: "cd backend && uvicorn app.main:app --reload --port 8000"
    test_command: "pytest -q"
  frontend_next:
    dev_command: "cd frontend && npm run dev"
    test_command: "cd frontend && npm test"
  backend_php:
    dev_command: "php -S localhost:8000 -t backend-php/public"
    test_command: "cd backend-php && ./vendor/bin/phpunit"

database:
  driver: "mysql"        # or "mongodb"
  env_prefix: "DB_"
  mongo_env_uri: "MONGO_URI"
```

CodegenAgent uses these fields to:
- Choose scaffold and file destinations (backend_dir, frontend_dir, tests_dir)
- Populate prompts with stack/runtime context
- Run default test commands if not overridden

---

## Data Models

### Request Models

#### `WorkflowRunRequest`
```python
{
  "workflow_type": str,        # e.g., "feature_from_contract"
  "project_id": str,           # e.g., "example-project"
  "contract_path": str,        # e.g., "design-contracts/feature.md"
  "dry_run": bool = True       # Default: True
}
```

#### `FeatureIdeaRequest`
```python
{
  "project_id": str,           # e.g., "example-project"
  "feature_name": str,         # e.g., "Lemonade Stand Planner"
  "summary": str,              # Feature summary
  "problem": str,              # Problem statement
  "user_story": str,           # User story
  "notes": str = ""            # Optional notes
}
```

### Response Models

#### `WorkflowRunResponse`
```python
{
  "workflow_id": str,          # e.g., "wf-example-project-2024-12-08T18:30:00"
  "status": Literal["accepted", "rejected", "error"],  # Legacy status (backward compat)
  "message": str,
  "details": Dict[str, Any],   # Workflow details
  "workflow_status": Optional[WorkflowStatus],  # New detailed status
  "tests_passed": Optional[bool],
  "smoke_passed": Optional[bool],
  "governance_ok": Optional[bool]
}
```

#### `WorkflowStatus` (Enum)
```python
class WorkflowStatus(str, Enum):
    SUCCESS = "success"
    FAILED_TESTS = "failed_tests"
    FAILED_SMOKE = "failed_smoke"
    FAILED_GOVERNANCE = "failed_governance"
    ERROR = "error"
```

**Status Computation**:
- If tests failed → `FAILED_TESTS`
- Else if smoke failed (when `run_smoke=true`) → `FAILED_SMOKE`
- Else if governance failed (when `create_pr=true`) → `FAILED_GOVERNANCE`
- Otherwise → `SUCCESS`

#### `WorkflowType` (Enum)
```python
class WorkflowType(str, Enum):
    FEATURE = "feature"  # Full feature workflow (ProductAgent → CodegenAgent → Tests → PR)
    BUGFIX = "bugfix"    # Bugfix-only workflow (Tests → BugfixAgent suggestions)
```

#### `FeatureIdeaResponse`
```python
{
  "project_id": str,           # e.g., "example-project"
  "contract_path": str,        # e.g., "design-contracts/lemonade-stand-planner.md"
  "message": str               # e.g., "Feature design contract created."
}
```

---

## Workflow Flow

### Feature Development Workflow (Current State)

```
1. POST /projects/register (if not already registered)
   - Register project with GitHub repo URL
   ↓
2. POST /ideas/feature
   ↓
3. ProductAgent.create_feature_contract()
   - Gets repo path (GitHub cache or local)
   - Slugifies feature name
   - Creates design-contracts directory in repo
   - Writes markdown file to repo
   - Returns contract_path
   ↓
4. POST /workflows/run
   ↓
5. OrchestratorAgent.run_feature_workflow()
   - Generates workflow ID
   - Loads project config (ConfigLoader - from GitHub or local)
   - Validates contract file exists in repo
   - If `dry_run=true`: stops after validation
   - If `dry_run=false`: invokes CodegenAgent to generate stub code + tests into repo
   - Returns workflow result + generated file paths
   ↓
6. [STUBBED] Test execution
   ↓
7. [STUBBED] Pull Request creation
   ↓
8. Human reviews and approves
```

### Current Limitations

- Code generation is LLM-assisted (requires API keys)
- PR creation requires GitHub token and repo metadata
- Test execution is command-based (uses `autopilot.yaml` runtime commands)

---

## What's Working

### ✅ Fully Functional

1. **Feature Contract Creation**
   - Accepts structured feature ideas via API
   - Creates properly formatted markdown files
   - Handles slugification correctly
   - Creates directories as needed

2. **Project Config Loading**
   - Loads YAML configurations
   - Handles missing files with proper errors
   - Returns structured config data

3. **Workflow Validation**
   - Validates project config exists
   - Validates design contract exists
   - Returns structured workflow plans
   - Generates unique workflow IDs

4. **API Service**
   - FastAPI endpoints working
   - Request/Response validation
   - Error handling

### ⚠️ Partially Working

1. **Workflow Execution**
   - Validates inputs correctly
   - Runs LLM-driven codegen when `dry_run=false` and `run_codegen=true`
   - Returns generated file paths
   - Test execution is command-based (uses `autopilot.yaml` runtime commands)
   - Smoke test execution (starts server, hits health endpoint, stops)
   - PR prep: branch/commit + PR stub; real PR if token/repo info + push_branch enabled
   - Workflow status computation (SUCCESS, FAILED_TESTS, FAILED_SMOKE, FAILED_GOVERNANCE, ERROR)

2. **Test Suite**
   - 10 tests total (all passing)
   - Integration tests for example-project golden path
   - MonitorAgent tests
   - Workflow status computation tests

---

## What's Stubbed

### Agents (Stub Status)

1. **MarketingAgent** - Stub only (not implemented yet)

### Workflow Steps (Stubbed)

1. Pull request creation (requires GitHub token + repo metadata; falls back to stub)
2. Automated workflow scheduling (no cron/scheduler yet)

### Endpoints (Stubbed)

1. None - All documented endpoints are implemented

---

## Usage Examples

### Example 1: Create a Feature Design Contract (Structured Input)

**Request**:
```bash
curl -X POST "http://localhost:8000/ideas/feature" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "example-project",
    "feature_name": "Lemonade Stand Planner",
    "summary": "Calculate profit, revenue, and break-even for a lemonade stand",
    "problem": "Need to determine if a lemonade stand business is profitable",
    "user_story": "As a business owner, I want to calculate profitability so that I can make informed decisions",
    "notes": "Initial MVP version"
  }'
```

**Response**:
```json
{
  "project_id": "example-project",
  "contract_path": "design-contracts/lemonade-stand-planner.md",
  "message": "Feature design contract created."
}
```

**Result**: Creates file at:
```
configs/examples/example-project/.sanjaya/design-contracts/lemonade-stand-planner.md
```

---

### Example 1b: Create a Feature Design Contract from Simple Idea (LLM-Powered) - NEW

**Request**:
```bash
curl -X POST "http://localhost:8000/ideas/feature-from-idea" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "example-project",
    "idea": "I want to add a feature that calculates profit margins for products and shows break-even analysis",
    "context": {
      "priority": "high"
    }
  }'
```

**Response**:
```json
{
  "project_id": "example-project",
  "contract_path": "design-contracts/profit-margin-calculator.md",
  "message": "Feature design contract generated using LLM."
}
```

**Result**: Creates comprehensive design contract with:
- Full API design (endpoints, request/response schemas)
- Data models with entities and relationships
- Logging & monitoring specifications
- Security requirements
- Acceptance criteria
- Test cases (unit, integration, E2E)
- Implementation notes
- Dependencies

**Note**: Requires `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` environment variable.

---

### Example 2: Run a Feature Workflow (Validation Only)

**Request**:
```bash
curl -X POST "http://localhost:8000/workflows/run" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "feature_from_contract",
    "project_id": "example-project",
    "contract_path": "design-contracts/lemonade-stand-planner.md",
    "dry_run": true
  }'
```

**Response**:
```json
{
  "workflow_id": "wf-example-project-2024-12-08T18:30:00.123456",
  "status": "accepted",
  "message": "Feature workflow validated (dry_run)",
  "details": {
    "project_id": "example-project",
    "autopilot_config": {
      "project_name": "example-project"
    },
    "design_contract": "design-contracts/lemonade-stand-planner.md",
    "dry_run": true,
    "workflow_steps": [
      "load_project_config",
      "validate_contract_exists",
      "prepare_codegen_inputs",
      "invoke_codegen_agent (skipped, dry_run)",
      "run_tests (skipped, dry_run)",
      "prepare_pull_request (skipped, dry_run)"
    ]
  }
}
```

---

### Example 2b: Run Workflow with Codegen (dry_run=false) - NEW

**Request**:
```bash
curl -X POST "http://localhost:8000/workflows/run" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "feature_from_contract",
    "project_id": "example-project",
    "contract_path": "design-contracts/lemonade-stand-planner.md",
    "dry_run": false,
    "run_codegen": true,
    "run_tests": false,
    "create_pr": false
  }'
```

**Behavior**:
- Validates project config and contract
- Invokes CodegenAgent (LLM) to write generated code/tests into the repo
- Returns generated file paths in `details.generated_files`

**Note**: Requires repo path resolvable (local examples or registered GitHub repo) and LLM keys for all stacks. No deterministic fallback.

---

### Example 2c: Run Workflow with Codegen + Tests + PR (requires token and repo metadata)

**Request**:
```bash
curl -X POST "http://localhost:8000/workflows/run" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "feature_from_contract",
    "project_id": "example-project",
    "contract_path": "design-contracts/lemonade-stand-planner.md",
    "dry_run": false,
    "run_codegen": true,
    "run_tests": true,
    "create_pr": true,
    "push_branch": true,
    "pr_base": "main",
    "branch_name": "feature/lemonade-planner",
    "commit_message": "feat: lemonade planner"
  }'
```

**Behavior**:
- Validates project config and contract
- Runs codegen (LLM) and writes code/tests to repo
- Runs tests using `runtime.backend.test_command` (or stack default)
- Creates branch/commit; if token and repo metadata are present, pushes and creates a GitHub PR; otherwise returns stub PR metadata

**Note**: Requires repo metadata (e.g., `metadata.repo_full_name`) and GitHub token for real PR creation.

---

## Stack Scaffolds (deterministic)

When `run_codegen=true`, CodegenAgent will write missing scaffold files for known stacks before LLM codegen:

- FastAPI (backend_dir, tests_dir):
  - `app/main.py`, `app/api/routes.py`, `app/core/config.py`, `app/core/db.py`
  - `requirements.txt`, `.env.example`
  - `tests/test_health.py`

- Next.js/Node (frontend_dir, tests_dir/frontend):
  - `package.json`, `next.config.mjs`, `tsconfig.json`
  - `app/page.tsx`, `.env.local.example`, sample `sample.test.tsx`

- PHP (backend_dir, tests_dir/php):
  - `public/index.php`
  - `src/config.php`, `src/db/mysql.php`, `src/db/mongo.php`
  - `composer.json`, `.env.example`
  - `tests/phpunit.xml`, `tests/HealthTest.php`

LLM still generates feature-specific code/tests; scaffolds ensure predictable entrypoints and manifests.

### Known requirements
- Real PR creation: requires repo metadata (`metadata.repo_full_name` or `metadata.github_repo`) and `GITHUB_TOKEN`; otherwise a stub PR is returned.
- Tests: use `runtime.*.test_command` when provided; fall back to stack defaults (pytest / npm test / phpunit).
- LLM: required for all stacks; no deterministic fallback for feature code/tests.

### Recommended install/run/smoke commands (per stack)

Define these in `autopilot.yaml` under `runtime` to make installs and smoke checks non-interactive and predictable:

- FastAPI / Python
  - `runtime.backend_fastapi.install_command`:  
    `python -m venv backend/.venv && . backend/.venv/bin/activate && pip install --upgrade pip && pip install -r backend/requirements.txt`
    (Optionally copy `.env.example` -> `.env` first)
  - `runtime.backend_fastapi.dev_command`: `cd backend && . .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000`
  - `runtime.backend_fastapi.test_command`: `cd backend && . .venv/bin/activate && pytest -q`
  - `smoke`: start uvicorn, hit `http://127.0.0.1:8000/health`, then stop

- Next.js / Node
  - `runtime.frontend_next.install_command`: `cd frontend && (test -f package-lock.json && npm ci || npm install)`
  - `runtime.frontend_next.dev_command`: `cd frontend && NEXT_TELEMETRY_DISABLED=1 PORT=3000 npm run dev`
  - `runtime.frontend_next.test_command`: `cd frontend && npm test`
  - `smoke`: start dev server on port 3000, hit `http://127.0.0.1:3000/api/health`, stop (add `app/api/health/route.ts` or `pages/api/health.ts`)

- PHP (plain)
  - `runtime.backend_php.install_command`: `cd backend-php && composer install --no-interaction --no-progress --prefer-dist` (copy `.env.example` -> `.env` first)
  - `runtime.backend_php.dev_command`: `cd backend-php && php -S 127.0.0.1:8000 -t public`
  - `runtime.backend_php.test_command`: `cd backend-php && ./vendor/bin/phpunit`
  - `smoke`: start built-in server on 8000, hit `http://127.0.0.1:8000/health`, stop

Note: Orchestrator’s current smoke step is simulated (does not start servers yet); these commands describe the intended behavior for real smoke runs.

---

## Design Decisions

### 1. Path Handling
- **Decision**: Contract paths are relative to `.sanjaya/`
- **Rationale**: Allows flexibility in project structure while maintaining consistency
- **Impact**: All agents must use the same path convention

### 2. Slugification
- **Decision**: Use simple regex-based slugification
- **Rationale**: No external dependencies, works for all use cases
- **Impact**: Feature names are converted to filesystem-safe slugs

### 3. Project Structure
- **Decision**: Support both GitHub repos (production) and local paths (testing)
- **Rationale**: Flexibility for development while supporting production use case
- **Impact**: ConfigLoader checks registry first, falls back to local paths

### 4. LLM-First Codegen
- **Decision**: Codegen/tests are fully LLM-driven for all stacks
- **Rationale**: Avoid brittle stubs; rely on prompts informed by `autopilot.yaml`
- **Impact**: Requires LLM keys; no deterministic fallback

### 5. Stack-Aware Prompts
- **Decision**: Include stack/runtime/dirs from `autopilot.yaml` in codegen prompts
- **Rationale**: Guide LLM toward correct file layout and commands
- **Impact**: More predictable file placement and naming

### 6. PR Flow
- **Decision**: Allow real PR creation when token + repo metadata are available; otherwise stub
- **Rationale**: Support end-to-end flow while remaining safe without credentials
- **Impact**: `push_branch` + repo metadata + token enable real PR; errors fall back to stub metadata

---

## Next Steps

### Immediate Priorities

1. ✅ **Golden Path Complete** - example-project is fully working
2. **External Repo Integration** - Ready to integrate lemonade-stand or other external repos
3. **MarketingAgent** - Implement marketing content generation
4. **PR Flow Hardening** - Improve error handling and metadata for PR creation

### Future Enhancements

1. **Automated Workflow Scheduling** - Cron/scheduler for continuous workflows
2. **Enhanced MonitorAgent** - Background service, auto-triggers, more detection patterns
3. **MarketingAgent** - Content generation for features/releases
4. **Enhanced LLM Prompts** - Project-specific context, better code generation
5. **Multi-step Requirement Clarification** - Interactive workflow for requirement refinement
6. **Stack Expansion** - Add more stack scaffolds (Django, Express, Laravel, etc.)

---

## Smoke Test Instructions (Codegen Flow)

1) Start API: `./scripts/dev-start.sh` (activate venv if needed).
2) Ensure project accessible: use local `configs/examples/example-project` or register a real repo.
3) Create or reuse a design contract (e.g., `design-contracts/lemonade-stand-planner.md`).
4) Run workflow with codegen:
```bash
curl -X POST "http://localhost:8000/workflows/run" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "feature_from_contract",
    "project_id": "example-project",
    "contract_path": "design-contracts/lemonade-stand-planner.md",
    "dry_run": false
  }'
```
5) Verify `details.generated_files` in response.
6) Inspect generated files in the repo (e.g., `generated/<slug>_feature.py`, `tests/test_<slug>_feature.py`).
7) LLM keys are required (OpenAI/Anthropic). No stub fallback; call will fail without keys.

---

## Golden Path: example-project Reference Implementation

**Status**: ✅ **Fully Working Golden Path**

The `configs/examples/example-project/` directory is a **complete, working reference implementation** that demonstrates the full Sanjaya workflow end-to-end.

### Structure

```
configs/examples/example-project/
├── .sanjaya/
│   ├── autopilot.yaml              # ✅ Project configuration
│   └── design-contracts/
│       └── test-feature.md         # ✅ Sample design contract
└── backend/                         # ✅ FastAPI backend
    ├── app/
    │   ├── __init__.py
    │   └── main.py                  # FastAPI app with /health and /ping
    ├── tests/
    │   ├── __init__.py
    │   └── test_health.py            # Unit tests (2 tests: test_health, test_ping)
    └── requirements.txt              # Dependencies: fastapi, uvicorn, pytest, httpx
```

### FastAPI Application

**Location**: `backend/app/main.py`

**Endpoints**:
- `GET /health` → `{"status": "ok"}`
- `GET /ping` → `{"message": "pong"}`

**Usage**:
```bash
cd configs/examples/example-project/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Configuration

**Location**: `.sanjaya/autopilot.yaml`

```yaml
project_name: "example-project"

codebase:
  root: "."
  backend_dir: "backend"
  tests_dir: "backend/tests"

stack:
  backend: "fastapi"
  database: "none"

runtime:
  backend_fastapi:
    install_command: "cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
    test_command: "cd backend && . .venv/bin/activate && pytest -q"
    smoke_command: "cd backend && . .venv/bin/activate && (pkill -f 'uvicorn app.main:app' || true) && sleep 1 && uvicorn app.main:app --host 127.0.0.1 --port 8000 > /dev/null 2>&1 & sleep 4 && curl -f http://127.0.0.1:8000/health && pkill -f 'uvicorn app.main:app'"
    dev_command: "cd backend && . .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

**Key Features**:
- Commands are non-interactive and CI-friendly
- Smoke command handles port conflicts automatically
- All commands work from `configs/examples/example-project/` root

### Running Tests

**Unit Tests**:
```bash
cd configs/examples/example-project/backend
. .venv/bin/activate
pytest -q
```
**Expected**: 2 tests pass (test_health, test_ping)

**Integration Tests**:
```bash
cd /Volumes/workplace/sanjaya-app
pytest tests/integration/test_example_project_golden_path.py -v
```
**Expected**: 2 tests pass
- `test_example_project_golden_path_workflow` - Full workflow with tests + smoke
- `test_example_project_golden_path_with_governance` - Includes governance check

### Golden Path Workflow

The example-project can run the complete Sanjaya workflow:

1. **Dry Run** (Validation):
   ```bash
   curl -X POST "http://localhost:8000/workflows/run" \
     -H "Content-Type: application/json" \
     -d '{
       "workflow_type": "feature",
       "project_id": "example-project",
       "contract_path": "design-contracts/test-feature.md",
       "dry_run": true
     }'
   ```
   ✅ Status: `accepted`

2. **Full Workflow with Tests + Smoke**:
   ```bash
   curl -X POST "http://localhost:8000/workflows/run" \
     -H "Content-Type: application/json" \
     -d '{
       "workflow_type": "feature",
       "project_id": "example-project",
       "contract_path": "design-contracts/test-feature.md",
       "dry_run": false,
       "run_codegen": false,
       "run_tests": true,
       "run_smoke": true,
       "create_pr": false
     }'
   ```
   ✅ Expected Response:
   ```json
   {
     "workflow_status": "success",
     "tests_passed": true,
     "smoke_passed": true,
     "governance_ok": null
   }
   ```

3. **Bugfix Workflow**:
   ```bash
   curl -X POST "http://localhost:8000/workflows/run" \
     -H "Content-Type: application/json" \
     -d '{
       "workflow_type": "bugfix",
       "project_id": "example-project",
       "run_tests": true,
       "run_bugfix": false
     }'
   ```
   ✅ Expected: `workflow_status: "success"` (tests pass)

### Integration Test Details

**Location**: `tests/integration/test_example_project_golden_path.py`

**Test Coverage**:
- ✅ Full feature workflow with tests + smoke
- ✅ Governance check integration
- ✅ Workflow status computation (SUCCESS, FAILED_TESTS, FAILED_SMOKE, FAILED_GOVERNANCE)
- ✅ All assertions: `tests_passed`, `smoke_passed`, `governance_ok`

**How It Works**:
1. Ensures example-project uses local path (unregisters if registered)
2. Instantiates OrchestratorAgent with ProjectRegistry
3. Runs workflow with all checks enabled
4. Asserts workflow completes with correct status

### Git Repository

- example-project is initialized as a git repository (required for RepoClient)
- Initial commit includes backend structure and design contract
- RepoClient can perform all git operations on this repo

### Use Cases

1. **Template for New Projects**: Copy structure for new projects
2. **Validation Reference**: Use to test new features and changes
3. **Demonstration**: Show end-to-end workflow functionality
4. **Integration Testing**: Validate OrchestratorAgent and workflow status computation

### Notes

- example-project uses **local path resolution** (not registered in ProjectRegistry for testing)
- Tests unregister example-project if registered to ensure local path usage
- Git repository required for RepoClient operations
- All dependencies (gitpython, openai) must be installed for full functionality
- Smoke command includes port conflict handling (`pkill` before start)

**See Also**: `docs/example_project_golden_path.md` for detailed reference guide.

---

## Notes

- All file paths use forward slashes (Unix-style)
- Python 3.11+ recommended
- FastAPI and Pydantic required
- PyYAML required for config loading
- GitPython required for git operations
- GitHub token (GITHUB_TOKEN env var) needed for private repos
- **LLM Integration**: OpenAI or Anthropic API key required for LLM-powered features
  - Set `OPENAI_API_KEY` for OpenAI (default)
  - Set `ANTHROPIC_API_KEY` for Anthropic
  - ProductAgent falls back gracefully if LLM not configured

## Architecture Changes

### v0.3: GitHub Repos Support
- Projects are now separate GitHub repositories
- Register projects via `POST /projects/register`
- ConfigLoader clones repos to `.cache/projects/{project_id}/`
- Local `configs/examples/` still supported for testing
- RepoClient handles all git operations

### Project Registry
- New `ProjectRegistry` class tracks registered projects
- Stores repo URLs and metadata in `.sanjaya/project_registry.json`
- Enables multi-project management

### v0.4: LLM-Powered ProductAgent
- **LLMClient**: Generic LLM client supporting OpenAI and Anthropic
- **ProductAgent Enhancement**: `create_feature_contract_from_idea()` method
  - Takes simple idea string → generates comprehensive design contract
  - Includes API design, data models, logging, monitoring, tests, security
  - Uses project context (tech stack, conventions) in prompts
- **New API Endpoint**: `POST /ideas/feature-from-idea`
- **Prompt Templates**: Structured prompts in `agents/product/prompts.py`
- **Backward Compatible**: Original `create_feature_contract()` still works

### v0.5: Golden Path Implementation + MonitorAgent MVP
- **example-project Golden Path**: Complete working reference implementation
  - FastAPI backend with `/health` and `/ping` endpoints
  - Unit tests (2 tests) that pass
  - Integration tests (2 tests) for golden path workflow
  - Working `autopilot.yaml` with runtime commands
  - Git repository initialized
- **MonitorAgent MVP**: On-demand log analysis
  - Rule-based pattern detection (errors, warnings, timeouts, exceptions)
  - `POST /monitor/check` endpoint
  - Structured issue reporting
- **Workflow Status Enhancement**: Detailed status computation
  - `WorkflowStatus` enum: SUCCESS, FAILED_TESTS, FAILED_SMOKE, FAILED_GOVERNANCE, ERROR
  - Status gating based on tests, smoke, and governance results
  - Response includes `workflow_status`, `tests_passed`, `smoke_passed`, `governance_ok`
- **Bugfix Workflow**: Bugfix-only workflow type
  - `workflow_type: "bugfix"` skips ProductAgent and CodegenAgent
  - Runs tests and suggests fixes via BugfixAgent if tests fail
  - Patches returned in response (not auto-applied, HITL)
- **Test Suite**: 10 tests total (all passing)
  - Golden path integration tests
  - MonitorAgent tests
  - Workflow status computation tests

### v0.6: Project Questionnaire System
- **Questionnaire Template**: `docs/project_questionnaire_template.yaml`
  - Defines structure and defaults for all questionnaire fields
  - Captures project type, architecture, UI, auth, data, constraints
- **Per-Project Questionnaire**: `.sanjaya/questionnaire.yaml`
  - Stores actual answers for each project
  - Auto-created by ProductAgent from template if missing
  - example-project has working questionnaire
- **ConfigLoader Integration**:
  - `load_project_questionnaire()` loads questionnaire.yaml
  - `_flatten_questionnaire_intent()` converts nested structure to flat dict
  - `load_project_config()` automatically attaches `config["intent"]`
- **ProductAgent Integration**:
  - `ensure_project_questionnaire()` creates questionnaire if missing
  - Uses intent in LLM prompts for design contract generation
  - Adds "Project Intent" section to generated contracts
  - Respects intent constraints (no UI if ui=none, no auth if disabled)
  - **NEW**: Checks `intent.locked` flag (raises error if locked, prevents contract creation)
  - **NEW**: Checks confidence threshold (raises error if below threshold)
  - **NEW**: Respects `out_of_scope` guardrail in prompts (explicitly forbids features)
  - **NEW**: Snapshots intent in design contracts for immutability (with hash)
- **CodegenAgent Integration**:
  - Reads `config["intent"]` for scaffolding decisions
  - Only scaffolds UI if `intent["ui"] != "none"`
  - Skips auth scaffolding if `intent["auth_enabled"] == False`
  - Uses `intent["backend"]` for backend stack decisions
- **High-Leverage Refinements**:
  - **Intent Lock** (`intent.locked`): Prevents ProductAgent from suggesting architecture changes
  - **Confidence Enforcement** (`project_meta.confidence`, `min_confidence_required`): Requires minimum confidence before proceeding
  - **Out of Scope Guardrail** (`constraints.out_of_scope`): Explicitly forbids certain features to prevent scope creep
  - **Intent Snapshot**: Immutable snapshot in design contracts for reproducibility and diffing
- **Benefits**:
  - Explicit project intent (no magic names)
  - Consistent decisions across all agents
  - Prevents LLM drift and scope creep
  - Immutable design contract history
  - Future-proof and extensible
  - Human-readable YAML format
- **Test Suite**: 20 tests total (all passing)
  - 6 tests for intent flattening (including refinements)
  - 4 tests for ProductAgent refinements (locked, confidence, snapshot)
  - All existing tests still pass

---

**Document Version**: 1.3  
**Last Updated**: December 2024  
**Maintained By**: Development Team

---

## Quick Reference: Running the Golden Path

### 1. Start API Server
```bash
cd /Volumes/workplace/sanjaya-app
python3 -m uvicorn autopilot_core.main_service.api:app --reload
```

### 2. Run Golden Path Integration Test
```bash
pytest tests/integration/test_example_project_golden_path.py -v
```

### 3. Run Full Test Suite
```bash
pytest tests/ -v
```
**Expected**: 10 tests pass

### 4. Test example-project Backend Manually
```bash
cd configs/examples/example-project/backend
. .venv/bin/activate
pytest -q  # 2 tests pass
uvicorn app.main:app --reload  # Test /health and /ping endpoints
```

### 5. Run Workflow via API
```bash
curl -X POST "http://localhost:8000/workflows/run" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "feature",
    "project_id": "example-project",
    "contract_path": "design-contracts/test-feature.md",
    "dry_run": false,
    "run_tests": true,
    "run_smoke": true
  }'
```

**See Also**:
- `docs/example_project_golden_path.md` - Detailed golden path reference
- `docs/example_project_final_summary.md` - Implementation summary
- `docs/agent_status_report.md` - Agent status details

