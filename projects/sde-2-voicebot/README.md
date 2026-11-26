# Academia AI Voicebot — Agentic Workflow Engine

**Team:** SDE 2  
**Workstream:** W4 — Agentic Workflow Engine (Weeks 1–4 / Days 1–30 Release Gate)  
**Student:** Karthik N M  
**Email:** karthiknm8050@gmail.com  
**Branch:** `team/sde-2-voicebot` / `karthik-nm`  
**Test Suite:** 153 automated tests passing (100% green in mock mode)  

---

## 🚀 Executive Summary

This repository delivers the **production-hardened Agentic Workflow Engine** for the **Academia AI Voice Co-Pilot**, fulfilling all deliverables and acceptance criteria across **Days 1–30 (Weeks 1–4)**:

- **Week 1 (Days 1–7):** Typed Pydantic schemas (`WorkflowPlan`, `WorkflowStep`, `ToolSpec`, `ApprovalRequest`), 7-state deterministic lifecycle machine, harmless mock tools (`knowledge_search`, `course_schedule`), and human approval gating.
- **Week 2 (Days 8–14):** Safe agentic execution: `PlanValidator` (dependency resolution & cycle detection via 3-color DFS), `ToolRegistry` with strict parameter and permission scope checking, approval TTL expiry, safe timeouts, and bounded retries strictly for idempotent operations.
- **Week 3 (Days 15–21):** Checkpoint and resume with failed-step recovery, SHA-256 idempotency deduplication, append-only step audit logger with credential redaction, typed progress events, reasoning proposal ingestion (`WorkflowProposal`), backend approval state service, and UI bridge.
- **Week 4 (Days 22–30): Hardening & Release Gate:**
  1. **Failure-Injection Test Suite (`tests/test_week4_failure_injection.py`):** Injects cyclic plans, malicious path traversals, null bytes, out-of-scope fields, duplicate submissions, step timeouts, and rejected approvals — proving **zero tools execute when they shouldn't**.
  2. **Deterministic Replay Engine (`src/workflow/replay.py`):** Captures execution traces and replays saved fixtures (`tests/fixtures/replay/`) with 100% deterministic fidelity without invoking live systems.
  3. **Authoritative Policy Matrix (`src/workflow/policy.py` & `POLICY_MATRIX.md`):** Complete mapping of Tool × Risk Level × Approval Requirement × Scopes × Retries, verified by 13 dedicated tests.
  4. **Operations Runbook (`RUNBOOK.md`):** Production runbook for operating the engine, handling crashes, triaging stuck approvals, and inspecting audit logs.
  5. **"Adding a Safe Tool" Developer Guide (`SAFE_TOOL_GUIDE.md`):** Step-by-step developer guide on introducing new tools safely.
  6. **Comprehensive Final Demo (`demo_week4.py`):** 8-scenario interactive demonstration covering both normal path and failure scenarios.

---

## 📁 Repository Structure

```
projects/sde-2-voicebot/
│
├── POLICY_MATRIX.md                   # Authoritative Policy Matrix (Tool x Risk x Approval x Scopes)
├── RUNBOOK.md                         # Workflow Engine Operations Manual & Incident Response
├── SAFE_TOOL_GUIDE.md                 # Developer Guide for adding allow-listed tools safely
├── demo_week4.py                      # Week 4 comprehensive demonstration (8 Scenarios)
├── demo_week3.py                      # Week 3 demonstration (5 Scenarios)
├── demo.py                            # Week 2 demonstration
├── requirements.txt                   # Project dependencies
│
├── src/
│   └── workflow/
│       ├── __init__.py                # Package exports
│       ├── schemas.py                 # Single source of truth for Pydantic schemas
│       ├── state_machine.py           # 7-state deterministic lifecycle state machine
│       ├── tools.py                   # BaseTool, harmless mock tools & ToolRegistry
│       ├── validator.py               # PlanValidator (cycles, deps, allow-lists, scopes)
│       ├── executor.py                # Safe WorkflowExecutor (timeouts, retries, approvals)
│       ├── checkpoint.py              # CheckpointStore, CheckpointManager & recovery
│       ├── idempotency.py             # IdempotencyStore with SHA-256 key derivation
│       ├── audit.py                   # StepAuditLogger (append-only) & ProgressEventEmitter
│       ├── integration.py             # Reasoning parser, backend approvals & UI bridge
│       ├── policy.py                  # PolicyMatrix engine & PolicyViolationError (Week 4)
│       ├── replay.py                  # ReplayEngine, ReplayFixture & WorkflowRecorder (Week 4)
│       └── README.md                  # Workflow engine architecture reference
│
└── tests/                             # 153 passing automated tests
    ├── conftest.py
    ├── test_workflow_schemas_and_sm.py
    ├── test_invalid_plans_and_transitions.py
    ├── test_mock_tools_and_executor.py
    ├── test_week2_policy_and_safe_executor.py
    ├── test_plan_validator.py
    ├── test_tool_registry.py
    ├── test_approval_manager.py
    ├── test_safe_executor.py
    ├── test_demo.py
    ├── test_week3_checkpoint_and_resume.py
    ├── test_week3_audit_and_events.py
    ├── test_week3_reasoning_and_ui_integration.py
    ├── test_week3_end_to_end_integration.py
    ├── test_week4_failure_injection.py  # Failure injection tests (18 tests)
    ├── test_week4_replay.py             # Deterministic replay tests (7 tests)
    ├── test_week4_policy_matrix.py      # Policy matrix row enforcement tests (13 tests)
    └── fixtures/
        └── replay/
            ├── successful_workflow_run.json
            ├── consequential_approval_granted.json
            ├── consequential_approval_rejected.json
            └── step_timeout_failure.json
```

---

## ⚡ Quickstart & Clean-Clone Verification

### 1. Install Dependencies
```bash
cd projects/sde-2-voicebot
pip install -r requirements.txt
```

### 2. Run All Automated Tests (153 Tests Passing)
```bash
pytest -v
```

### 3. Run Week 4 Live Demonstration (8 Scenarios)
```bash
python demo_week4.py
```

Scenarios demonstrated:
1. Normal Path (harmless read-only knowledge & schedule queries)
2. Consequential Path (SENSITIVE action paused, supervisor approves via UI bridge)
3. Failure Injection: Cyclic Plan (A -> B -> A detected and blocked; 0 tool calls)
4. Failure Injection: Malicious Input (Path traversal `../../etc/passwd` blocked; 0 tool calls)
5. Failure Injection: Rejected Approval (Supervisor rejects; ZERO tool execution verified)
6. Failure Injection: Step Timeout & Retry Suppression (Enforced timeouts halt execution)
7. Deterministic Replay (Recorded fixture replayed and verified with 0 live side-effects)
8. Policy Matrix Enforcement (Active validation of canonical governance rules)

---

## 🛡️ Authoritative Policy Matrix Summary

| Tool Name | Risk Level | Approval Required | Scopes | Retries | Max Timeout |
| :--- | :--- | :---: | :--- | :---: | :---: |
| `knowledge_search` | `informational` | **NO** | `kb:read` | Yes | 30.0s |
| `course_schedule` | `informational` | **NO** | `schedule:read` | Yes | 30.0s |
| `student_record_query` | `low_risk` | **NO** | `student:read` | Yes | 30.0s |
| `update_student_profile` | `sensitive` | **YES** | `student:write` | No | 60.0s |
| `drop_course_registration` | `sensitive` | **YES** | `enrollment:write` | No | 60.0s |
| `delete_student_account` | `destructive` | **YES** | `admin:delete` | No | 60.0s |

See [`POLICY_MATRIX.md`](./POLICY_MATRIX.md) for full rationale and test validation.

---

## ⚠️ Known Limitations & Future Work

1. **In-Memory Store Persistence:** Default stores (`CheckpointStore`, `IdempotencyStore`, `StepAuditLogger`) operate in-memory for testing and isolation. For multi-node distributed deployments, bind them to Redis or PostgreSQL backends.
2. **Synchronous Mock Execution:** In mock mode, tools run in a thread-pool executor. Future work will bridge tools to asynchronous HTTP/gRPC connectors for production voicebot microservices.
3. **Approval Escalation Notification:** Approval requests currently notify listeners via `ProgressEventEmitter`. Integrating webhooks / Slack / SMS alerts can be added in subsequent milestones.
