# Academia AI Voice Co-Pilot — SDE Internship

**Contributor:** Karthik N M  
**Role:** SDE 2  
**Email:** karthiknm8050@gmail.com  
**Repository:** [https://github.com/KARTHIK-NM/SDE](https://github.com/KARTHIK-NM/SDE)  
**Branch:** `main` & `team/sde-2-voicebot`  

---

## Project Overview

This repository contains the complete codebase and documentation for the **Academia AI Voice Co-Pilot** SDE Internship, covering both **Week 1** and **Week 2** for **Workstream W4: Agentic Workflow Engine**.

The goal of this system is to provide a persistent, context-aware, multimodal agentic AI assistance layer that runs safely on a user's machine — supporting natural voice interactions, visual and document understanding, human-in-the-loop safety gating, and controlled tool execution.

---

## Repository Structure

```
.
├── WEEK1/
│   └── voicebot-SDE2-teamm-karthik-nm/
│       ├── projects/
│       │   └── sde-2-voicebot/
│       │       ├── demo.py                             # Week 1 demonstration script
│       │       ├── src/workflow/                       # Core workflow engine
│       │       │   ├── executor.py                     # Workflow execution & approval gating
│       │       │   ├── schemas.py                      # Data schemas & contracts
│       │       │   ├── state_machine.py                # 7-state lifecycle state machine
│       │       │   ├── tools.py                        # Harmless mock tools & tool registry
│       │       │   ├── validator.py                    # Plan validation (cycles & missing deps)
│       │       │   └── README.md                       # Workflow module documentation
│       │       └── tests/                              # Week 1 test suite (35+ unit tests)
│       │           ├── test_invalid_plans_and_transitions.py
│       │           ├── test_mock_tools_and_executor.py
│       │           ├── test_week2_policy_and_safe_executor.py
│       │           └── test_workflow_schemas_and_sm.py
│       ├── README.md                                   # Week 1 team documentation
│       ├── project_explanation.md                      # Detailed technical architecture guide
│       └── week1_explanation.md                        # Day-by-day implementation breakdown
│
└── WEEK2/
    ├── projects/
    │   └── sde-2-voicebot/
    │       ├── schemas.py                              # Shared Pydantic schemas (Week 1 base)
    │       ├── plan_validator.py                       # Dependency & cycle validation (Kahn's algo)
    │       ├── tool_registry.py                        # Allow-listed registry with arg & scope validation
    │       ├── approval_manager.py                     # Human-in-the-loop approval, reject & TTL expiry
    │       ├── safe_executor.py                        # Safe executor (timeouts, retries, cancellation)
    │       ├── mock_tools.py                           # Harmless mock tools (no external network/FS write)
    │       ├── requirements.txt                        # Dependencies
    │       ├── README.md                               # Week 2 module documentation
    │       └── tests/                                  # Full test suite (55 tests passing, zero warnings)
    │           ├── conftest.py                         # Shared pytest fixtures & test helpers
    │           ├── test_plan_validator.py              # Tests for plan validation
    │           ├── test_tool_registry.py               # Tests for registry & scopes
    │           ├── test_approval_manager.py            # Tests for approval & expiry
    │           ├── test_safe_executor.py               # Tests for execution, timeouts, retries
    │           └── test_demo.py                        # D14 end-to-end approved vs rejected demo
    └── README.md                                       # Week 2 overview
```

---

## Deliverables Summary

### Week 1 (Days 1–7): Foundation & First Vertical Slice
- **Days 1–2:** Schemas (`WorkflowPlan`, `WorkflowStep`, `ToolSpec`, `ApprovalRequest`, `WorkflowResult`) and 7-state lifecycle state machine.
- **Days 3–4:** Two harmless mock tools (`knowledge_search`, `course_schedule`) with no external sending, `ToolRegistry`, and `WorkflowExecutor` with approval gating.
- **Days 5–6:** Unit test suite validating invalid plans (cycles, missing dependencies, duplicate IDs) and state transitions.
- **Day 7:** Demonstration script (`demo.py`) running harmless, approved, and rejected execution scenarios.

### Week 2 (Days 8–14): Plan Validation, Tool Registry, Approval Logic & Safe Executor
- **Days 8–9:** Dependency and cycle validation (`PlanValidator` with Kahn's topological sort); allow-listed `ToolRegistry` with strict argument schema verification and permission scopes (`read_files`, `search`, `compute`).
- **Days 10–11:** Approval logic with expiry (`expires_at`, `get_status()`, `is_expired()`). Rejection or expiry guarantees zero tool execution and emits safe audit records.
- **Days 12–13:** Safe executor with per-step timeouts, bounded retries strictly for idempotent tools (`idempotent=True`), non-idempotent tool protection, and cancellation via `threading.Event`.
- **Day 14:** Policy test suite (55 tests passing, zero warnings) and D14 end-to-end demo of approved vs rejected execution paths.

---

## How to Run

### Running Week 2 (Safe Agentic Execution Engine)

```bash
cd WEEK2/projects/sde-2-voicebot
pip install -r requirements.txt

# Run all 55 tests
pytest tests/ -v

# Run the D14 approved vs rejected demonstration
pytest tests/test_demo.py -v -s
```

### Running Week 1 (Initial Vertical Slice)

```bash
cd WEEK1/voicebot-SDE2-teamm-karthik-nm/projects/sde-2-voicebot

# Run Week 1 tests
pytest tests/ -v

# Run Week 1 demo
python demo.py
```
