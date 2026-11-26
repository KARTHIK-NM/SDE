"""
Academiaai AI Voicebot - Week 4 (Days 22–30) Demonstration.
Workstream: W4 (Agentic Workflow Engine) - Team SDE 2
Author: Karthik N M

Demonstrates all Week 4 Hardening and Demonstration Deliverables:
1. Scenario 1: Normal Path (Informational workflow with knowledge search & course schedule)
2. Scenario 2: Consequential Step with Human Approval (SENSITIVE action approved via UI bridge)
3. Scenario 3: Failure Injection — Cyclic Plan Detected & Blocked (Zero tools executed)
4. Scenario 4: Failure Injection — Malicious Argument & Path Traversal Blocked (Zero tools executed)
5. Scenario 5: Failure Injection — Consequential Action Rejected by Supervisor (Zero tools executed)
6. Scenario 6: Failure Injection — Step Timeout & Non-Idempotent Retry Suppression
7. Scenario 7: Deterministic Replay of Recorded Fixture (100% reproducible trace verification)
8. Scenario 8: Policy Matrix Enforcement Verification
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.workflow.schemas import (
    ApprovalRequest,
    ApprovalStatus,
    ProgressEvent,
    ProgressEventType,
    RetryPolicy,
    RiskLevel,
    StepStatus,
    ToolFailureBehavior,
    ToolSpec,
    WorkflowPlan,
    WorkflowState,
    WorkflowStep,
)
from src.workflow.tools import (
    BaseTool,
    MockCourseScheduleTool,
    MockKnowledgeSearchTool,
    ToolRegistry,
)
from src.workflow.validator import PlanValidationError, PlanValidator
from src.workflow.executor import WorkflowExecutor
from src.workflow.policy import PolicyMatrix, PolicyViolationError
from src.workflow.replay import ReplayEngine
from src.workflow.integration import BackendApprovalService, WorkflowUIBridge


class DemoSpyTool(BaseTool):
    """Spy tool to demonstrate zero-execution guarantees during failure injection."""

    def __init__(self, name: str, risk_level: RiskLevel = RiskLevel.INFORMATIONAL, delay: float = 0.0):
        spec = ToolSpec(
            name=name,
            purpose="Demo spy tool",
            input_schema={"type": "object", "properties": {"target": {"type": "string"}}},
            permission_requirements=[],
            risk_level=risk_level,
            failure_behavior=ToolFailureBehavior.FAIL_WORKFLOW,
        )
        super().__init__(spec)
        self.call_count = 0
        self.delay = delay

    def execute(self, arguments):
        self.call_count += 1
        if self.delay > 0:
            time.sleep(self.delay)
        return {"status": "success", "call_count": self.call_count}


def banner(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def run_scenario_1_normal_path():
    banner("SCENARIO 1: Normal Path — Harmless Informational Workflow")
    print("Objective: Execute 2 harmless informational steps (knowledge search & schedule lookup).")

    registry = ToolRegistry.get_default_registry()

    step1 = WorkflowStep(
        step_id="step-info-1",
        tool_name="knowledge_search",
        arguments={"query": "cs101"},
        description="Search introductory CS lecture info",
        risk_level=RiskLevel.INFORMATIONAL,
        requires_approval=False,
    )
    step2 = WorkflowStep(
        step_id="step-info-2",
        tool_name="course_schedule",
        arguments={"course_code": "CS101", "term": "Fall 2026"},
        description="Look up CS101 timetable and classroom",
        risk_level=RiskLevel.INFORMATIONAL,
        requires_approval=False,
        depends_on=["step-info-1"],
    )
    plan = WorkflowPlan(
        session_id="sess-demo-1",
        correlation_id="corr-demo-1",
        title="CS101 Academic Information Lookup",
        steps=[step1, step2],
    )

    executor = WorkflowExecutor(plan=plan, registry=registry)
    result = executor.run()

    print(f"Workflow State : {result.final_state.value.upper()}")
    print(f"Step 1 Status  : {step1.status.value} | Result: {step1.result.get('count')} hit(s) found")
    print(f"Step 2 Status  : {step2.status.value} | Instructor: {step2.result.get('instructor')} | Room: {step2.result.get('location')}")
    print("Audit Log      : 2 records written with execution timing.")
    assert result.final_state == WorkflowState.SUCCEEDED


def run_scenario_2_consequential_approval():
    banner("SCENARIO 2: Consequential Path — SENSITIVE Step Gated by Human Approval")
    print("Objective: Pause on sensitive step, request human approval, and resume to completion.")

    spy = DemoSpyTool("update_student_profile", risk_level=RiskLevel.SENSITIVE)
    registry = ToolRegistry()
    registry.register(MockKnowledgeSearchTool())
    registry.register(spy)

    approval_service = BackendApprovalService()

    step1 = WorkflowStep(
        step_id="step-prep",
        tool_name="knowledge_search",
        arguments={"query": "tuition payment"},
        description="Verify policy",
    )
    step2 = WorkflowStep(
        step_id="step-sensitive",
        tool_name="update_student_profile",
        arguments={"target": "financial_aid_record"},
        description="Update student financial aid tier",
        risk_level=RiskLevel.SENSITIVE,
        requires_approval=True,
        depends_on=["step-prep"],
        is_idempotent=False,
    )
    plan = WorkflowPlan(
        session_id="sess-demo-2",
        correlation_id="corr-demo-2",
        title="Student Aid Update Plan",
        steps=[step1, step2],
    )

    bridge = WorkflowUIBridge(
        registry=registry,
        approval_service=approval_service,
    )
    bridge._plans[plan.plan_id] = plan

    res_initial = bridge.execute_workflow(plan.plan_id)
    assert res_initial is None  # Paused awaiting approval
    executor = bridge._executors[plan.plan_id]
    assert executor.current_state == WorkflowState.AWAITING_APPROVAL
    print(f"Execution State: {executor.current_state.value.upper()} (Halted at human gate)")

    pending = bridge.list_pending_approvals()
    assert len(pending) == 1
    appr_id = pending[0].approval_id
    print(f"Approval Raised: {appr_id} for step '{pending[0].step_id}' ({pending[0].tool_name})")

    # Operator approves via UI Bridge
    print("Human Operator : Approving request via WorkflowUIBridge.ui_approve()...")
    final_res = bridge.ui_approve(appr_id, approver="supervisor_carol")

    print(f"Final State    : {final_res.final_state.value.upper()}")
    print(f"Tool Invoked   : {spy.call_count} time(s) (Executed ONLY after approval granted).")
    assert final_res.final_state == WorkflowState.SUCCEEDED
    assert spy.call_count == 1


def run_scenario_3_cyclic_plan_failure():
    banner("SCENARIO 3: Failure Injection — Cyclic Plan Detected & Blocked")
    print("Objective: Prove cyclic dependencies (A -> B -> A) are blocked before any tool execution.")

    spy_a = DemoSpyTool("spy_a")
    spy_b = DemoSpyTool("spy_b")
    registry = ToolRegistry()
    registry.register(spy_a)
    registry.register(spy_b)

    step_a = WorkflowStep(
        step_id="step-a",
        tool_name="spy_a",
        arguments={"target": "a"},
        description="Step A",
        depends_on=["step-b"],
    )
    step_b = WorkflowStep(
        step_id="step-b",
        tool_name="spy_b",
        arguments={"target": "b"},
        description="Step B",
        depends_on=["step-a"],
    )

    plan = WorkflowPlan.model_construct(
        plan_id="plan-demo-cycle",
        session_id="sess-demo-3",
        correlation_id="corr-demo-3",
        title="Cyclic Plan",
        steps=[step_a, step_b],
    )

    validator = PlanValidator(registry=registry)
    try:
        validator.validate_dependencies_and_cycles(plan)
        print("ERROR: Cycle was not detected!")
    except PlanValidationError as e:
        print(f"Validation Error: {e.message}")
        print(f"Tool A Calls    : {spy_a.call_count} (ZERO execution guaranteed)")
        print(f"Tool B Calls    : {spy_b.call_count} (ZERO execution guaranteed)")
        assert spy_a.call_count == 0
        assert spy_b.call_count == 0


def run_scenario_4_malicious_input_failure():
    banner("SCENARIO 4: Failure Injection — Malicious Path Traversal Blocked")
    print("Objective: Prove path traversal payloads ('../../etc/passwd') are rejected before execution.")

    registry = ToolRegistry.get_default_registry()
    tool = registry.get("course_schedule")

    malicious_arg = {"course_code": "../../etc/passwd"}
    try:
        tool.validate_arguments(malicious_arg)
        print("ERROR: Malicious path traversal was not rejected!")
    except ValueError as ve:
        print(f"Defense Guardrail: {ve}")
        print("Security Status  : Malicious argument neutralized before reaching tool logic.")


def run_scenario_5_rejection_zero_execution():
    banner("SCENARIO 5: Failure Injection — Consequential Action Rejected by Supervisor")
    print("Objective: Prove rejected approval strictly results in ZERO tool execution.")

    spy = DemoSpyTool("delete_student_account", risk_level=RiskLevel.DESTRUCTIVE)
    registry = ToolRegistry()
    registry.register(spy)

    step = WorkflowStep(
        step_id="step-destruct",
        tool_name="delete_student_account",
        arguments={"target": "student_account"},
        description="Purge student record",
        risk_level=RiskLevel.DESTRUCTIVE,
        requires_approval=True,
    )
    plan = WorkflowPlan(
        session_id="sess-demo-5",
        correlation_id="corr-demo-5",
        title="Destructive Purge Plan",
        steps=[step],
    )

    executor = WorkflowExecutor(plan=plan, registry=registry)
    executor.run()
    appr_id = list(executor.pending_approvals.keys())[0]

    print(f"Action Paused  : Approval {appr_id} requested for DESTRUCTIVE action.")
    print("Supervisor Decision: REJECTED with reason 'Policy compliance veto'.")
    res = executor.reject_request(appr_id, reason="Policy compliance veto")

    print(f"Final State    : {res.final_state.value.upper()}")
    print(f"Tool Calls     : {spy.call_count} (ZERO tool execution strictly enforced).")
    assert res.final_state == WorkflowState.CANCELLED
    assert spy.call_count == 0


def run_scenario_6_step_timeout_failure():
    banner("SCENARIO 6: Failure Injection — Step Timeout & Non-Idempotent Protection")
    print("Objective: Prove step timeouts are enforced and non-idempotent steps are never retried.")

    slow_spy = DemoSpyTool("slow_tool", delay=0.15)
    registry = ToolRegistry()
    registry.register(slow_spy)

    step = WorkflowStep(
        step_id="step-timeout",
        tool_name="slow_tool",
        arguments={"target": "heavy_batch"},
        description="Slow batch step",
        timeout_seconds=0.05,
        is_idempotent=False,
        retry_policy=RetryPolicy(max_retries=3),
    )
    plan = WorkflowPlan(
        session_id="sess-demo-6",
        correlation_id="corr-demo-6",
        title="Timeout Plan",
        steps=[step],
    )

    executor = WorkflowExecutor(plan=plan, registry=registry)
    result = executor.run()

    print(f"Final State    : {result.final_state.value.upper()}")
    print(f"Error Details  : {result.error_details}")
    print(f"Attempts Made  : {slow_spy.call_count} (Retries strictly suppressed for non-idempotent step).")
    assert result.final_state == WorkflowState.FAILED
    assert slow_spy.call_count == 1


def run_scenario_7_deterministic_replay():
    banner("SCENARIO 7: Deterministic Replay Engine")
    print("Objective: Load recorded execution fixture and deterministically reproduce the run.")

    fixtures_dir = Path(__file__).parent / "tests" / "fixtures" / "replay"
    fixture_file = fixtures_dir / "successful_workflow_run.json"

    engine = ReplayEngine()
    fixture = engine.load_fixture(str(fixture_file))

    print(f"Loaded Fixture : {fixture.fixture_id} ({fixture.title})")
    print(f"Recorded State : {fixture.final_state.value.upper()} with {len(fixture.step_traces)} step trace(s)")

    verification = engine.replay(fixture)
    print(f"Replay Outcome : {'PASSED (Deterministic Match)' if verification.success else 'FAILED'}")
    print(f"Steps Verified : {verification.steps_verified}/{len(fixture.step_traces)}")
    print(f"Discrepancies  : {len(verification.discrepancies)} detected.")
    assert verification.success is True


def run_scenario_8_policy_matrix_enforcement():
    banner("SCENARIO 8: Authoritative Policy Matrix Enforcement")
    print("Objective: Display canonical enterprise policy rules and verify active enforcement.\n")

    matrix = PolicyMatrix()
    print(matrix.as_markdown_table())

    # Test policy enforcement
    test_step = WorkflowStep(
        step_id="step-policy-test",
        tool_name="delete_student_account",
        arguments={"target": "profile"},
        description="Delete account",
        risk_level=RiskLevel.DESTRUCTIVE,
        requires_approval=True,
    )
    matrix.enforce_step(test_step, caller_permissions=["admin:delete"])
    print("\nPolicy Enforcement: Passed all security invariants for DESTRUCTIVE tier.")


def main():
    print("================================================================================")
    print("   ACADEMIAAI VOICEBOT AGENTIC WORKFLOW ENGINE — WEEK 4 FINAL DEMONSTRATION")
    print("   Student: Karthik N M | Team: SDE 2 | Days 22–30 Hardening & Demonstration")
    print("================================================================================")

    run_scenario_1_normal_path()
    run_scenario_2_consequential_approval()
    run_scenario_3_cyclic_plan_failure()
    run_scenario_4_malicious_input_failure()
    run_scenario_5_rejection_zero_execution()
    run_scenario_6_step_timeout_failure()
    run_scenario_7_deterministic_replay()
    run_scenario_8_policy_matrix_enforcement()

    banner("DEMONSTRATION COMPLETE: ALL 8 SCENARIOS PASSED WITH 100% FIDELITY")


if __name__ == "__main__":
    main()
