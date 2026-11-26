"""
Policy Matrix Enforcement Test Suite.
Workstream: W4 (Agentic Workflow) - Team SDE 2
Author: Karthik N M

Days 25-27 Deliverable:
Validates that the canonical Policy Matrix is defined, complete, and strictly enforced:
1. Every row of the policy matrix is tested against its security rules.
2. SENSITIVE and DESTRUCTIVE steps strictly require human approval.
3. Callers without required permission scopes are rejected.
4. Retries are strictly forbidden for non-idempotent or consequential tools.
5. Step timeouts exceeding policy bounds are rejected.
6. Markdown documentation generation is validated.
"""

import pytest

from src.workflow.schemas import (
    RetryPolicy,
    RiskLevel,
    ToolFailureBehavior,
    WorkflowPlan,
    WorkflowStep,
)
from src.workflow.policy import (
    PolicyMatrix,
    PolicyRule,
    PolicyViolationError,
)


@pytest.fixture
def matrix() -> PolicyMatrix:
    return PolicyMatrix()


# ============================================================================
# 1. Canonical Matrix Integrity Tests
# ============================================================================

def test_policy_matrix_contains_all_canonical_tools(matrix):
    """Verifies that all standard enterprise tools exist in the policy matrix."""
    expected_tools = {
        "knowledge_search",
        "course_schedule",
        "student_record_query",
        "update_student_profile",
        "drop_course_registration",
        "delete_student_account",
    }
    registered = {rule.tool_name for rule in matrix.list_rules()}
    for tool in expected_tools:
        assert tool in registered, f"Tool '{tool}' must exist in policy matrix"


# ============================================================================
# 2. Individual Row Enforcement Tests (Tool x Risk x Approval x Permissions)
# ============================================================================

def test_policy_matrix_enforces_row_knowledge_search(matrix):
    """Row 1: knowledge_search must be INFORMATIONAL, approval False, scope kb:read."""
    rule = matrix.get_rule("knowledge_search")
    assert rule.risk_level == RiskLevel.INFORMATIONAL
    assert rule.approval_required is False
    assert rule.allowed_caller_permissions == ["kb:read"]
    assert rule.allow_retries is True

    valid_step = WorkflowStep(
        step_id="s1",
        tool_name="knowledge_search",
        arguments={"query": "cs101"},
        description="Search info",
        risk_level=RiskLevel.INFORMATIONAL,
        requires_approval=False,
    )
    matrix.enforce_step(valid_step, caller_permissions=["kb:read"])


def test_policy_matrix_enforces_row_course_schedule(matrix):
    """Row 2: course_schedule must be INFORMATIONAL, approval False, scope schedule:read."""
    rule = matrix.get_rule("course_schedule")
    assert rule.risk_level == RiskLevel.INFORMATIONAL
    assert rule.approval_required is False
    assert rule.allowed_caller_permissions == ["schedule:read"]
    assert rule.allow_retries is True

    valid_step = WorkflowStep(
        step_id="s2",
        tool_name="course_schedule",
        arguments={"course_code": "CS101"},
        description="Lookup schedule",
        risk_level=RiskLevel.INFORMATIONAL,
        requires_approval=False,
    )
    matrix.enforce_step(valid_step, caller_permissions=["schedule:read"])


def test_policy_matrix_enforces_row_student_record_query(matrix):
    """Row 3: student_record_query is LOW_RISK, approval False, scope student:read."""
    rule = matrix.get_rule("student_record_query")
    assert rule.risk_level == RiskLevel.LOW_RISK
    assert rule.approval_required is False
    assert rule.allowed_caller_permissions == ["student:read"]

    valid_step = WorkflowStep(
        step_id="s3",
        tool_name="student_record_query",
        arguments={"student_id": "STU-001"},
        description="Query record",
        risk_level=RiskLevel.LOW_RISK,
        requires_approval=False,
    )
    matrix.enforce_step(valid_step, caller_permissions=["student:read"])


def test_policy_matrix_enforces_row_update_student_profile(matrix):
    """Row 4: update_student_profile is SENSITIVE, approval True, scope student:write, retries False."""
    rule = matrix.get_rule("update_student_profile")
    assert rule.risk_level == RiskLevel.SENSITIVE
    assert rule.approval_required is True
    assert rule.allowed_caller_permissions == ["student:write"]
    assert rule.allow_retries is False

    valid_step = WorkflowStep(
        step_id="s4",
        tool_name="update_student_profile",
        arguments={"student_id": "STU-001", "email": "test@uni.edu"},
        description="Update profile",
        risk_level=RiskLevel.SENSITIVE,
        requires_approval=True,
        is_idempotent=False,
    )
    matrix.enforce_step(valid_step, caller_permissions=["student:write"])


def test_policy_matrix_enforces_row_drop_course_registration(matrix):
    """Row 5: drop_course_registration is SENSITIVE, approval True, scope enrollment:write, retries False."""
    rule = matrix.get_rule("drop_course_registration")
    assert rule.risk_level == RiskLevel.SENSITIVE
    assert rule.approval_required is True
    assert rule.allowed_caller_permissions == ["enrollment:write"]
    assert rule.allow_retries is False

    valid_step = WorkflowStep(
        step_id="s5",
        tool_name="drop_course_registration",
        arguments={"student_id": "STU-001", "course_code": "CS101"},
        description="Drop course",
        risk_level=RiskLevel.SENSITIVE,
        requires_approval=True,
        is_idempotent=False,
    )
    matrix.enforce_step(valid_step, caller_permissions=["enrollment:write"])


def test_policy_matrix_enforces_row_delete_student_account(matrix):
    """Row 6: delete_student_account is DESTRUCTIVE, approval True, scope admin:delete, retries False."""
    rule = matrix.get_rule("delete_student_account")
    assert rule.risk_level == RiskLevel.DESTRUCTIVE
    assert rule.approval_required is True
    assert rule.allowed_caller_permissions == ["admin:delete"]
    assert rule.allow_retries is False

    valid_step = WorkflowStep(
        step_id="s6",
        tool_name="delete_student_account",
        arguments={"student_id": "STU-001"},
        description="Delete account",
        risk_level=RiskLevel.DESTRUCTIVE,
        requires_approval=True,
        is_idempotent=False,
    )
    matrix.enforce_step(valid_step, caller_permissions=["admin:delete"])


# ============================================================================
# 3. Violation Detection Tests
# ============================================================================

def test_policy_matrix_rejects_sensitive_step_without_approval(matrix):
    """Universal invariant: SENSITIVE step with requires_approval=False violates policy."""
    step = WorkflowStep.model_construct(
        step_id="s-bad",
        tool_name="update_student_profile",
        arguments={"student_id": "1"},
        description="Bad step",
        risk_level=RiskLevel.SENSITIVE,
        requires_approval=False,  # Unsafe bypass
    )
    with pytest.raises(PolicyViolationError) as exc_info:
        matrix.enforce_step(step)

    assert "MUST require human approval" in str(exc_info.value)


def test_policy_matrix_rejects_destructive_step_without_approval(matrix):
    """Universal invariant: DESTRUCTIVE step with requires_approval=False violates policy."""
    step = WorkflowStep.model_construct(
        step_id="s-bad",
        tool_name="delete_student_account",
        arguments={"student_id": "1"},
        description="Bad step",
        risk_level=RiskLevel.DESTRUCTIVE,
        requires_approval=False,  # Unsafe bypass
    )
    with pytest.raises(PolicyViolationError) as exc_info:
        matrix.enforce_step(step)

    assert "MUST require human approval" in str(exc_info.value)


def test_policy_matrix_rejects_caller_missing_permission_scope(matrix):
    """Policy matrix raises PolicyViolationError when caller lacks required permission scope."""
    step = WorkflowStep(
        step_id="s-perm",
        tool_name="delete_student_account",
        arguments={"student_id": "1"},
        description="Delete account",
        risk_level=RiskLevel.DESTRUCTIVE,
        requires_approval=True,
        is_idempotent=False,
    )
    with pytest.raises(PolicyViolationError) as exc_info:
        matrix.enforce_step(step, caller_permissions=["student:read"])

    assert "missing required permission 'admin:delete'" in str(exc_info.value)


def test_policy_matrix_rejects_retries_on_non_retryable_tool(matrix):
    """Policy matrix raises PolicyViolationError if retries are requested on non-retryable tool."""
    step = WorkflowStep(
        step_id="s-retry",
        tool_name="delete_student_account",
        arguments={"student_id": "1"},
        description="Delete account",
        risk_level=RiskLevel.DESTRUCTIVE,
        requires_approval=True,
        is_idempotent=False,
        retry_policy=RetryPolicy(max_retries=2),
    )
    with pytest.raises(PolicyViolationError) as exc_info:
        matrix.enforce_step(step, caller_permissions=["admin:delete"])

    assert "Retries are strictly prohibited" in str(exc_info.value)


def test_policy_matrix_rejects_excessive_step_timeout(matrix):
    """Policy matrix raises PolicyViolationError if step timeout exceeds max threshold."""
    step = WorkflowStep(
        step_id="s-tout",
        tool_name="knowledge_search",
        arguments={"query": "cs101"},
        description="Search info",
        risk_level=RiskLevel.INFORMATIONAL,
        requires_approval=False,
        timeout_seconds=90.0,  # Max allowed is 30.0s
    )
    with pytest.raises(PolicyViolationError) as exc_info:
        matrix.enforce_step(step, caller_permissions=["kb:read"])

    assert "exceeds maximum allowed policy threshold" in str(exc_info.value)


def test_policy_matrix_as_markdown_table_generates_valid_table(matrix):
    """Verifies that as_markdown_table produces a compliant markdown documentation table."""
    md = matrix.as_markdown_table()
    assert "| Tool Name | Risk Level | Approval Required |" in md
    assert "`knowledge_search`" in md
    assert "`course_schedule`" in md
    assert "`delete_student_account`" in md
    assert "**YES**" in md
    assert "**NO**" in md
