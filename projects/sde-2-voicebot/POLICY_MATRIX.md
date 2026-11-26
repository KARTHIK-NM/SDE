# Security & Governance Policy Matrix

**Workstream:** W4 — Agentic Workflow Engine (Week 4 / Days 22–30)  
**Team:** SDE 2 (`projects/sde-2-voicebot/`)  
**Student:** Karthik N M  
**Authoritative Enforcement Engine:** `src/workflow/policy.py` (`PolicyMatrix`)  
**Test Enforcement:** `tests/test_week4_policy_matrix.py` (13 automated tests)

---

## 1. Overview & Policy Invariants

The Policy Matrix defines the operational safety boundary for all tool actions within the Academiaai Voicebot agentic workflow engine. It establishes a multi-dimensional governance framework mapping **Tool Name × Risk Level × Approval Requirement × Permission Scopes × Timeout Limits × Retry Policies**.

### Non-Negotiable Security Invariants
1. **Universal Consequential Escalation:** Any step or tool classified under PRD Risk Categories **C (SENSITIVE)** or **D (DESTRUCTIVE)** strictly defaults to `requires_approval = True`. Any plan attempting to execute these tiers without explicit human approval is blocked immediately by `PolicyMatrix.enforce_step()`.
2. **Strict Scope Verification:** Callers must explicitly hold all permission scopes declared in the policy rule before any step can execute.
3. **Non-Idempotent / Consequential Protection:** Tools that mutate state (`is_idempotent = False`) or have risk levels of SENSITIVE or DESTRUCTIVE strictly forbid automated retry loops (`allow_retries = False`).
4. **Execution Timeout Bounding:** Steps cannot declare execution timeouts exceeding the policy threshold for that tool tier.
5. **Rejection & Expiry Zero-Execution Guarantee:** Rejection or TTL expiration guarantees zero downstream tool execution and writes an immutable audit event.

---

## 2. Authoritative Policy Matrix Table

| Tool Name | Risk Level | Approval Required | Required Scopes | Failure Behavior | Max Timeout | Retries Allowed | Purpose & Operational Rationale |
| :--- | :--- | :---: | :--- | :--- | :---: | :---: | :--- |
| `knowledge_search` | `informational` | **NO** | `kb:read` | `fail_workflow` | 30.0s | Yes | Read-only search across academic FAQs, catalogs, and documentation. Harmless in-memory lookup. |
| `course_schedule` | `informational` | **NO** | `schedule:read` | `fail_workflow` | 30.0s | Yes | Read-only query of course times, rooms, and instructor schedules. Harmless in-memory lookup. |
| `student_record_query` | `low_risk` | **NO** | `student:read` | `fail_workflow` | 30.0s | Yes | Read-only query of enrolled student records within authorized student scope. |
| `update_student_profile` | `sensitive` | **YES** | `student:write` | `fail_workflow` | 60.0s | No | Mutates student profile details or advisor assignments. Human approval is strictly mandatory. |
| `drop_course_registration`| `sensitive` | **YES** | `enrollment:write`| `fail_workflow` | 60.0s | No | Drops an enrolled course section. Academic standing impact requires human sign-off. |
| `delete_student_account` | `destructive` | **YES** | `admin:delete` | `fail_workflow` | 60.0s | No | Permanently purges user account and records. Administrator sign-off strictly required. |

---

## 3. Enforcement Architecture

```
[ Incoming WorkflowPlan / Proposal ]
                  │
                  ▼
         [ PlanValidator ]
                  │
                  ▼
         [ PolicyMatrix.enforce_plan() ]
          ├── 1. Check RiskLevel vs Approval Gate
          ├── 2. Check Caller Permission Scopes
          ├── 3. Enforce Retry Policy vs Idempotency
          └── 4. Enforce Timeout Thresholds
                  │
         ┌────────┴────────┐
         │                 │
      [Pass]            [Fail]
         │                 │
         ▼                 ▼
[ WorkflowExecutor ]  [ PolicyViolationError ]
                      (Zero tools executed)
```

---

## 4. Verification & Testing

Every single row and security condition of this Policy Matrix is actively enforced in unit and regression suites:
- `tests/test_week4_policy_matrix.py` validates all rows, scope restrictions, and violation errors.
- `tests/test_week4_failure_injection.py` validates that attempts to circumvent policy rules result in zero tool calls.
