"""Compatibility checks from the frozen 1.0 contract to the current runtime snapshot."""

from __future__ import annotations

from typing import Any

_POSITIONAL_KINDS = {
    "POSITIONAL_ONLY",
    "POSITIONAL_OR_KEYWORD",
    "VAR_POSITIONAL",
}


def compatibility_errors(
    baseline: dict[str, Any],
    current: dict[str, Any],
) -> tuple[str, ...]:
    """Return deterministic incompatibility messages against a frozen baseline."""

    errors: list[str] = []

    if current.get("schema_version") != baseline.get("schema_version"):
        errors.append(
            "schema_version changed from "
            f"{baseline.get('schema_version')!r} to {current.get('schema_version')!r}"
        )

    _compare_stable_facades(
        baseline.get("stable_facades"),
        current.get("stable_facades"),
        errors,
    )
    _compare_provisional_facades(
        baseline.get("provisional_facades"),
        current.get("provisional_facades"),
        errors,
    )
    _compare_operational_contracts(
        baseline.get("operational_contracts"),
        current.get("operational_contracts"),
        errors,
    )

    return tuple(errors)


def _compare_stable_facades(
    baseline: object,
    current: object,
    errors: list[str],
) -> None:
    if not isinstance(baseline, dict) or not isinstance(current, dict):
        errors.append("stable_facades must remain mappings")
        return

    for module_name, baseline_module in baseline.items():
        path = f"stable_facades.{module_name}"
        current_module = current.get(module_name)

        if not isinstance(baseline_module, dict):
            errors.append(f"{path} baseline descriptor is invalid")
            continue
        if not isinstance(current_module, dict):
            errors.append(f"{path} was removed")
            continue

        baseline_exports = baseline_module.get("exports")
        current_exports = current_module.get("exports")
        baseline_symbols = baseline_module.get("symbols")
        current_symbols = current_module.get("symbols")

        if not isinstance(baseline_exports, list) or not isinstance(current_exports, list):
            errors.append(f"{path}.exports must remain lists")
            continue
        if not isinstance(baseline_symbols, dict) or not isinstance(current_symbols, dict):
            errors.append(f"{path}.symbols must remain mappings")
            continue

        for export_name in baseline_exports:
            export_path = f"{path}.{export_name}"
            if export_name not in current_exports:
                errors.append(f"{export_path} was removed")
                continue

            baseline_symbol = baseline_symbols.get(export_name)
            current_symbol = current_symbols.get(export_name)
            if not isinstance(baseline_symbol, dict) or not isinstance(current_symbol, dict):
                errors.append(f"{export_path} descriptor is missing or invalid")
                continue

            _compare_symbol(export_path, baseline_symbol, current_symbol, errors)


def _compare_provisional_facades(
    baseline: object,
    current: object,
    errors: list[str],
) -> None:
    if not isinstance(baseline, dict) or not isinstance(current, dict):
        errors.append("provisional_facades must remain mappings")
        return

    for module_name, baseline_descriptor in baseline.items():
        path = f"provisional_facades.{module_name}"
        current_descriptor = current.get(module_name)
        if current_descriptor is None:
            errors.append(f"{path} disappeared without an explicit promotion/migration decision")
            continue
        if current_descriptor != baseline_descriptor:
            errors.append(
                f"{path} changed from {baseline_descriptor!r} to {current_descriptor!r}"
            )


def _compare_operational_contracts(
    baseline: object,
    current: object,
    errors: list[str],
) -> None:
    if not isinstance(baseline, dict) or not isinstance(current, dict):
        errors.append("operational_contracts must remain mappings")
        return

    baseline_cli = baseline.get("cli")
    current_cli = current.get("cli")
    _compare_cli_contract(baseline_cli, current_cli, errors)

    for contract_name in ("extensions", "typing"):
        baseline_contract = baseline.get(contract_name)
        current_contract = current.get(contract_name)
        path = f"operational_contracts.{contract_name}"

        if not isinstance(baseline_contract, dict) or not isinstance(current_contract, dict):
            errors.append(f"{path} must remain a mapping")
            continue

        for key, baseline_value in baseline_contract.items():
            if key not in current_contract:
                errors.append(f"{path}.{key} was removed")
            elif current_contract[key] != baseline_value:
                errors.append(
                    f"{path}.{key} changed from {baseline_value!r} "
                    f"to {current_contract[key]!r}"
                )


def _compare_cli_contract(
    baseline: object,
    current: object,
    errors: list[str],
) -> None:
    path = "operational_contracts.cli"
    if not isinstance(baseline, dict) or not isinstance(current, dict):
        errors.append(f"{path} must remain a mapping")
        return

    additive_lists = {"commands", "root_options"}
    for key, baseline_value in baseline.items():
        item_path = f"{path}.{key}"
        if key not in current:
            errors.append(f"{item_path} was removed")
            continue

        current_value = current[key]
        if key in additive_lists:
            if not isinstance(baseline_value, list) or not isinstance(current_value, list):
                errors.append(f"{item_path} must remain a list")
                continue
            for item in baseline_value:
                if item not in current_value:
                    errors.append(f"{item_path} removed {item!r}")
        elif current_value != baseline_value:
            errors.append(
                f"{item_path} changed from {baseline_value!r} to {current_value!r}"
            )


def _compare_symbol(
    path: str,
    baseline: dict[str, Any],
    current: dict[str, Any],
    errors: list[str],
) -> None:
    baseline_kind = baseline.get("kind")
    current_kind = current.get("kind")

    if current_kind != baseline_kind:
        errors.append(f"{path}.kind changed from {baseline_kind!r} to {current_kind!r}")
        return

    if baseline_kind == "function":
        _compare_signature(
            f"{path}.signature",
            baseline.get("signature"),
            current.get("signature"),
            errors,
        )
        return

    if baseline_kind in {"class", "protocol"}:
        _compare_class(path, baseline, current, errors)
        return

    if current != baseline:
        errors.append(f"{path} changed incompatibly")


def _compare_class(
    path: str,
    baseline: dict[str, Any],
    current: dict[str, Any],
    errors: list[str],
) -> None:
    for key in ("bases", "abstract", "dataclass"):
        if (key in baseline or key in current) and current.get(key) != baseline.get(key):
            errors.append(
                f"{path}.{key} changed from {baseline.get(key)!r} "
                f"to {current.get(key)!r}"
            )

    if "signature" in baseline:
        _compare_signature(
            f"{path}.signature",
            baseline.get("signature"),
            current.get("signature"),
            errors,
        )
    elif "signature" in current:
        errors.append(f"{path}.signature was introduced on a previously unsignatured type")

    baseline_members = baseline.get("members", {})
    current_members = current.get("members", {})
    if not isinstance(baseline_members, dict) or not isinstance(current_members, dict):
        errors.append(f"{path}.members must remain mappings")
        return

    for member_name, baseline_member in baseline_members.items():
        member_path = f"{path}.{member_name}"
        current_member = current_members.get(member_name)

        if not isinstance(baseline_member, dict):
            errors.append(f"{member_path} baseline descriptor is invalid")
            continue
        if not isinstance(current_member, dict):
            errors.append(f"{member_path} was removed")
            continue

        if current_member.get("kind") != baseline_member.get("kind"):
            errors.append(
                f"{member_path}.kind changed from {baseline_member.get('kind')!r} "
                f"to {current_member.get('kind')!r}"
            )
            continue

        for key in ("binding", "abstract"):
            if (
                key in baseline_member or key in current_member
            ) and current_member.get(key) != baseline_member.get(key):
                errors.append(
                    f"{member_path}.{key} changed from {baseline_member.get(key)!r} "
                    f"to {current_member.get(key)!r}"
                )

        _compare_signature(
            f"{member_path}.signature",
            baseline_member.get("signature"),
            current_member.get("signature"),
            errors,
        )


def _compare_signature(
    path: str,
    baseline: object,
    current: object,
    errors: list[str],
) -> None:
    if baseline is None and current is None:
        return
    if not isinstance(baseline, dict) or not isinstance(current, dict):
        errors.append(f"{path} was removed or changed shape")
        return

    if current.get("return") != baseline.get("return"):
        errors.append(
            f"{path}.return changed from {baseline.get('return')!r} "
            f"to {current.get('return')!r}"
        )

    baseline_parameters = baseline.get("parameters")
    current_parameters = current.get("parameters")
    if not isinstance(baseline_parameters, list) or not isinstance(current_parameters, list):
        errors.append(f"{path}.parameters must remain lists")
        return

    baseline_by_name = {
        parameter.get("name"): parameter
        for parameter in baseline_parameters
        if isinstance(parameter, dict)
    }
    current_by_name = {
        parameter.get("name"): parameter
        for parameter in current_parameters
        if isinstance(parameter, dict)
    }

    baseline_positional = [
        parameter.get("name")
        for parameter in baseline_parameters
        if isinstance(parameter, dict)
        and parameter.get("kind") in _POSITIONAL_KINDS
    ]
    current_baseline_positional = [
        parameter.get("name")
        for parameter in current_parameters
        if isinstance(parameter, dict)
        and parameter.get("name") in baseline_by_name
        and parameter.get("kind") in _POSITIONAL_KINDS
    ]
    if current_baseline_positional != baseline_positional:
        errors.append(
            f"{path} changed positional parameter ordering from "
            f"{baseline_positional!r} to {current_baseline_positional!r}"
        )

    for parameter_name, baseline_parameter in baseline_by_name.items():
        parameter_path = f"{path}.parameters.{parameter_name}"
        current_parameter = current_by_name.get(parameter_name)
        if not isinstance(current_parameter, dict):
            errors.append(f"{parameter_path} was removed")
            continue

        for key in ("kind", "annotation", "required", "value"):
            if (
                key in baseline_parameter or key in current_parameter
            ) and current_parameter.get(key) != baseline_parameter.get(key):
                errors.append(
                    f"{parameter_path}.{key} changed from "
                    f"{baseline_parameter.get(key)!r} "
                    f"to {current_parameter.get(key)!r}"
                )

    for parameter_name, current_parameter in current_by_name.items():
        if parameter_name in baseline_by_name:
            continue
        parameter_path = f"{path}.parameters.{parameter_name}"
        if (
            current_parameter.get("kind") != "KEYWORD_ONLY"
            or current_parameter.get("required") is not False
        ):
            errors.append(
                f"{parameter_path} is a new parameter but is not optional keyword-only"
            )


__all__ = ["compatibility_errors"]
