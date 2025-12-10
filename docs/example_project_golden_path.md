# Example Project - Golden Path Reference

**Status**: ✅ **Complete and Working**

The `configs/examples/example-project/` directory is now a fully functional "golden path" reference implementation that demonstrates the complete Sanjaya workflow.

## Structure

```
configs/examples/example-project/
├── .sanjaya/
│   ├── autopilot.yaml          # Project configuration
│   └── design-contracts/
│       └── test-feature.md     # Sample design contract
└── backend/
    ├── app/
    │   ├── __init__.py
    │   └── main.py              # FastAPI app with /health and /ping
    ├── tests/
    │   ├── __init__.py
    │   └── test_health.py       # Tests for health endpoint
    └── requirements.txt         # Python dependencies
```

## FastAPI Application

**Location**: `backend/app/main.py`

**Endpoints**:
- `GET /health` → Returns `{"status": "ok"}`
- `GET /ping` → Returns `{"message": "pong"}`

**Usage**:
```bash
cd configs/examples/example-project/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Configuration

**Location**: `.sanjaya/autopilot.yaml`

**Key Settings**:
- `backend_dir: "backend"` - Points to FastAPI backend
- `tests_dir: "backend/tests"` - Points to test directory
- `runtime.backend_fastapi` - Defines install, test, smoke, and dev commands

## Running Tests

**Unit Tests**:
```bash
cd configs/examples/example-project/backend
. .venv/bin/activate
pytest -q
```

**Expected Output**: 2 tests pass (test_health, test_ping)

## Running Smoke Tests

**Via autopilot.yaml command**:
```bash
cd configs/examples/example-project
cd backend && . .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000 & sleep 3 && curl -f http://127.0.0.1:8000/health && pkill -f 'uvicorn app.main:app'
```

**Expected**: Server starts, health check passes, server stops

## End-to-End Workflow

The example-project can now run the complete Sanjaya workflow:

1. **Dry Run** (Validation):
   ```python
   orchestrator.run_feature_workflow(
       project_id="example-project",
       contract_path="design-contracts/test-feature.md",
       dry_run=True
   )
   ```
   ✅ Status: `accepted`

2. **Full Workflow with Tests**:
   ```python
   orchestrator.run_feature_workflow(
       project_id="example-project",
       contract_path="design-contracts/test-feature.md",
       dry_run=False,
       run_tests=True
   )
   ```
   ✅ Status: `SUCCESS` (tests pass)

3. **Bugfix Workflow**:
   ```python
   orchestrator.run_bugfix_workflow(
       project_id="example-project",
       run_tests=True
   )
   ```
   ✅ Status: `SUCCESS` (tests pass)

## Integration Tests

**Location**: `tests/test_example_project_workflow.py`

**Test Coverage**:
- ✅ Dry-run workflow validation
- ✅ Full workflow with test execution
- ✅ Bugfix workflow execution

**Run Tests**:
```bash
pytest tests/test_example_project_workflow.py -v
```

## Notes

- **Git Repository**: example-project is initialized as a git repository (required for RepoClient)
- **Local Path**: example-project uses local path resolution (not registered in ProjectRegistry for testing)
- **Dependencies**: Requires gitpython, openai (or anthropic) for full functionality
- **Golden Path**: This project serves as the reference implementation for how Sanjaya workflows should work

## Next Steps

This golden path can now be used to:
1. Test new agent features
2. Demonstrate end-to-end workflows
3. Serve as a template for new projects
4. Validate changes to OrchestratorAgent or other core components

