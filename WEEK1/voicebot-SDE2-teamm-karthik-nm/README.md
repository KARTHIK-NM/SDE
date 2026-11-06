# voicebot-SDE2-teamm
AI Voice Co-Pilot - Team SDE 2

## Contributor: Karthik N M
**Workstream:** W4 — Agentic Workflow Engine (Week 1 & Week 2 / Days 1–14)  
**Email:** karthiknm8050@gmail.com  
**Branch:** `team/sde-2-voicebot`  
**Project Folder:** `projects/sde-2-voicebot/`

---

### Workstream W4 Deliverables (Week 1 & Week 2)

#### Week 1 (Days 1–7): Foundation & First Vertical Slice
- **Days 1–2:** Schemas (`WorkflowPlan`, `WorkflowStep`, `ToolSpec`, `ApprovalRequest`, `WorkflowResult`) and 7-state lifecycle state machine.
- **Days 3–4:** Two harmless mock tools (`knowledge_search`, `course_schedule`) with no external sending, `ToolRegistry`, and `WorkflowExecutor` with approval gating.
- **Days 5–6:** 35 unit tests validating invalid plans (cycles, missing dependencies, duplicate IDs) and state transitions.
- **Day 7:** Demonstration script (`demo.py`) running harmless, approved, and rejected execution scenarios.

#### Week 2 (Days 8–14): Plan Validation, Tool Registry, Approval Logic & Safe Executor
- **Days 8–9:** Dependency and cycle validation (`PlanValidator` with 3-color DFS); allow-listed `ToolRegistry` with strict argument schema verification and permission scopes (`kb:read`, `schedule:read`).
- **Days 10–11:** Approval logic with expiry (`ttl_seconds`, `expires_at`, `is_expired()`). Rejection or expiry guarantees zero tool execution and logs safe audit events.
- **Days 12–13:** Safe executor timeouts, bounded retries strictly for idempotent steps (`is_idempotent=True`), non-idempotent operation protection, and immediate cancellation.
- **Day 14:** Comprehensive policy test suite (47 tests passing) and upgraded demonstration script (`demo.py`) illustrating approved, rejected, and expired execution paths.

---

### Running Tests
```bash
cd projects/sde-2-voicebot
python -m pytest tests -v
```

### Running Live Demo
```bash
python projects/sde-2-voicebot/demo.py
```
