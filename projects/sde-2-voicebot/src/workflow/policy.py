"""
Policy Matrix and Enforcement Engine for Academiaai AI Voicebot.
Workstream: W4 (Agentic Workflow) - Team SDE 2
Author: Karthik N M

Week 4 (Days 25-27 Deliverable):
Defines the canonical Policy Matrix mapping (Tool x Risk Level x Approval Required x Permissions x Retries).
Enforces strict policy invariants:
1. Consequential steps (SENSITIVE and DESTRUCTIVE) strictly require human approval.
2. Callers must possess all required permission scopes.
3. Non-idempotent or destructive steps strictly forbid automatic retries.
4. Step timeouts must not exceed policy-configured maximum thresholds.
"""

from typing import Any, Dict, Iterable, List, Optional, Set
from pydantic import BaseModel, Field

from src.workflow.schemas import (
    RiskLevel,
    ToolFailureBehavior,
    WorkflowPlan,
    WorkflowStep,
)


class PolicyViolationError(Exception):
    """Raised when a step or plan violates the security Policy Matrix."""

    def __init__(
        self,
        message: str,
        step_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.step_id = step_id
        self.tool_name = tool_name
        self.details = details or {}


class PolicyRule(BaseModel):
    """
    Individual row in the Policy Matrix.
    Defines security and operational boundaries for an allow-listed tool.
    """

    tool_name: str = Field(..., description="Unique tool name")
    risk_level: RiskLevel = Field(..., description="PRD Risk category")
    approval_required: bool = Field(..., description="Whether human approval gate is mandatory")
    allowed_caller_permissions: List[str] = Field(
        default_factory=list, description="Scopes required to execute this tool"
    )
    failure_behavior: ToolFailureBehavior = Field(
        default=ToolFailureBehavior.FAIL_WORKFLOW,
        description="Standard failure behavior",
    )
    max_timeout_seconds: float = Field(
        default=60.0, ge=0.1, description="Upper bound for step execution timeout"
    )
    allow_retries: bool = Field(
        default=True, description="Whether idempotent retries are permitted"
    )
    description: str = Field(..., description="Policy rule rationale and purpose")


class PolicyMatrix:
    """
    Security and Governance Policy Matrix for the Agentic Workflow Engine.
    Maintains authoritative mappings and validates plans and steps against them.
    """

    def __init__(self, rules: Optional[List[PolicyRule]] = None):
        self._rules: Dict[str, PolicyRule] = {}
        if rules:
            for rule in rules:
                self.register_rule(rule)
        else:
            self._load_default_matrix()

    def _load_default_matrix(self) -> None:
        """Populates the canonical enterprise policy matrix."""
        default_rules = [
            PolicyRule(
                tool_name="knowledge_search",
                risk_level=RiskLevel.INFORMATIONAL,
                approval_required=False,
                allowed_caller_permissions=["kb:read"],
                failure_behavior=ToolFailureBehavior.FAIL_WORKFLOW,
                max_timeout_seconds=30.0,
                allow_retries=True,
                description="Read-only search across academic FAQs, catalogs, and documentation.",
            ),
            PolicyRule(
                tool_name="course_schedule",
                risk_level=RiskLevel.INFORMATIONAL,
                approval_required=False,
                allowed_caller_permissions=["schedule:read"],
                failure_behavior=ToolFailureBehavior.FAIL_WORKFLOW,
                max_timeout_seconds=30.0,
                allow_retries=True,
                description="Read-only query of course times, rooms, and instructor schedules.",
            ),
            PolicyRule(
                tool_name="student_record_query",
                risk_level=RiskLevel.LOW_RISK,
                approval_required=False,
                allowed_caller_permissions=["student:read"],
                failure_behavior=ToolFailureBehavior.FAIL_WORKFLOW,
                max_timeout_seconds=30.0,
                allow_retries=True,
                description="Low-risk read-only query of enrolled student records within authorized scope.",
            ),
            PolicyRule(
                tool_name="update_student_profile",
                risk_level=RiskLevel.SENSITIVE,
                approval_required=True,
                allowed_caller_permissions=["student:write"],
                failure_behavior=ToolFailureBehavior.FAIL_WORKFLOW,
                max_timeout_seconds=60.0,
                allow_retries=False,
                description="Mutates student records or contact details. Human approval is mandatory.",
            ),
            PolicyRule(
                tool_name="drop_course_registration",
                risk_level=RiskLevel.SENSITIVE,
                approval_required=True,
                allowed_caller_permissions=["enrollment:write"],
                failure_behavior=ToolFailureBehavior.FAIL_WORKFLOW,
                max_timeout_seconds=60.0,
                allow_retries=False,
                description="Drops an enrolled course. Academic impact requires explicit student/advisor confirmation.",
            ),
            PolicyRule(
                tool_name="delete_student_account",
                risk_level=RiskLevel.DESTRUCTIVE,
                approval_required=True,
                allowed_caller_permissions=["admin:delete"],
                failure_behavior=ToolFailureBehavior.FAIL_WORKFLOW,
                max_timeout_seconds=60.0,
                allow_retries=False,
                description="Permanently deletes user account and records. Strictly requires human approval.",
            ),
        ]
        for rule in default_rules:
            self.register_rule(rule)

    def register_rule(self, rule: PolicyRule) -> None:
        """Registers or overrides a policy rule."""
        self._rules[rule.tool_name] = rule

    def get_rule(self, tool_name: str) -> Optional[PolicyRule]:
        """Retrieves the policy rule for a tool if registered."""
        return self._rules.get(tool_name)

    def has_rule(self, tool_name: str) -> bool:
        """Checks if a tool has a specific policy rule."""
        return tool_name in self._rules

    def list_rules(self) -> List[PolicyRule]:
        """Returns all registered policy rules."""
        return list(self._rules.values())

    def enforce_step(
        self,
        step: WorkflowStep,
        caller_permissions: Optional[Iterable[str]] = None,
    ) -> None:
        """
        Enforces policy matrix compliance for a single step:
        1. Universal Invariant: SENSITIVE or DESTRUCTIVE steps must require approval.
        2. Policy Rule Invariant: Tool must comply with registered PolicyRule.
        3. Permission Invariant: Caller must possess required permission scopes.
        4. Retry Invariant: Non-idempotent or non-retryable tools must not have retry policies.
        5. Timeout Invariant: Timeout must not exceed policy max_timeout_seconds.
        """
        # Universal Consequential Invariant
        if step.risk_level in (RiskLevel.SENSITIVE, RiskLevel.DESTRUCTIVE):
            if not step.requires_approval:
                raise PolicyViolationError(
                    f"Policy Violation: Step '{step.step_id}' with risk level '{step.risk_level.value}' "
                    f"MUST require human approval.",
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    details={"risk_level": step.risk_level.value, "requires_approval": step.requires_approval},
                )

        rule = self.get_rule(step.tool_name)
        if rule:
            # Check risk level matches policy rule
            if rule.approval_required and not step.requires_approval:
                raise PolicyViolationError(
                    f"Policy Violation: Tool '{step.tool_name}' requires human approval under policy rule.",
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    details={"policy_requires_approval": rule.approval_required},
                )

            # Check caller permissions
            if caller_permissions is not None:
                granted_set = set(caller_permissions)
                for req in rule.allowed_caller_permissions:
                    if req not in granted_set:
                        raise PolicyViolationError(
                            f"Policy Violation: Caller missing required permission '{req}' for tool '{step.tool_name}'. "
                            f"Granted scopes: {sorted(list(granted_set))}",
                            step_id=step.step_id,
                            tool_name=step.tool_name,
                            details={"required_permission": req, "granted_permissions": list(granted_set)},
                        )

            # Check retry policy
            if not rule.allow_retries or not step.is_idempotent:
                if step.retry_policy is not None and step.retry_policy.max_retries > 0:
                    raise PolicyViolationError(
                        f"Policy Violation: Retries are strictly prohibited for tool '{step.tool_name}' "
                        f"(is_idempotent={step.is_idempotent}, policy_allow_retries={rule.allow_retries}).",
                        step_id=step.step_id,
                        tool_name=step.tool_name,
                    )

            # Check timeout limit
            if step.timeout_seconds is not None and step.timeout_seconds > rule.max_timeout_seconds:
                raise PolicyViolationError(
                    f"Policy Violation: Step timeout {step.timeout_seconds}s exceeds maximum allowed "
                    f"policy threshold {rule.max_timeout_seconds}s for tool '{step.tool_name}'.",
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    details={"timeout_seconds": step.timeout_seconds, "max_allowed": rule.max_timeout_seconds},
                )

    def enforce_plan(
        self,
        plan: WorkflowPlan,
        caller_permissions: Optional[Iterable[str]] = None,
    ) -> None:
        """Validates all steps in a plan against the policy matrix."""
        for step in plan.steps:
            self.enforce_step(step, caller_permissions=caller_permissions)

    def as_markdown_table(self) -> str:
        """Returns the Policy Matrix formatted as a Markdown documentation table."""
        lines = [
            "| Tool Name | Risk Level | Approval Required | Required Scopes | Failure Behavior | Max Timeout | Retries Allowed | Purpose |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for rule in self.list_rules():
            scopes = ", ".join(f"`{s}`" for s in rule.allowed_caller_permissions) if rule.allowed_caller_permissions else "None"
            lines.append(
                f"| `{rule.tool_name}` | `{rule.risk_level.value}` | **{'YES' if rule.approval_required else 'NO'}** | "
                f"{scopes} | `{rule.failure_behavior.value}` | `{rule.max_timeout_seconds}s` | "
                f"{'Yes' if rule.allow_retries else 'No'} | {rule.description} |"
            )
        return "\n".join(lines)
