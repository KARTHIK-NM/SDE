# Academia AI Voice Co-Pilot — SDE Internship

**Team:** SDE 2  
**Branch:** `team/sde-2-voicebot`  
**Project Folder:** `projects/sde-2-voicebot/`  
**Sprint:** Week 2 (Days 8–14)  
**Feature:** W4 – Agentic Workflow: Plan Validation, Tool Registry, Approval Logic & Safe Executor

---

## Overview

This repository contains the Week 2 implementation of the safe agentic execution layer for the Academia AI Voice Co-Pilot.

Key capabilities:
- **Plan Validation (D8–9):** Dependency validation and cycle detection using Kahn's algorithm (topological sort).
- **Allow-Listed Tool Registry (D8–9):** Strict allow-list enforcement, argument presence/type validation, and permission scope checks.
- **Approval Logic & Expiry (D10–11):** Human-in-the-loop sign-off (approve/reject) with TTL expiry. Rejection or expiry guarantees zero tool execution and emits a safe audit record.
- **Safe Executor (D12–13):** Wall-clock timeouts, bounded retries (strictly restricted to idempotent tools), and cooperative thread cancellation.
- **Harmless Mock Tools:** Only safe mock tools (file search, file read, web search, summarize, calculator). No external sending or real system modification.
- **Policy Tests & D14 Demo (D14):** 55 unit/integration tests verifying all safety policies, plus end-to-end demo of approved vs rejected plans.

---

## Project Structure

```
.
└── projects/
    └── sde-2-voicebot/
        ├── schemas.py            # Shared Pydantic models (Week 1 base)
        ├── plan_validator.py     # Plan validator (dependencies & cycles)
        ├── tool_registry.py      # Allow-listed registry with arg & scope checks
        ├── approval_manager.py   # Approval lifecycle (approve/reject/expiry)
        ├── safe_executor.py      # Safe executor (timeouts, retries, cancellation)
        ├── mock_tools.py         # Harmless mock tools
        ├── requirements.txt      # Dependencies
        ├── README.md             # Project documentation
        └── tests/
            ├── conftest.py               # Shared fixtures & test helpers
            ├── test_plan_validator.py    # Tests for plan validation
            ├── test_tool_registry.py     # Tests for registry & scopes
            ├── test_approval_manager.py  # Tests for approval & expiry
            ├── test_safe_executor.py     # Tests for execution, timeouts, retries
            └── test_demo.py              # D14 end-to-end approved vs rejected demo
```

---

## Setup & Running Tests

1. Navigate to the project directory:
   ```bash
   cd projects/sde-2-voicebot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the full test suite (55 tests):
   ```bash
   pytest tests/ -v
   ```

4. Run the D14 approved vs rejected demonstration:
   ```bash
   pytest tests/test_demo.py -v -s
   ```

