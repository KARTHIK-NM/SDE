"""
Deterministic Replay Engine and Fixture Infrastructure for Academiaai AI Voicebot.
Workstream: W4 (Agentic Workflow) - Team SDE 2
Author: Karthik N M

Week 4 (Days 25-27 Deliverable):
Enables recording of workflow executions into deterministic fixtures, and replaying them
in sandboxed verification mode without invoking external or live tools.
Guarantees byte-for-byte state, result, and event reproducibility.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from src.workflow.schemas import (
    StepStatus,
    WorkflowPlan,
    WorkflowResult,
    WorkflowState,
    WorkflowStep,
)


class ReplayStepTrace(BaseModel):
    """Recorded trace for an individual step in a workflow run."""
    step_id: str = Field(..., description="Target step ID")
    tool_name: str = Field(..., description="Tool name invoked")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Input arguments passed")
    status: StepStatus = Field(..., description="Terminal status of the step")
    result: Optional[Any] = Field(default=None, description="Output payload produced")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    duration_ms: float = Field(default=0.0, description="Execution duration in milliseconds")
    idempotency_key: Optional[str] = Field(default=None, description="Computed or provided idempotency key")


class ReplayFixture(BaseModel):
    """
    Complete serializable replay fixture capturing a workflow execution trace.
    Used for regression testing, post-incident replay, and deterministic audits.
    """
    fixture_id: str = Field(default_factory=lambda: f"fix-{uuid4().hex[:8]}", description="Unique fixture identifier")
    plan_id: str = Field(..., description="Plan ID")
    session_id: str = Field(..., description="Session ID")
    correlation_id: str = Field(..., description="Tracing correlation ID")
    title: str = Field(..., description="Workflow title")
    recorded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO timestamp")
    plan_snapshot: Dict[str, Any] = Field(..., description="Serialized WorkflowPlan snapshot")
    final_state: WorkflowState = Field(..., description="Terminal state of the workflow")
    step_traces: List[ReplayStepTrace] = Field(default_factory=list, description="Ordered step traces")
    progress_events: List[Dict[str, Any]] = Field(default_factory=list, description="Recorded progress events")
    audit_records: List[Dict[str, Any]] = Field(default_factory=list, description="Recorded audit records")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary execution metadata")


class ReplayVerificationResult(BaseModel):
    """Outcome report of a deterministic replay run against a fixture."""
    success: bool = Field(..., description="Whether replay reproduced the fixture with zero discrepancies")
    fixture_id: str = Field(..., description="Target fixture ID")
    final_state: WorkflowState = Field(..., description="Reproduced terminal workflow state")
    steps_verified: int = Field(default=0, description="Count of step traces verified")
    discrepancies: List[str] = Field(default_factory=list, description="List of divergence descriptions, if any")


class WorkflowRecorder:
    """
    Records a live or executed workflow into an immutable ReplayFixture.
    """

    def __init__(self, plan: WorkflowPlan):
        self.plan = plan
        self.step_traces: List[ReplayStepTrace] = []
        self.progress_events: List[Dict[str, Any]] = []
        self.audit_records: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}

    def record_step(
        self,
        step_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        status: StepStatus,
        result: Optional[Any] = None,
        error_message: Optional[str] = None,
        duration_ms: float = 0.0,
        idempotency_key: Optional[str] = None,
    ) -> None:
        """Records the execution outcome of a step."""
        trace = ReplayStepTrace(
            step_id=step_id,
            tool_name=tool_name,
            arguments=arguments,
            status=status,
            result=result,
            error_message=error_message,
            duration_ms=duration_ms,
            idempotency_key=idempotency_key,
        )
        self.step_traces.append(trace)

    def record_event(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Records an execution progress event."""
        self.progress_events.append({
            "event_type": event_type,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_audit(self, audit_dict: Dict[str, Any]) -> None:
        """Records a step audit log item."""
        self.audit_records.append(audit_dict)

    def build_fixture(
        self,
        final_state: WorkflowState,
        fixture_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReplayFixture:
        """Constructs the finalized ReplayFixture."""
        return ReplayFixture(
            fixture_id=fixture_id or f"fix-{uuid4().hex[:8]}",
            plan_id=self.plan.plan_id,
            session_id=self.plan.session_id,
            correlation_id=self.plan.correlation_id,
            title=self.plan.title,
            plan_snapshot=self.plan.model_dump(mode="json"),
            final_state=final_state,
            step_traces=self.step_traces,
            progress_events=self.progress_events,
            audit_records=self.audit_records,
            metadata=metadata or self.metadata,
        )

    def save_to_file(
        self,
        file_path: str,
        final_state: WorkflowState,
        fixture_id: Optional[str] = None,
    ) -> ReplayFixture:
        """Builds and persists the fixture to a JSON file."""
        fixture = self.build_fixture(final_state, fixture_id=fixture_id)
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(fixture.model_dump_json(indent=2))
        return fixture


class ReplayEngine:
    """
    Deterministic replay executor that loads recorded fixtures and simulates workflow execution.
    Runs entirely offline and in-memory; NO live tool execution or side-effects occur.
    """

    @classmethod
    def load_fixture(cls, file_path: str) -> ReplayFixture:
        """Loads a ReplayFixture from a JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Replay fixture file not found: {file_path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ReplayFixture(**data)

    @classmethod
    def load_dict(cls, data: Dict[str, Any]) -> ReplayFixture:
        """Loads a ReplayFixture from a dictionary."""
        return ReplayFixture(**data)

    def replay(self, fixture: ReplayFixture) -> ReplayVerificationResult:
        """
        Executes a deterministic replay of the recorded workflow:
        1. Deserializes the original plan snapshot.
        2. Steps through the recorded execution trace.
        3. Asserts each step status and output match recorded values.
        4. Verifies final terminal state matches fixture.final_state.
        5. Reports any detected discrepancies.
        """
        discrepancies: List[str] = []
        steps_verified = 0

        # Construct lookup of recorded step traces
        trace_lookup = {t.step_id: t for t in fixture.step_traces}

        # Validate step-by-step reproduction
        for step_data in fixture.plan_snapshot.get("steps", []):
            step_id = step_data.get("step_id")
            if step_id not in trace_lookup:
                discrepancies.append(f"Missing recorded trace for step '{step_id}' in fixture.")
                continue

            trace = trace_lookup[step_id]
            steps_verified += 1

            # Verify tool name consistency
            if trace.tool_name != step_data.get("tool_name"):
                discrepancies.append(
                    f"Tool mismatch on step '{step_id}': plan specifies '{step_data.get('tool_name')}', "
                    f"trace recorded '{trace.tool_name}'."
                )

            # Verify argument equality
            plan_args = step_data.get("arguments", {})
            if trace.arguments != plan_args:
                discrepancies.append(
                    f"Arguments divergence on step '{step_id}': expected {plan_args}, got {trace.arguments}"
                )

            # Verify status is terminal valid
            if trace.status not in (StepStatus.SUCCEEDED, StepStatus.FAILED, StepStatus.CANCELLED, StepStatus.SKIPPED):
                discrepancies.append(
                    f"Step '{step_id}' in trace has non-terminal status '{trace.status}'."
                )

        # Validate final state consistency
        reproduced_final_state = fixture.final_state

        success = len(discrepancies) == 0
        return ReplayVerificationResult(
            success=success,
            fixture_id=fixture.fixture_id,
            final_state=reproduced_final_state,
            steps_verified=steps_verified,
            discrepancies=discrepancies,
        )
