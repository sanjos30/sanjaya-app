# Fix Core MVP Plan

**Based on**: ChatGPT review + actual codebase analysis  
**Date**: December 2024

## Actual State Assessment

### ✅ What's Already Working

1. **ProjectRegistry** - Fully implemented (not a stub!)
2. **ConfigLoader** - Has `get_repo_path()` implemented
3. **RepoClient** - Has `get_diff()`, `set_repo_path()`, all core methods
4. **BugfixAgent** - Has `BugfixRequest`, `suggest_fixes()` implemented
5. **GovernanceAgent** - Has `GovernanceResult`, `evaluate()` implemented
6. **ProductAgent** - Has `create_feature_contract_from_idea()` with LLM
7. **CodegenAgent** - Has `generate_code()`, `generate_tests()` with LLM
8. **Tests** - All 5 tests pass ✅

### ❌ What's Actually Missing

1. **example-project backend** - The directory `configs/examples/example-project/backend/` doesn't exist
2. **End-to-end verification** - Can't actually run a workflow on example-project because backend is missing
3. **Documentation accuracy** - Docs may overstate completion in some areas

## Real Gaps to Fix

### Gap 1: example-project Backend Structure
- Missing: `configs/examples/example-project/backend/` directory
- Missing: FastAPI app with `/health` endpoint
- Missing: Tests that actually pass
- Missing: Proper project structure

### Gap 2: End-to-End Workflow Verification
- Need: A test that runs a full feature workflow on example-project
- Need: Verify tests actually run
- Need: Verify smoke tests actually run

### Gap 3: Documentation Accuracy
- Need: Update `docs/agent_status_report.md` to reflect actual state
- Need: Document what's MVP vs full implementation

## Implementation Plan

### Step 1: Create example-project Backend (HIGH PRIORITY)

**Goal**: Make `configs/examples/example-project/` a real, working FastAPI project

1. Create directory structure:
   ```
   configs/examples/example-project/
   ├── .sanjaya/
   │   └── autopilot.yaml (already exists)
   └── backend/
       ├── app/
       │   ├── __init__.py
       │   └── main.py (FastAPI app with /health)
       ├── tests/
       │   ├── __init__.py
       │   └── test_health.py
       └── requirements.txt
   ```

2. Create `backend/app/main.py`:
   ```python
   from fastapi import FastAPI
   
   app = FastAPI(title="Example Project")
   
   @app.get("/health")
   def health():
       return {"status": "ok"}
   
   @app.get("/ping")
   def ping():
       return {"message": "pong"}
   ```

3. Create `backend/tests/test_health.py`:
   ```python
   from fastapi.testclient import TestClient
   from app.main import app
   
   client = TestClient(app)
   
   def test_health():
       response = client.get("/health")
       assert response.status_code == 200
       assert response.json() == {"status": "ok"}
   ```

4. Create `backend/requirements.txt`:
   ```
   fastapi
   uvicorn[standard]
   pytest
   httpx
   ```

### Step 2: Update autopilot.yaml (if needed)

**Current config looks good**, but verify paths are correct:
- `backend_dir: "backend"` ✅
- `tests_dir: "backend/tests"` ✅
- Runtime commands reference `backend` ✅

**May need to adjust**:
- Commands should run from `configs/examples/example-project/` root
- Verify `BACKEND_DIR` env var usage in smoke scripts

### Step 3: Add End-to-End Integration Test

**Goal**: Verify full workflow works on example-project

1. Create `tests/test_example_project_workflow.py`:
   ```python
   def test_example_project_feature_workflow():
       """Test that a feature workflow can run on example-project."""
       from agents.orchestrator.orchestrator_agent import OrchestratorAgent
       from autopilot_core.config.project_registry import ProjectRegistry
       
       registry = ProjectRegistry()
       orchestrator = OrchestratorAgent(project_registry=registry)
       
       # Create a simple design contract first
       # Then run workflow
       # Assert workflow_status == SUCCESS
   ```

2. Test scenarios:
   - Dry run (validation only)
   - Full workflow with tests
   - Full workflow with smoke tests

### Step 4: Verify Smoke Scripts Work

**Goal**: Ensure smoke scripts can find and test example-project backend

1. Test manually:
   ```bash
   cd configs/examples/example-project
   BACKEND_DIR=backend bash ../../scripts/smoke_fastapi.sh
   ```

2. Fix any path issues in smoke scripts or commands

### Step 5: Update Documentation

**Goal**: Make docs match reality

1. Update `docs/agent_status_report.md`:
   - Mark what's actually MVP vs full
   - Note that example-project needs backend (or mark as complete after Step 1)

2. Add note about example-project being the golden path reference

## Priority Order

1. **Step 1** (Create backend) - Blocks everything else
2. **Step 2** (Verify config) - Quick check
3. **Step 3** (Integration test) - Proves it works
4. **Step 4** (Smoke verification) - Ensures end-to-end
5. **Step 5** (Docs) - Cleanup

## Estimated Time

- Step 1: 30 minutes
- Step 2: 10 minutes  
- Step 3: 30 minutes
- Step 4: 20 minutes
- Step 5: 15 minutes

**Total: ~2 hours**

## Success Criteria

✅ `configs/examples/example-project/backend/` exists with working FastAPI app  
✅ `pytest configs/examples/example-project/backend/tests/` passes  
✅ Smoke test runs successfully  
✅ Integration test passes  
✅ Documentation accurately reflects state  

## ✅ IMPLEMENTATION COMPLETE

All steps have been implemented:

- ✅ **Step 1**: Backend structure created with FastAPI app, tests, and requirements.txt
- ✅ **Step 2**: autopilot.yaml updated with working runtime commands
- ✅ **Step 3**: Golden path integration test added in `tests/integration/test_example_project_golden_path.py`
- ✅ **Step 4**: Documentation updated
- ✅ **Step 5**: All tests pass, FastAPI app verified manually

**Golden Path Test**: `tests/integration/test_example_project_golden_path.py::test_example_project_golden_path_workflow`  

