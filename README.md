# Academia AI Voice Co-Pilot — SDE Internship

**Team:** SDE 2  
**Workstream:** W4 — Agentic Workflow Engine (Weeks 1, 2, 3 & 4 / Days 1–30 Release Gate)  
**Contributor:** Karthik N M  
**Email:** karthiknm8050@gmail.com  
**Branch:** `team/sde-2-voicebot` / `karthik-nm`  
**Project Folder:** `projects/sde-2-voicebot/`  
**Repository:** [https://github.com/KARTHIK-NM/SDE](https://github.com/KARTHIK-NM/SDE)  

---

## 🎯 Executive Summary

This repository delivers the **complete, unified, and production-hardened Agentic Workflow Engine** for the **Academia AI Voice Co-Pilot**, combining all deliverables across **Days 1–30**:

- **Week 1 (Days 1–7):** Typed schemas, 7-state deterministic lifecycle state machine, harmless in-memory mock tools (`knowledge_search`, `course_schedule`), and human-in-the-loop approval gating.
- **Week 2 (Days 8–14):** Plan validator (dependencies & cycle detection via Kahn's algorithm / 3-color DFS), allow-listed tool registry with argument type and permission scope enforcement, approval logic with TTL expiry, safe executor (timeouts, bounded retries strictly for idempotent operations, non-idempotent protection, and cancellation).
- **Week 3 (Days 15–21):** Checkpoint and resume with failed-step recovery (skips completed steps on resume), SHA-256 idempotency keys preventing duplicate tool runs, step-level audit trail with duration and credential masking, real-time typed progress events, reasoning proposal ingestion (`WorkflowProposal`), backend approval state service, and UI integration bridge with duplicate and expired approval protection.
- **Week 4 (Days 22–30): Hardening & Demonstration Release Gate:**
  1. **Failure-Injection Test Suite (`tests/test_week4_failure_injection.py`):** Injects cyclic plans (self-loops, 2-node cycles, 3-node cycles), malicious arguments (path traversal, null bytes, out-of-scope fields), duplicate submissions, step timeouts, and rejected approvals — proving **no tool executes when it shouldn't**.
  2. **Deterministic Replay Engine (`src/workflow/replay.py`):** Reproduces recorded workflow runs deterministically from saved JSON fixtures (`tests/fixtures/replay/`).
  3. **Authoritative Policy Matrix (`src/workflow/policy.py` & `POLICY_MATRIX.md`):** Complete mapping of Tool × Risk Level × Approval Required × Required Permissions × Retries, enforced by 13 dedicated tests.
  4. **Workflow Operations Runbook (`RUNBOOK.md`):** Comprehensive production runbook covering setup, execution, monitoring, checkpointing, recovery, and incident response.
  5. **"Adding a Safe Tool" Developer Guide (`SAFE_TOOL_GUIDE.md`):** Step-by-step developer guide on adding allow-listed tools safely.
  6. **Comprehensive Final Demo (`demo_week4.py`):** 8-scenario interactive live demonstration.
  7. **Automated Verification:** **153 automated tests passing** in mock mode with zero external calls.

---

## 📁 Unified Project Structure

```
.
├── projects/
│   └── sde-2-voicebot/
│       ├── POLICY_MATRIX.md                # Authoritative Policy Matrix (Tool x Risk x Approval x Scopes)
│       ├── RUNBOOK.md                      # Workflow Engine Operations Manual & Incident Response
│       ├── SAFE_TOOL_GUIDE.md              # Developer Guide for adding allow-listed tools safely
│       ├── demo_week4.py                   # Week 4 comprehensive demonstration (8 Scenarios)
│       ├── demo_week3.py                   # Week 3 demonstration (5 Scenarios)
│       ├── demo.py                         # Week 2 demonstration
│       ├── requirements.txt                # Project dependencies
│       ├── README.md                       # Voicebot module documentation
│       ├── src/
│       │   └── workflow/
│       │       ├── schemas.py              # Single source of truth for workflow models
│       │       ├── state_machine.py        # 7-state lifecycle controller with audit history
│       │       ├── validator.py            # PlanValidator: cycles, deps, tools, scopes
│       │       ├── tools.py                # Allow-listed registry & mock tools with defense checks
│       │       ├── executor.py             # Safe executor: timeouts, retries, approvals
│       │       ├── checkpoint.py           # CheckpointStore, CheckpointManager & recovery
│       │       ├── idempotency.py          # IdempotencyStore with SHA-256 keying
│       │       ├── audit.py                # StepAuditLogger & ProgressEventEmitter
│       │       ├── integration.py          # Reasoning proposal parser & UI bridge
│       │       ├── policy.py               # Authoritative Policy Matrix & Enforcer (Week 4)
│       │       ├── replay.py               # Deterministic Replay Engine & Recorder (Week 4)
│       │       └── README.md               # Detailed workflow architecture guide
│       └── tests/                          # 153 passing unit, policy, replay & failure tests
│           ├── conftest.py
│           ├── test_workflow_schemas_and_sm.py
│           ├── test_invalid_plans_and_transitions.py
│           ├── test_mock_tools_and_executor.py
│           ├── test_week2_policy_and_safe_executor.py
│           ├── test_plan_validator.py
│           ├── test_tool_registry.py
│           ├── test_approval_manager.py
│           ├── test_safe_executor.py
│           ├── test_demo.py
│           ├── test_week3_checkpoint_and_resume.py
│           ├── test_week3_audit_and_events.py
│           ├── test_week3_reasoning_and_ui_integration.py
│           ├── test_week3_end_to_end_integration.py
│           ├── test_week4_failure_injection.py  # 18 failure injection tests
│           ├── test_week4_replay.py             # 7 deterministic replay tests
│           ├── test_week4_policy_matrix.py      # 13 policy matrix enforcement tests
│           └── fixtures/
│               └── replay/
│                   ├── successful_workflow_run.json
│                   ├── consequential_approval_granted.json
│                   ├── consequential_approval_rejected.json
│                   └── step_timeout_failure.json
├── requirements.txt                        # Global requirements
├── README.md                               # Project documentation
└── .gitignore
```

---

## 🚀 Quickstart & Commands

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

### 4. Run Week 3 Live Demonstration (5 Scenarios)

```bash
python demo_week3.py
```

---

## 🛡️ Key Safety Invariants Enforced

1. **Deterministic State Machine:** Strictly transitions between 7 states (`draft`, `awaiting_approval`, `running`, `paused`, `succeeded`, `failed`, `cancelled`) with full audit history.
2. **Universal Consequential Escalation:** Steps with `RiskLevel.SENSITIVE` or `RiskLevel.DESTRUCTIVE` strictly require human approval.
3. **Approval Rejection & Expiry:** Rejection or TTL expiry guarantees **zero tool execution** and writes an immutable audit record.
4. **Idempotency & Deduplication:** SHA-256 keys prevent duplicate execution even across crashes and re-runs.
5. **Deterministic Replay:** Recorded execution fixtures reproduce runs with 100% deterministic fidelity without external side-effects.
6. **Input Defense:** Rejects path traversal sequences (`../`), null bytes (`\x00`), and out-of-scope arguments before reaching tool logic.
7. **Harmless Mock Mode:** Only harmless in-memory tools (`knowledge_search`, `course_schedule`); no external network or live mutations.
