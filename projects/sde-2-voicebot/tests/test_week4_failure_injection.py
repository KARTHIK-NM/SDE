"""
Week 4 Failure-Injection Test Suite.
Workstream: W4 (Agentic Workflow) - Team SDE 2
Author: Karthik N M

Days 22-24 Deliverable:
Validates all Week 4 Failure-Injection Acceptance Criteria:
1. Cyclic plans (self-loops, 2-node cycles, 3-node cycles, subgraph cycles) rejected; 0 tools execute.
2. Malicious or out-of-scope arguments (path traversal, null bytes, out-of-scope extra fields, negative bounds) rejected; 0 tools execute.
3. Duplicate submissions (duplicate step IDs, duplicate plan executions, duplicate approvals) prevented; 0 duplicate executions.
4. Step timeouts enforced; non-idempotent actions never retried.
5. Rejected & expired approvals strictly guarantee ZERO downstream tool execution.
6. Missing permissions prevent execution before any tool runs.
"""

import time
from typing import Any, Dict
import pytest

from src.workflow.schemas import (
    ApprovalStatus,
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
from src.workflow.validator import (
    PlanValidationError,
    PlanValidator,
)
from src.workflow.executor import WorkflowExecutor


class SpyTool(BaseTool):
    """Spy tool that records exact invocation counts to verify ZERO execution invariants."""

    def __init__(
        self,
        name: str = "spy_tool",
        risk_level: RiskLevel = RiskLevel.INFORMATIONAL,
        permissions: list = None,
        delay_seconds: float = 0.0,
        fail: bool = False,
    ):
        spec = ToolSpec(
            name=name,
            purpose="Spy tool for failure injection verification",
            input_schema={
                "type": "object",
                "properties": {
                    "payload": {"type": "string"},
                },
            },
            permission_requirements=permissions or [],
            risk_level=risk_level,
            failure_behavior=ToolFailureBehavior.FAIL_WORKFLOW,
        )
        super().__init__(spec)
        self.call_count = 0
        self.delay_seconds = delay_seconds
        self.fail = fail

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        self.call_count += 1
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)
        if self.fail:
            raise RuntimeError("Injected tool failure")
        return {"status": "success", "call_count": self.call_count}


# ============================================================================
# 1. Cyclic Plan Failure-Injection Tests
# ============================================================================

def test_failure_injection_self_loop_cycle_blocks_tool_execution():
    """Self-referential step cycle A -> A is blocked before execution; tool is never invoked."""
    spy = SpyTool(name="spy_self")
    registry = ToolRegistry()
    registry.register(spy)

    with pytest.raises(Exception) as exc_info:
        WorkflowPlan(
            session_id="sess-fail-1",
            correlation_id="corr-fail-1",
            title="Self Cycle Plan",
            steps=[
                WorkflowStep(
                    step_id="step-1",
                    tool_name="spy_self",
                    arguments={"payload": "test"},
                    description="Self looping step",
                    depends_on=["step-1"],
                )
            ],
        )

    assert "cannot depend on itself" in str(exc_info.value) or "Cyclic" in str(exc_info.value)
    assert spy.call_count == 0


def test_failure_injection_two_node_cycle_blocks_tool_execution():
    """Direct 2-node cycle A -> B -> A is detected and rejected; zero tools execute."""
    spy1 = SpyTool(name="spy_1")
    spy2 = SpyTool(name="spy_2")
    registry = ToolRegistry()
    registry.register(spy1)
    registry.register(spy2)

    step_a = WorkflowStep(
        step_id="step-a",
        tool_name="spy_1",
        arguments={"payload": "a"},
        description="Step A",
        depends_on=["step-b"],
    )
    step_b = WorkflowStep(
        step_id="step-b",
        tool_name="spy_2",
        arguments={"payload": "b"},
        description="Step B",
        depends_on=["step-a"],
    )

    plan = WorkflowPlan.model_construct(
        plan_id="plan-cycle-2",
        session_id="sess-cycle-2",
        correlation_id="corr-cycle-2",
        title="Direct Cycle Plan",
        steps=[step_a, step_b],
    )

    validator = PlanValidator(registry=registry)
    with pytest.raises(PlanValidationError) as exc_info:
        validator.validate_dependencies_and_cycles(plan)

    assert "Cyclic dependency detected" in str(exc_info.value)
    assert spy1.call_count == 0
    assert spy2.call_count == 0


def test_failure_injection_three_node_cycle_blocks_tool_execution():
    """Multi-node cycle A -> B -> C -> A is detected by 3-color DFS; zero tools execute."""
    spy = SpyTool(name="spy_multi")
    registry = ToolRegistry()
    registry.register(spy)

    steps = [
        WorkflowStep(
            step_id="step-1",
            tool_name="spy_multi",
            arguments={"payload": "1"},
            description="Step 1",
            depends_on=["step-3"],
        ),
        WorkflowStep(
            step_id="step-2",
            tool_name="spy_multi",
            arguments={"payload": "2"},
            description="Step 2",
            depends_on=["step-1"],
        ),
        WorkflowStep(
            step_id="step-3",
            tool_name="spy_multi",
            arguments={"payload": "3"},
            description="Step 3",
            depends_on=["step-2"],
        ),
    ]

    plan = WorkflowPlan.model_construct(
        plan_id="plan-cycle-3",
        session_id="sess-cycle-3",
        correlation_id="corr-cycle-3",
        title="3-Node Cycle Plan",
        steps=steps,
    )

    validator = PlanValidator(registry=registry)
    with pytest.raises(PlanValidationError) as exc_info:
        validator.validate_plan(plan)

    assert "Cyclic dependency detected" in str(exc_info.value)
    assert spy.call_count == 0


# ============================================================================
# 2. Malicious and Out-of-Scope Argument Tests
# ============================================================================

def test_failure_injection_path_traversal_linux_rejected():
    """Path traversal payload '../' is detected and rejected; tool is never executed."""
    registry = ToolRegistry.get_default_registry()
    tool = registry.get("course_schedule")

    with pytest.raises(ValueError) as exc_info:
        tool.validate_arguments({"course_code": "../../etc/passwd"})

    assert "path traversal sequence" in str(exc_info.value).lower()


def test_failure_injection_path_traversal_windows_rejected():
    """Windows path traversal payload '..\\windows\\system32' is rejected before tool runs."""
    registry = ToolRegistry.get_default_registry()
    tool = registry.get("course_schedule")

    with pytest.raises(ValueError) as exc_info:
        tool.validate_arguments({"course_code": "..\\windows\\system32"})

    assert "path traversal sequence" in str(exc_info.value).lower()


def test_failure_injection_null_byte_injection_rejected():
    """Null byte string injection is rejected; tool execution is strictly prevented."""
    registry = ToolRegistry.get_default_registry()
    tool = registry.get("knowledge_search")

    with pytest.raises(ValueError) as exc_info:
        tool.validate_arguments({"query": "cs101\x00malicious_code"})

    assert "null byte" in str(exc_info.value).lower()


def test_failure_injection_out_of_scope_extra_field_rejected():
    """Undeclared or out-of-scope fields are rejected by strict schema validation."""
    registry = ToolRegistry.get_default_registry()
    tool = registry.get("knowledge_search")

    with pytest.raises(ValueError) as exc_info:
        tool.validate_arguments({
            "query": "cs101",
            "unauthorized_admin_param": True,
        })

    assert "out-of-scope argument" in str(exc_info.value) or "disallowed" in str(exc_info.value)


def test_failure_injection_negative_integer_bounds_rejected():
    """Out-of-bounds integer arguments (e.g. max_results < 1) are rejected."""
    registry = ToolRegistry.get_default_registry()
    tool = registry.get("knowledge_search")

    with pytest.raises(ValueError) as exc_info:
        tool.validate_arguments({"query": "cs101", "max_results": -5})

    assert "must be >= 1" in str(exc_info.value)


def test_failure_injection_unregistered_shadow_tool_rejected():
    """A plan referencing an unregistered shadow tool is rejected; zero tools run."""
    step = WorkflowStep(
        step_id="step-shadow",
        tool_name="unregistered_shadow_tool",
        arguments={"cmd": "whoami"},
        description="Shadow tool attempt",
    )
    plan = WorkflowPlan.model_construct(
        plan_id="plan-shadow",
        session_id="sess-shadow",
        correlation_id="corr-shadow",
        title="Shadow Tool Plan",
        steps=[step],
    )
    validator = PlanValidator()
    with pytest.raises(PlanValidationError) as exc_info:
        validator.validate_tools_and_arguments(plan)

    assert "not in allow-list" in str(exc_info.value)


# ============================================================================
# 3. Duplicate Submissions & Re-execution Protection
# ============================================================================

def test_failure_injection_duplicate_step_id_rejected():
    """Plans containing duplicate step IDs are rejected before execution."""
    with pytest.raises(Exception) as exc_info:
        WorkflowPlan(
            session_id="sess-dup-1",
            correlation_id="corr-dup-1",
            title="Duplicate Steps Plan",
            steps=[
                WorkflowStep(
                    step_id="step-dup",
                    tool_name="knowledge_search",
                    arguments={"query": "cs101"},
                    description="First step",
                ),
                WorkflowStep(
                    step_id="step-dup",
                    tool_name="knowledge_search",
                    arguments={"query": "cs101"},
                    description="Duplicate step",
                ),
            ],
        )

    assert "Duplicate step_id detected" in str(exc_info.value)


def test_failure_injection_duplicate_execution_prevented_by_idempotency():
    """Idempotent step executed twice only runs live tool once; second call uses cache."""
    spy = SpyTool(name="spy_idemp")
    registry = ToolRegistry()
    registry.register(spy)

    step = WorkflowStep(
        step_id="step-idemp",
        tool_name="spy_idemp",
        arguments={"payload": "cache_test"},
        description="Idempotent test step",
        is_idempotent=True,
        idempotency_key="idemp-test-shared-key",
    )
    plan = WorkflowPlan(
        session_id="sess-idemp",
        correlation_id="corr-idemp",
        title="Idempotency Plan",
        steps=[step],
    )

    executor = WorkflowExecutor(plan=plan, registry=registry)
    res1 = executor.run()
    assert res1.final_state == WorkflowState.SUCCEEDED
    assert spy.call_count == 1

    # Second execution of identical step in new plan using shared idempotency store
    step2 = WorkflowStep(
        step_id="step-idemp-2",
        tool_name="spy_idemp",
        arguments={"payload": "cache_test"},
        description="Idempotent test step",
        is_idempotent=True,
        idempotency_key="idemp-test-shared-key",
    )
    plan2 = WorkflowPlan(
        session_id="sess-idemp-2",
        correlation_id="corr-idemp-2",
        title="Idempotency Plan 2",
        steps=[step2],
    )
    executor2 = WorkflowExecutor(
        plan=plan2,
        registry=registry,
        idempotency_store=executor.idempotency_store,
    )
    res2 = executor2.run()
    assert res2.final_state == WorkflowState.SUCCEEDED
    # Tool must NOT have been called a second time
    assert spy.call_count == 1


def test_failure_injection_duplicate_approval_rejected():
    """Attempting to approve an already approved approval request raises ValueError."""
    spy = SpyTool(name="spy_conseq", risk_level=RiskLevel.SENSITIVE)
    registry = ToolRegistry()
    registry.register(spy)

    step = WorkflowStep(
        step_id="step-conseq",
        tool_name="spy_conseq",
        arguments={"payload": "sensitive_data"},
        description="Sensitive action",
        risk_level=RiskLevel.SENSITIVE,
        requires_approval=True,
    )
    plan = WorkflowPlan(
        session_id="sess-dup-appr",
        correlation_id="corr-dup-appr",
        title="Duplicate Approval Plan",
        steps=[step],
    )

    executor = WorkflowExecutor(plan=plan, registry=registry)
    result = executor.run()
    assert result is None
    assert len(executor.pending_approvals) == 1
    approval_id = list(executor.pending_approvals.keys())[0]

    # First approval succeeds
    executor.approve_request(approval_id)
    assert spy.call_count == 1

    # Second approval attempt must raise error and NOT re-execute tool
    with pytest.raises(ValueError) as exc_info:
        executor.approve_request(approval_id)

    assert "Duplicate approval rejected" in str(exc_info.value)
    assert spy.call_count == 1


def test_failure_injection_approving_rejected_request_rejected():
    """Attempting to approve a previously rejected request is refused."""
    spy = SpyTool(name="spy_rej", risk_level=RiskLevel.SENSITIVE)
    registry = ToolRegistry()
    registry.register(spy)

    step = WorkflowStep(
        step_id="step-rej",
        tool_name="spy_rej",
        arguments={"payload": "sensitive_data"},
        description="Sensitive action",
        risk_level=RiskLevel.SENSITIVE,
        requires_approval=True,
    )
    plan = WorkflowPlan(
        session_id="sess-rej",
        correlation_id="corr-rej",
        title="Rejection Plan",
        steps=[step],
    )

    executor = WorkflowExecutor(plan=plan, registry=registry)
    executor.run()
    approval_id = list(executor.pending_approvals.keys())[0]

    # Reject request
    executor.reject_request(approval_id, reason="Denied by supervisor")
    assert spy.call_count == 0

    # Approving rejected request raises ValueError
    with pytest.raises(ValueError) as exc_info:
        executor.approve_request(approval_id)

    assert "already rejected" in str(exc_info.value)
    assert spy.call_count == 0


# ============================================================================
# 4. Step Timeout and Retry Protection
# ============================================================================

def test_failure_injection_step_timeout_enforced():
    """Step execution exceeding timeout_seconds is terminated with TimeoutError."""
    slow_spy = SpyTool(name="slow_spy", delay_seconds=0.2)
    registry = ToolRegistry()
    registry.register(slow_spy)

    step = WorkflowStep(
        step_id="step-slow",
        tool_name="slow_spy",
        arguments={"payload": "slow"},
        description="Slow step",
        timeout_seconds=0.05,
    )
    plan = WorkflowPlan(
        session_id="sess-tout",
        correlation_id="corr-tout",
        title="Timeout Plan",
        steps=[step],
    )

    executor = WorkflowExecutor(plan=plan, registry=registry)
    result = executor.run()
    assert result.final_state == WorkflowState.FAILED
    assert "timed out" in str(result.error_details).lower()


def test_failure_injection_non_idempotent_step_never_retried():
    """Non-idempotent steps timing out or failing are strictly never retried."""
    failing_spy = SpyTool(name="fail_spy", fail=True)
    registry = ToolRegistry()
    registry.register(failing_spy)

    step = WorkflowStep(
        step_id="step-non-idemp",
        tool_name="fail_spy",
        arguments={"payload": "mutation"},
        description="Non-idempotent mutation",
        is_idempotent=False,
        retry_policy=RetryPolicy(max_retries=3, backoff_seconds=0.01),
    )
    plan = WorkflowPlan(
        session_id="sess-no-retry",
        correlation_id="corr-no-retry",
        title="Non-Idempotent Plan",
        steps=[step],
    )

    executor = WorkflowExecutor(plan=plan, registry=registry)
    result = executor.run()
    assert result.final_state == WorkflowState.FAILED
    # Even though retry_policy asked for 3 retries, call_count must be strictly 1
    assert failing_spy.call_count == 1


# ============================================================================
# 5. Rejected and Expired Approvals Guarantee Zero Execution
# ============================================================================

def test_failure_injection_rejected_approval_guarantees_zero_execution():
    """Rejection of a consequential action guarantees tool execute() is NEVER called."""
    spy = SpyTool(name="spy_conseq", risk_level=RiskLevel.DESTRUCTIVE)
    registry = ToolRegistry()
    registry.register(spy)

    step = WorkflowStep(
        step_id="step-destructive",
        tool_name="spy_conseq",
        arguments={"payload": "delete_all"},
        description="Destructive action",
        risk_level=RiskLevel.DESTRUCTIVE,
        requires_approval=True,
    )
    plan = WorkflowPlan(
        session_id="sess-rej-zero",
        correlation_id="corr-rej-zero",
        title="Zero Execution Rejection Plan",
        steps=[step],
    )

    executor = WorkflowExecutor(plan=plan, registry=registry)
    executor.run()
    approval_id = list(executor.pending_approvals.keys())[0]

    result = executor.reject_request(approval_id, reason="Security veto")
    assert result.final_state == WorkflowState.CANCELLED
    assert step.status == StepStatus.CANCELLED
    # Absolutely zero tool invocations
    assert spy.call_count == 0


def test_failure_injection_expired_approval_guarantees_zero_execution():
    """Expired approval strictly prevents tool execution."""
    spy = SpyTool(name="spy_conseq", risk_level=RiskLevel.SENSITIVE)
    registry = ToolRegistry()
    registry.register(spy)

    step = WorkflowStep(
        step_id="step-expire",
        tool_name="spy_conseq",
        arguments={"payload": "action"},
        description="Sensitive action",
        risk_level=RiskLevel.SENSITIVE,
        requires_approval=True,
    )
    plan = WorkflowPlan(
        session_id="sess-exp-zero",
        correlation_id="corr-exp-zero",
        title="Zero Execution Expired Plan",
        steps=[step],
    )

    executor = WorkflowExecutor(plan=plan, registry=registry, default_approval_ttl_seconds=0.01)
    executor.run()
    approval_id = list(executor.pending_approvals.keys())[0]

    # Wait for TTL to expire
    time.sleep(0.02)
    result = executor.check_for_expired_approvals()

    assert result is not None
    assert result.final_state == WorkflowState.CANCELLED
    assert spy.call_count == 0


# ============================================================================
# 6. Missing Permission Scope Failure-Injection
# ============================================================================

def test_failure_injection_missing_permission_scope_blocks_tool_execution():
    """Caller without required permission scope is blocked before tool runs."""
    spy = SpyTool(name="spy_admin", permissions=["admin:write"])
    registry = ToolRegistry()
    registry.register(spy)

    step = WorkflowStep(
        step_id="step-perm",
        tool_name="spy_admin",
        arguments={"payload": "admin_action"},
        description="Admin tool execution",
    )
    plan = WorkflowPlan(
        session_id="sess-perm-fail",
        correlation_id="corr-perm-fail",
        title="Permission Check Plan",
        steps=[step],
    )

    executor = WorkflowExecutor(
        plan=plan,
        registry=registry,
        caller_permissions=["student:read"],  # Missing "admin:write"
    )
    result = executor.run()
    assert result.final_state == WorkflowState.FAILED
    assert "requires permission 'admin:write'" in str(result.error_details)
    assert spy.call_count == 0
