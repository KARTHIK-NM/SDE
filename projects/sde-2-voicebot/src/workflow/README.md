# Workstream W4: Agentic Workflow Engine (Weeks 1, 2, 3 & 4 / Days 1–30)

**Student:** Karthik N M  
**Team:** SDE 2 (`projects/sde-2-voicebot/`)  
**Scope:** Days 1–30 (Foundation, Safe Execution, Checkpoint/Audit/Integration, Hardening & Release Gate)

---

## 1. Executive Summary

This package delivers the production-ready Agentic Workflow Engine for the Academiaai Voicebot, strictly adhering to Workstream W4 across Weeks 1–4:

### Week 1 (Days 1–7): Foundation & First Vertical Slice
1. **Typed Workflow Schemas (Days 1–2):** Single-source schemas defined in `src/workflow/schemas.py` (`WorkflowPlan`, `WorkflowStep`, `ToolSpec`, `ApprovalRequest`, `WorkflowResult`).
2. **Deterministic State Machine (Days 1–2):** Enforces lifecycle transitions (`draft`, `awaiting_approval`, `running`, `paused`, `succeeded`, `failed`, `cancelled`) with full audit history in `src/workflow/state_machine.py`.
3. **Mock Tools (Days 3–4):** Two harmless mock tools (`MockKnowledgeSearchTool`, `MockCourseScheduleTool`) with no external sending, and safe `ToolRegistry` in `src/workflow/tools.py`.
4. **Agentic Executor (Days 3–4):** Orchestrates step execution in mock mode with a mandatory safety gate where sensitive/destructive actions automatically default to awaiting human approval in `src/workflow/executor.py`.

### Week 2 (Days 8–14): Safe Execution Upgrade
1. **Plan Validator (Days 8–9):** `PlanValidator` in `src/workflow/validator.py` detects dependency cycles (3-color DFS), missing dependencies, duplicate IDs, unknown tools, argument types, and enforces permission scopes.
2. **Approval Logic & Expiry (Days 10–11):** `ApprovalRequest` includes TTL (`ttl_seconds`, `expires_at`). Rejection or expiration strictly guarantees ZERO tool execution and logs safe audit events.
3. **Safe Executor (Days 12–13):** `WorkflowExecutor` enforces step timeouts, bounded retries strictly for idempotent steps (`is_idempotent=True`), non-idempotent safety, and immediate cancellation.
4. **Policy Tests & Live Demonstration (Day 14):** Automated tests in `tests/` and live demonstration in `demo.py`.

### Week 3 (Days 15–21): Checkpoint, Audit Trail & Integration
1. **Checkpoint & Resume (Days 15–16):** `CheckpointStore`, `CheckpointManager`, and failed-step recovery helper skipping completed steps on resume (`src/workflow/checkpoint.py`).
2. **Idempotency Keys (Days 15–16):** `IdempotencyStore` using SHA-256 key derivation (`src/workflow/idempotency.py`).
3. **Audit Trail & Events (Days 17–18):** Append-only `StepAuditLogger` with credential redaction, and `ProgressEventEmitter` with typed events (`src/workflow/audit.py`).
4. **Reasoning & UI Integration (Days 19–20):** `WorkflowProposalParser`, `BackendApprovalService`, and `WorkflowUIBridge` (`src/workflow/integration.py`).

### Week 4 (Days 22–30): Hardening & Release Gate
1. **Failure-Injection Test Suite (Days 22–24):** Tests cyclic plans, malicious path traversals, null bytes, out-of-scope fields, duplicate submissions, step timeouts, and rejected approvals in `tests/test_week4_failure_injection.py`.
2. **Deterministic Replay Engine (Days 25–27):** Records and replays execution traces with zero side-effects in `src/workflow/replay.py` and `tests/test_week4_replay.py`.
3. **Authoritative Policy Matrix (Days 25–27):** Canonical security mapping in `src/workflow/policy.py`, documented in `POLICY_MATRIX.md`, tested in `tests/test_week4_policy_matrix.py`.
4. **Runbook & Safe Tool Guide (Days 28–29):** Committed in `RUNBOOK.md` and `SAFE_TOOL_GUIDE.md`.
5. **Final Comprehensive Demonstration (Day 30):** 8-scenario live demonstration in `demo_week4.py`.

---

## 2. Architecture & Component Structure

```
projects/sde-2-voicebot/
│
├── POLICY_MATRIX.md                           # Authoritative Policy Matrix
├── RUNBOOK.md                                 # Operations Manual & Incident Response
├── SAFE_TOOL_GUIDE.md                         # Guide for adding safe allow-listed tools
├── demo_week4.py                              # Week 4 comprehensive demonstration (8 Scenarios)
│
├── src/
│   └── workflow/
│       ├── __init__.py                        # Package exports
│       ├── schemas.py                         # Single source of truth for workflow schemas
│       ├── state_machine.py                   # 7-state deterministic state machine
│       ├── validator.py                       # PlanValidator (cycles, deps, tools, scopes)
│       ├── tools.py                           # BaseTool, mock tools with input defenses, ToolRegistry
│       ├── executor.py                        # Safe executor (timeouts, retries, approvals)
│       ├── checkpoint.py                      # CheckpointStore, CheckpointManager & recovery
│       ├── idempotency.py                     # IdempotencyStore with SHA-256 keys
│       ├── audit.py                           # StepAuditLogger & ProgressEventEmitter
│       ├── integration.py                     # Reasoning parser & UI bridge
│       ├── policy.py                          # PolicyMatrix & PolicyViolationError (Week 4)
│       ├── replay.py                          # ReplayEngine, ReplayFixture, WorkflowRecorder (Week 4)
│       └── README.md                          # This architecture reference
│
└── tests/                                     # 153 passing automated tests
```

---

## 3. Running All Tests & Demo

```bash
cd projects/sde-2-voicebot

# Run all 153 tests
pytest -v

# Run Week 4 Live Demonstration
python demo_week4.py
```
