# Developer Guide: Adding a Safe Tool

**Workstream:** W4 — Agentic Workflow Engine (Week 4 / Days 22–30)  
**Team:** SDE 2 (`projects/sde-2-voicebot/`)  
**Author:** Karthik N M  
**Document Version:** 1.0.0 (Release Candidate)  

---

## 1. Safety Principles & Invariants

When introducing a new tool to the Academiaai Voicebot workflow engine, you must adhere to the following strict safety principles:

1. **Sandboxed & Harmless Mock Execution:** In mock mode, tools must operate entirely in-memory or on local fixtures. Never perform live network calls, unauthorized filesystem mutations, or send live emails/notifications without sandbox isolation.
2. **Single Source of Truth:** Reuse existing schema definitions (`ToolSpec`, `RiskLevel`, `ToolFailureBehavior` from `src.workflow.schemas`). Do **NOT** redefine schemas elsewhere.
3. **Risk Tiering (PRD Section 18):**
   - **INFORMATIONAL (Category A):** Read-only queries (e.g. searching FAQs, checking schedules). No state modification. Auto-executable.
   - **LOW_RISK (Category B):** Read queries touching personalized or non-critical records within caller scope.
   - **SENSITIVE (Category C):** Mutates records, enrollments, or profile data. **Mandatory human approval gate.**
   - **DESTRUCTIVE (Category D):** Deletes, drops, or permanently alters accounts/data. **Mandatory human approval gate + zero retries.**
4. **Input Defense:** Always reject path traversal sequences (`../`, `..\\`), null bytes (`\x00`), and out-of-scope arguments.

---

## 2. Step-by-Step Implementation Guide

### Step 1: Subclass `BaseTool` and Define `ToolSpec`
Create your tool class inheriting from `src.workflow.tools.BaseTool`:

```python
from typing import Any, Dict
from datetime import datetime, timezone
from src.workflow.schemas import RiskLevel, ToolFailureBehavior, ToolSpec
from src.workflow.tools import BaseTool

class MockLibraryBookLookupTool(BaseTool):
    """
    Looks up library book availability and shelf location.
    Risk Tier: INFORMATIONAL.
    """

    def __init__(self):
        spec = ToolSpec(
            name="library_book_lookup",
            purpose="Retrieves book availability, call number, and shelf location in the university library.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "isbn": {
                        "type": "string",
                        "description": "Standard 10 or 13 character ISBN identifier",
                    },
                    "include_shelf_map": {
                        "type": "boolean",
                        "description": "Whether to return floor plan coordinates",
                        "default": False,
                    },
                },
                "required": ["isbn"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "isbn": {"type": "string"},
                    "title": {"type": "string"},
                    "available": {"type": "boolean"},
                    "shelf_location": {"type": "string"},
                    "mock_mode": {"type": "boolean"},
                },
            },
            permission_requirements=["library:read"],
            risk_level=RiskLevel.INFORMATIONAL,
            failure_behavior=ToolFailureBehavior.FAIL_WORKFLOW,
        )
        super().__init__(spec)
```

### Step 2: Implement `execute()` with Argument Validation
`BaseTool.validate_arguments()` automatically validates required arguments, expected types, path traversal sequences, and bounds. Implement `execute()` safely:

```python
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Validate arguments against input_schema
        self.validate_arguments(arguments)

        isbn = arguments["isbn"].strip().upper()
        include_shelf = arguments.get("include_shelf_map", False)

        # 2. Mock business logic in-memory
        return {
            "status": "success",
            "isbn": isbn,
            "title": f"Academic Book Volume ({isbn})",
            "available": True,
            "shelf_location": "Main Library, 3rd Floor, Section B-14",
            "mock_mode": True,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }
```

### Step 3: Register in `ToolRegistry`
Add the new tool to your `ToolRegistry`:

```python
from src.workflow.tools import ToolRegistry

registry = ToolRegistry.get_default_registry()
registry.register(MockLibraryBookLookupTool())
```

### Step 4: Add Policy Rule to `PolicyMatrix`
Update `src/workflow/policy.py` (`PolicyMatrix._load_default_matrix()`) to record the official policy entry:

```python
PolicyRule(
    tool_name="library_book_lookup",
    risk_level=RiskLevel.INFORMATIONAL,
    approval_required=False,
    allowed_caller_permissions=["library:read"],
    failure_behavior=ToolFailureBehavior.FAIL_WORKFLOW,
    max_timeout_seconds=30.0,
    allow_retries=True,
    description="Read-only query of library inventory and availability.",
)
```

Also add the corresponding row to `POLICY_MATRIX.md`.

---

## 3. Required Test Coverage Checklist

Before submitting a Pull Request for any new tool, verify that the following tests pass:

- [ ] **Schema Conformance:** Tool's `ToolSpec` passes Pydantic validation.
- [ ] **Happy Path Test:** Valid inputs return the expected mock schema response.
- [ ] **Argument Validation Tests:**
  - [ ] Missing required arguments raise `ValueError`.
  - [ ] Invalid argument types (e.g. integer passed for string) raise `ValueError`.
  - [ ] Out-of-scope extra arguments raise `ValueError` (`additionalProperties: False`).
  - [ ] Path traversal strings (`../../etc/passwd`) raise `ValueError`.
  - [ ] Null bytes (`\x00`) raise `ValueError`.
- [ ] **Permission Tests:** Caller without declared permission scope raises `PermissionError`.
- [ ] **Approval Gating (if SENSITIVE or DESTRUCTIVE):**
  - [ ] Workflow automatically halts in `AWAITING_APPROVAL`.
  - [ ] Rejection strictly guarantees tool `execute()` is never called (`call_count == 0`).
  - [ ] Expiry strictly guarantees zero tool execution (`call_count == 0`).
- [ ] **Policy Matrix Test:** Row passes `PolicyMatrix.enforce_step()`.
- [ ] **Deterministic Replay Test:** Execution trace can be recorded and verified with `ReplayEngine`.
