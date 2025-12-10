# Project Questionnaire Overview

## Purpose

The Project Questionnaire is a structured way to capture high-level project intent, making projects like "lemonade-stand" driven by explicit configuration rather than vague names.

## Location

Each project has a questionnaire file at:
```
<project_root>/.sanjaya/questionnaire.yaml
```

## Template

The questionnaire template is located at:
```
docs/project_questionnaire_template.yaml
```

This template defines the structure and default values for all questionnaire fields.

## Structure

The questionnaire captures:

- **Project Metadata**: Name, description, confidence level, and minimum confidence threshold
- **Project Type**: demo, internal_tool, or production
- **Architecture**: UI type (none/web/mobile) and backend stack (fastapi/node/none)
- **UI Details**: Framework (nextjs/react/none) and key pages
- **Authentication**: Enabled/disabled and providers
- **Data**: Persistence (none/sqlite/postgres) and multi-user support
- **Constraints**: Complexity level, monitoring, test requirements, and out-of-scope features
- **Intent Lock**: Flag to prevent ProductAgent from suggesting changes or re-interpreting architecture

## Integration

### ConfigLoader

The `ConfigLoader` automatically:
1. Loads `questionnaire.yaml` when loading project config
2. Flattens the nested structure into a simple `intent` dict
3. Attaches `intent` to the project config as `config["intent"]`

**Example**:
```python
config = config_loader.load_project_config("example-project")
intent = config["intent"]  # Flattened questionnaire answers
# {
#   "project_type": "demo",
#   "ui": "none",
#   "backend": "fastapi",
#   "auth_enabled": False,
#   "persistence": "none",
#   ...
# }
```

### ProductAgent

The `ProductAgent`:
1. **Ensures questionnaire exists**: `ensure_project_questionnaire()` creates it from template if missing
2. **Checks intent lock**: If `intent.locked == True`, raises error preventing contract creation
3. **Checks confidence threshold**: If confidence < min_confidence_required, raises error
4. **Uses intent in design contracts**: Questionnaire answers are included in LLM prompts
5. **Respects out_of_scope**: Features listed as out_of_scope are explicitly forbidden in prompts
6. **Adds Project Intent section**: Design contracts include a "Project Intent" section summarizing questionnaire answers
7. **Snapshots intent**: Design contracts include an immutable "Project Intent Snapshot" with hash for verification

**Example**:
```python
product_agent = ProductAgent()
# Automatically ensures questionnaire exists
questionnaire = product_agent.ensure_project_questionnaire("example-project")

# Intent is used when generating design contracts
contract = product_agent.create_feature_contract_from_idea(
    project_id="example-project",
    idea="Add a health check endpoint"
)
# Design contract includes:
# - Project Intent section (current intent)
# - Project Intent Snapshot (immutable snapshot with hash)
```

**Locked Intent Behavior**:
- If `intent.locked == True`, ProductAgent raises `ValueError` before generating contracts
- Prevents "helpful" LLM drift from suggesting architecture changes
- Forces strict compliance mode

**Confidence Enforcement**:
- If `confidence < min_confidence_required`, ProductAgent raises `ValueError`
- Future: Could trigger exactly ONE clarifying question (not implemented yet)
- Keeps UX sharp and avoids chatty loops

**Out of Scope Guardrail**:
- Features in `constraints.out_of_scope` are explicitly forbidden
- LLM prompt includes: "DO NOT design, scaffold, or mention these features"
- Stops scope creep as ideas grow

### CodegenAgent

The `CodegenAgent` uses `config["intent"]` to make decisions:

- **Backend scaffolding**: Only scaffolds FastAPI if `intent["backend"] == "fastapi"`
- **UI scaffolding**: Only scaffolds Next.js if `intent["ui"] == "web"` and `intent["ui_framework"] == "nextjs"`
- **Auth scaffolding**: Skips auth if `intent["auth_enabled"] == False`
- **Persistence**: Respects `intent["persistence"]` (none/sqlite/postgres)

**Example**:
```python
codegen_agent = CodegenAgent()
intent = project_config.get("intent", {})

# Only scaffold UI if intent says so
if intent.get("ui") == "web" and intent.get("ui_framework") == "nextjs":
    scaffold_nextjs_ui()

# Skip auth if disabled
if not intent.get("auth_enabled"):
    skip_auth_scaffolding()
```

## Flattened Intent Structure

The `_flatten_questionnaire_intent()` method converts the nested questionnaire into:

```python
{
    "project_type": "demo",
    "ui": "web",                    # or "none", "mobile"
    "backend": "fastapi",           # or "node", "none"
    "ui_framework": "nextjs",      # or "react", "none"
    "ui_pages": ["landing", "form"],
    "auth_enabled": False,
    "auth_providers": [],
    "persistence": "none",          # or "sqlite", "postgres"
    "multi_user": False,
    "complexity": "toy",            # or "simple", "realistic"
    "monitoring": True,
    "tests_required": True,
    "out_of_scope": [],            # List of features explicitly out of scope
    "locked": False,                # If True, prevents ProductAgent from suggesting changes
    "confidence": 0.85,            # Confidence level (0.0-1.0)
    "min_confidence_required": 0.75  # Minimum confidence threshold
}
```

## Creating a Questionnaire

### Manual Creation

1. Copy `docs/project_questionnaire_template.yaml` to `<project_root>/.sanjaya/questionnaire.yaml`
2. Edit values to match your project
3. Ensure `project_meta.name` matches your project_id

### Automatic Creation

The `ProductAgent.ensure_project_questionnaire()` method automatically creates a questionnaire from the template if it doesn't exist:

```python
product_agent = ProductAgent()
questionnaire = product_agent.ensure_project_questionnaire("my-project")
# Creates .sanjaya/questionnaire.yaml if missing
```

## Example: example-project

The `example-project` has a questionnaire at:
```
configs/examples/example-project/.sanjaya/questionnaire.yaml
```

This questionnaire specifies:
- Project type: demo
- UI: none (backend-only)
- Backend: fastapi
- Auth: disabled
- Persistence: none
- Complexity: toy
- Monitoring: enabled
- Tests required: true

This intent is automatically available to all agents via `config["intent"]`.

## Benefits

1. **Explicit Intent**: Projects declare their architecture and constraints upfront
2. **Consistent Decisions**: All agents use the same intent for decision-making
3. **No Magic Names**: Project behavior is driven by questionnaire, not naming conventions
4. **Future-Proof**: Easy to extend with new fields without breaking existing projects
5. **Human-Readable**: YAML format is easy to edit manually or via future tools

## High-Leverage Refinements

### 1. Intent Lock (`intent.locked`)

**Purpose**: Prevent ProductAgent from suggesting changes or re-interpreting architecture.

**Behavior**:
- If `locked: true`, ProductAgent raises `ValueError` before creating contracts
- Forces strict compliance mode
- Prevents "helpful" LLM drift later

**Example**:
```yaml
intent:
  locked: true
```

### 2. Confidence Enforcement (`project_meta.confidence`, `project_meta.min_confidence_required`)

**Purpose**: Ensure sufficient confidence before proceeding with design contracts.

**Behavior**:
- If `confidence < min_confidence_required`, ProductAgent raises `ValueError`
- Future: Could trigger exactly ONE clarifying question (not implemented yet)
- Keeps UX sharp and avoids chatty loops

**Example**:
```yaml
project_meta:
  confidence: 0.83
  min_confidence_required: 0.75
```

### 3. Out of Scope Guardrail (`constraints.out_of_scope`)

**Purpose**: Explicitly forbid certain features/domains to prevent scope creep.

**Behavior**:
- Features listed in `out_of_scope` are explicitly forbidden in LLM prompts
- DesignAgent prompt rule: "Features listed as out_of_scope must not be designed, scaffolded, or mentioned"
- Stops scope creep as ideas grow

**Example**:
```yaml
constraints:
  out_of_scope:
    value: ["payments", "notifications", "admin panel"]
```

### 4. Intent Snapshot in Design Contracts

**Purpose**: Immutability - later changes to questionnaire won't silently invalidate past designs.

**Behavior**:
- When creating a design contract, ProductAgent snapshots the current intent
- Snapshot includes all intent fields plus a hash for verification
- Design contract includes "Project Intent Snapshot" section
- Enables reproducibility and diffing

**Example** (in design contract):
```yaml
## Project Intent Snapshot

project_intent_snapshot:
  ui: none
  auth_enabled: false
  backend: fastapi
  # ... all other intent fields

Snapshot Hash: abc123def456
```

## Future Enhancements

- UI tool for editing questionnaires
- Validation of questionnaire values
- Migration tools for updating questionnaire structure
- Integration with project creation workflows
- Single clarifying question when confidence is below threshold

