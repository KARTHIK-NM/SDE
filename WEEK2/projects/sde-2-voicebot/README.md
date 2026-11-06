# SDE-2 Voicebot — Agentic Workflow Engine

**Team:** SDE 2  
**Branch:** `team/sde-2-voicebot`  
**Sprint:** Week 2 (Days 8–14)  
**Feature:** W4 – Plan Validation · Tool Registry · Approval Logic · Safe Executor

---

## What This Does

Implements the **safe agentic execution layer** for the AI Voice Co-Pilot:

| Layer | Module | Responsibility |
|-------|--------|---------------|
| Schemas | `schemas.py` | Shared Pydantic models (Week 1 base) |
| Validator | `plan_validator.py` | Dependency & cycle checks on plans |
| Registry | `tool_registry.py` | Allow-listed tools with arg + scope validation |
| Approval | `approval_manager.py` | Approve / reject / expiry logic |
| Executor | `safe_executor.py` | Timeouts, bounded retries, cancellation |
| Mock Tools | `mock_tools.py` | Harmless tools only — no external I/O |

---

## Project Layout

```
sde-2-voicebot/
├── schemas.py            # Shared Pydantic schemas (Week 1)
├── plan_validator.py     # Dependency + cycle validation (D8-9)
├── tool_registry.py      # Allow-listed registry (D8-9)
├── approval_manager.py   # Approve/reject/expiry (D10-11)
├── safe_executor.py      # Timeout/retry/cancel executor (D12-13)
├── mock_tools.py         # Harmless mock tool implementations
├── tests/
│   ├── test_plan_validator.py
│   ├── test_tool_registry.py
│   ├── test_approval_manager.py
│   ├── test_safe_executor.py
│   └── test_demo.py      # D14 approved-vs-rejected demo
├── requirements.txt
└── README.md
```

---

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Running the Demo

```bash
python -m pytest tests/test_demo.py -v -s
```

