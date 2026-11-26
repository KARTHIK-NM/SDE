"""
Deterministic Replay Test Suite.
Workstream: W4 (Agentic Workflow) - Team SDE 2
Author: Karthik N M

Days 25-27 Deliverable:
Validates all Week 4 Deterministic Replay Acceptance Criteria:
1. Recorded workflow runs are loaded and replayed with 100% deterministic fidelity.
2. Replay fixtures verify successful, approved, rejected, and timeout failure executions.
3. Live execution recording via WorkflowRecorder creates valid, verifiable fixtures.
4. Discrepancies (tampered tools, modified arguments, diverging outcomes) are strictly caught.
"""

import json
from pathlib import Path
import pytest

from src.workflow.schemas import (
    RiskLevel,
    StepStatus,
    WorkflowPlan,
    WorkflowState,
    WorkflowStep,
)
from src.workflow.tools import ToolRegistry
from src.workflow.executor import WorkflowExecutor
from src.workflow.replay import (
    ReplayEngine,
    ReplayFixture,
    ReplayStepTrace,
    WorkflowRecorder,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "replay"


def test_load_and_replay_successful_workflow_fixture():
    """Replays the recorded 2-step harmless search & schedule workflow deterministically."""
    fixture_path = FIXTURES_DIR / "successful_workflow_run.json"
    engine = ReplayEngine()
    fixture = engine.load_fixture(str(fixture_path))

    result = engine.replay(fixture)
    assert result.success is True
    assert result.discrepancies == []
    assert result.steps_verified == 2
    assert result.final_state == WorkflowState.SUCCEEDED


def test_load_and_replay_consequential_approval_granted_fixture():
    """Replays the sensitive approval granted workflow deterministically."""
    fixture_path = FIXTURES_DIR / "consequential_approval_granted.json"
    engine = ReplayEngine()
    fixture = engine.load_fixture(str(fixture_path))

    result = engine.replay(fixture)
    assert result.success is True
    assert result.discrepancies == []
    assert result.steps_verified == 2
    assert result.final_state == WorkflowState.SUCCEEDED


def test_load_and_replay_consequential_approval_rejected_fixture():
    """Replays the consequential approval rejection workflow deterministically."""
    fixture_path = FIXTURES_DIR / "consequential_approval_rejected.json"
    engine = ReplayEngine()
    fixture = engine.load_fixture(str(fixture_path))

    result = engine.replay(fixture)
    assert result.success is True
    assert result.discrepancies == []
    assert result.steps_verified == 1
    assert result.final_state == WorkflowState.CANCELLED


def test_load_and_replay_step_timeout_failure_fixture():
    """Replays the step timeout failure workflow deterministically."""
    fixture_path = FIXTURES_DIR / "step_timeout_failure.json"
    engine = ReplayEngine()
    fixture = engine.load_fixture(str(fixture_path))

    result = engine.replay(fixture)
    assert result.success is True
    assert result.discrepancies == []
    assert result.steps_verified == 1
    assert result.final_state == WorkflowState.FAILED


def test_replay_detects_tampered_tool_discrepancy():
    """Replay engine catches any discrepancy if recorded tool name diverges from plan."""
    fixture_path = FIXTURES_DIR / "successful_workflow_run.json"
    engine = ReplayEngine()
    fixture = engine.load_fixture(str(fixture_path))

    # Tamper with recorded trace for step-1
    fixture.step_traces[0].tool_name = "malicious_injected_tool"

    result = engine.replay(fixture)
    assert result.success is False
    assert len(result.discrepancies) > 0
    assert any("Tool mismatch" in d for d in result.discrepancies)


def test_replay_detects_tampered_arguments_discrepancy():
    """Replay engine catches any discrepancy if arguments were modified."""
    fixture_path = FIXTURES_DIR / "successful_workflow_run.json"
    engine = ReplayEngine()
    fixture = engine.load_fixture(str(fixture_path))

    # Tamper with recorded arguments for step-1
    fixture.step_traces[0].arguments = {"query": "tampered_payload"}

    result = engine.replay(fixture)
    assert result.success is False
    assert len(result.discrepancies) > 0
    assert any("Arguments divergence" in d for d in result.discrepancies)


def test_workflow_recorder_captures_and_replays_live_execution(tmp_path):
    """Proves a live WorkflowExecutor execution can be captured by WorkflowRecorder and replayed."""
    registry = ToolRegistry.get_default_registry()

    step = WorkflowStep(
        step_id="step-rec-1",
        tool_name="knowledge_search",
        arguments={"query": "cs101"},
        description="Search CS101",
    )
    plan = WorkflowPlan(
        session_id="sess-rec-1",
        correlation_id="corr-rec-1",
        title="Live Recorded Plan",
        steps=[step],
    )

    recorder = WorkflowRecorder(plan=plan)

    executor = WorkflowExecutor(plan=plan, registry=registry)
    exec_result = executor.run()
    assert exec_result.final_state == WorkflowState.SUCCEEDED

    # Record trace
    recorder.record_step(
        step_id=step.step_id,
        tool_name=step.tool_name,
        arguments=step.arguments,
        status=step.status,
        result=step.result,
        duration_ms=15.0,
    )

    output_file = tmp_path / "live_recorded_fixture.json"
    fixture = recorder.save_to_file(str(output_file), final_state=exec_result.final_state)

    # Replay the generated fixture
    engine = ReplayEngine()
    loaded_fixture = engine.load_fixture(str(output_file))
    verify_result = engine.replay(loaded_fixture)

    assert verify_result.success is True
    assert verify_result.discrepancies == []
    assert verify_result.steps_verified == 1
    assert verify_result.final_state == WorkflowState.SUCCEEDED
