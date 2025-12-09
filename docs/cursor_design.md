# Sanjaya Autopilot — Implementation Design Document

**Last Updated**: December 2024  
**Version**: v0.2 (Step 2 Implementation)

This document tracks the current implementation state of the Sanjaya Autopilot platform, including what has been built, how it works, and what remains to be implemented.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current Implementation Status](#current-implementation-status)
3. [API Endpoints](#api-endpoints)
4. [Agent Implementations](#agent-implementations)
5. [File Structure & Conventions](#file-structure--conventions)
6. [Path Handling](#path-handling)
7. [Data Models](#data-models)
8. [Workflow Flow](#workflow-flow)
9. [What's Working](#whats-working)
10. [What's Stubbed](#whats-stubbed)
11. [Usage Examples](#usage-examples)

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

### ✅ Implemented (v0.2)

1. **API Service** (`autopilot_core/main_service/api.py`)
   - FastAPI service with multiple endpoints
   - Request/Response models using Pydantic
   - Error handling with HTTPException

2. **OrchestratorAgent** (`agents/orchestrator/orchestrator_agent.py`)
   - Loads project configurations
   - Validates design contract files
   - Returns structured workflow plans
   - Generates workflow IDs

3. **ProductAgent v0** (`agents/product/product_agent.py`)
   - Creates feature design contracts from structured input
   - Slugifies feature names for filesystem safety
   - Writes markdown files with standard template

4. **ConfigLoader** (`autopilot_core/config/loader.py`)
   - Loads per-project `autopilot.yaml` configurations
   - YAML parsing with error handling

### ⏳ Stubbed (Not Yet Implemented)

1. **CodegenAgent** - Code generation from design contracts
2. **BugfixAgent** - Bugfix patch generation
3. **MonitorAgent** - Log monitoring and issue detection
4. **GovernanceAgent** - Safety rule enforcement
5. **MarketingAgent** - Marketing content generation
6. **Full Workflow Execution** - Currently only validates inputs
7. **Pull Request Creation** - PR generation not implemented
8. **Test Execution** - Test running not implemented

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

**Response**: TBD (currently returns `pass`)

**Status**: ⏳ Stubbed

---

#### 3. `POST /workflows/run`
**Purpose**: Execute a workflow (feature development, bugfix, etc.)

**Request Model**: `WorkflowRunRequest`
```json
{
  "workflow_type": "feature_from_contract",
  "project_id": "example-project",
  "contract_path": "design-contracts/lemonade-stand-planner.md",
  "dry_run": true
}
```

**Response Model**: `WorkflowRunResponse`
```json
{
  "workflow_id": "wf-example-project-2024-12-08T18:30:00",
  "status": "accepted",
  "message": "Feature workflow validated (stub)",
  "details": {
    "project_id": "example-project",
    "autopilot_config": {...},
    "design_contract": "design-contracts/lemonade-stand-planner.md",
    "dry_run": true,
    "workflow_steps": [...]
  }
}
```

**Status**: ✅ Partially Implemented (validation only, execution stubbed)

---

#### 4. `POST /ideas/feature`
**Purpose**: Create a feature design contract from a feature idea

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
- Creates feature design contracts from structured input
- Slugifies feature names for filesystem safety
- Writes markdown files with standard template

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

#### `_slugify(text: str) -> str`
- Converts text to filesystem-safe slug
- Lowercase, hyphens instead of spaces
- Removes special characters
- Example: `"Lemonade Stand Planner"` → `"lemonade-stand-planner"`

**Status**: ✅ Fully Implemented (v0)

---

### 3. ConfigLoader

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

## File Structure & Conventions

### Project Structure
```
sanjaya-app/
├── autopilot_core/              # Core platform code
│   ├── __init__.py
│   ├── main_service/
│   │   ├── __init__.py
│   │   └── api.py              # FastAPI service
│   ├── config/
│   │   ├── __init__.py
│   │   └── loader.py           # Config loader
│   └── workflows/               # Workflow definitions (stubbed)
├── agents/                      # Agent implementations
│   ├── __init__.py
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   └── orchestrator_agent.py
│   ├── product/
│   │   ├── __init__.py
│   │   └── product_agent.py
│   └── [other agents - stubbed]
├── configs/
│   ├── global-settings.yaml
│   ├── autopilot-schema.yaml
│   └── examples/
│       ├── autopilot-example.yaml
│       └── example-project/
│           └── .sanjaya/
│               ├── autopilot.yaml
│               └── design-contracts/
│                   └── [feature contracts]
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

### Project Configuration Structure

Each project under `configs/examples/{project_id}/` must have:
```
.sanjaya/
├── autopilot.yaml              # Project configuration
└── design-contracts/           # Feature design contracts
    └── {slugified-feature-name}.md
```

---

## Path Handling

### Path Conventions

1. **Contract Path Format** (relative to `.sanjaya/`):
   ```
   design-contracts/{slugified-feature-name}.md
   ```
   Example: `design-contracts/lemonade-stand-planner.md`

2. **Full Path Construction**:
   ```
   configs/examples/{project_id}/.sanjaya/{contract_path}
   ```
   Example: `configs/examples/example-project/.sanjaya/design-contracts/lemonade-stand-planner.md`

3. **Config Path**:
   ```
   configs/examples/{project_id}/.sanjaya/autopilot.yaml
   ```

### Path Consistency

- **ProductAgent** returns `contract_path` relative to `.sanjaya/`
- **OrchestratorAgent** expects `contract_path` relative to `.sanjaya/`
- Both agents construct full paths using the same pattern
- This ensures compatibility between agents

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
  "status": Literal["accepted", "rejected", "error"],
  "message": str,
  "details": Dict[str, Any]    # Workflow details
}
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
1. POST /ideas/feature
   ↓
2. ProductAgent.create_feature_contract()
   - Slugifies feature name
   - Creates design-contracts directory
   - Writes markdown file
   - Returns contract_path
   ↓
3. POST /workflows/run
   ↓
4. OrchestratorAgent.run_feature_workflow()
   - Generates workflow ID
   - Loads project config (ConfigLoader)
   - Validates contract file exists
   - Returns workflow plan (stub)
   ↓
5. [STUBBED] CodegenAgent.generate_code()
   ↓
6. [STUBBED] Test execution
   ↓
7. [STUBBED] Pull Request creation
   ↓
8. Human reviews and approves
```

### Current Limitations

- Workflow execution stops after validation
- Code generation not implemented
- PR creation not implemented
- Test execution not implemented

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
   - Returns structured responses
   - Does not execute actual workflow steps

---

## What's Stubbed

### Agents (Stub Status)

1. **CodegenAgent** - Stub only
2. **BugfixAgent** - Stub only
3. **MonitorAgent** - Stub only
4. **GovernanceAgent** - Stub only
5. **MarketingAgent** - Stub only

### Workflow Steps (Stubbed)

1. Code generation from design contracts
2. Test execution
3. Pull request creation
4. Actual workflow orchestration

### Endpoints (Stubbed)

1. `GET /projects` - Returns `pass`

---

## Usage Examples

### Example 1: Create a Feature Design Contract

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

### Example 2: Run a Feature Workflow

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
  "message": "Feature workflow validated (stub)",
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
      "invoke_codegen_agent (stub)",
      "run_tests (stub)",
      "prepare_pull_request (stub)"
    ]
  }
}
```

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
- **Decision**: All example projects under `configs/examples/`
- **Rationale**: Clear separation between platform code and project configs
- **Impact**: ConfigLoader assumes this structure

### 4. Stub-First Approach
- **Decision**: Implement validation before execution
- **Rationale**: Allows testing of structure and flow before complex logic
- **Impact**: Current workflows validate but don't execute

---

## Next Steps

### Immediate Priorities

1. **CodegenAgent Implementation**
   - Read design contracts
   - Generate code based on project stack
   - Create test files

2. **Workflow Execution**
   - Connect OrchestratorAgent to CodegenAgent
   - Implement actual workflow steps
   - Add error handling

3. **Pull Request Creation**
   - Integrate GitHub client
   - Create branches
   - Generate PRs

### Future Enhancements

1. LLM integration for ProductAgent
2. GovernanceAgent safety checks
3. MonitorAgent log analysis
4. BugfixAgent implementation
5. MarketingAgent content generation

---

## Notes

- All file paths use forward slashes (Unix-style)
- Python 3.11+ recommended
- FastAPI and Pydantic required
- PyYAML required for config loading
- No LLM integration yet (v0 is template-based)

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Maintained By**: Development Team

