"""
Thin wrappers for LangGraph nodes to inject security validation.

The wrapper intercepts agent outputs, runs S1 validation, and writes back the
patched text so downstream nodes see the sanitized content. Issues are
aggregated on the state under ``validation_issues`` for later inspection.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, MutableMapping, Optional

from defiagents.security.output_validator import OutputValidator, ValidationContext

State = Dict[str, Any]
NodeFunc = Callable[[State], Dict[str, Any]]


def _extract_protocol_name(state: MutableMapping[str, Any]) -> str:
    """
    Best-effort protocol name extraction for validation context.

    Falls back through the various aliases used across the codebase to avoid
    KeyError while still providing useful metadata to the validator.
    """
    for key in (
        "protocol_of_interest",
        "protocol_name",
        "company_name",
        "company_of_interest",
    ):
        value = state.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _merge_issues(target: MutableMapping[str, Any], issues: Iterable[dict]) -> None:
    """
    Append validation issues to the state's collection without discarding
    existing entries.
    """
    if not issues:
        return

    existing = target.get("validation_issues")
    if isinstance(existing, list):
        target["validation_issues"] = [*existing, *issues]
    else:
        target["validation_issues"] = list(issues)


def _build_context(
    agent_name: str, state: MutableMapping[str, Any]
) -> ValidationContext:
    """Construct a ValidationContext from the current state."""
    context: ValidationContext = {
        "agent_name": agent_name,
        "protocol_name": _extract_protocol_name(state),
        "investment_amount": state.get("investment_amount"),
    }
    return context


def wrap_agent_node_with_validation(
    node_func: NodeFunc, agent_name: str, state_key: str
) -> NodeFunc:
    """
    Wrap an agent node to run S1 output validation on its textual result.

    The wrapper leaves the original node behavior intact and only patches the
    designated ``state_key`` with the validator's ``patched_text``. If issues
    are detected they are collected under ``validation_issues`` for later use.
    """
    validator = OutputValidator()

    def validated_node(state: State) -> Dict[str, Any]:
        result = node_func(state)
        if not isinstance(result, dict):
            return result

        original_output = result.get(state_key)
        if not isinstance(original_output, str):
            return result

        validation_result = validator.validate(
            original_output, context=_build_context(agent_name, state)
        )

        result[state_key] = validation_result["patched_text"]
        if not validation_result["is_safe"]:
            _merge_issues(result, validation_result["issues"])

        return result

    return validated_node


__all__ = ["wrap_agent_node_with_validation"]
