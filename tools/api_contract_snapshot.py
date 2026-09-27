"""Generate the canonical PyPageKit 1.0 public contract snapshot."""

from __future__ import annotations

import dataclasses
import enum
import importlib
import inspect
import json
import tomllib
import types
import typing
from collections.abc import Callable as AbcCallable
from pathlib import Path
from typing import Any, get_args, get_origin

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_API_PATH = REPOSITORY_ROOT / "PUBLIC_API.toml"
DEPRECATIONS_PATH = REPOSITORY_ROOT / "DEPRECATIONS.toml"
TARGET_RELEASE = "1.0.0"
CONTRACT_SCHEMA_VERSION = 1


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as source:
        return tomllib.load(source)


def _public_modules(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    modules = inventory["modules"]
    if not isinstance(modules, list):
        raise TypeError("PUBLIC_API.toml modules must be a list.")
    return modules


def _canonical_paths(
    modules: list[dict[str, Any]],
) -> dict[int, str]:
    candidates: dict[int, list[str]] = {}

    for module_inventory in modules:
        module_name = module_inventory["name"]
        if not isinstance(module_name, str):
            raise TypeError("Public module name must be a string.")
        module = importlib.import_module(module_name)
        exports = module_inventory["exports"]
        if not isinstance(exports, list):
            raise TypeError(f"{module_name} exports must be a list.")

        for export_name in exports:
            if export_name == "__version__":
                continue
            if not isinstance(export_name, str):
                raise TypeError(f"{module_name} export names must be strings.")
            value = getattr(module, export_name)
            candidates.setdefault(id(value), []).append(f"{module_name}.{export_name}")

    result: dict[int, str] = {}
    for object_id, paths in candidates.items():
        result[object_id] = min(
            paths,
            key=lambda value: (
                value.count("."),
                len(value),
                value,
            ),
        )
    return result


def _normalized_module_name(module_name: str) -> str:
    if module_name == "pathlib._local":
        return "pathlib"
    return module_name


def _type_name(value: Any, canonical_paths: dict[int, str]) -> str:
    if value is inspect.Signature.empty:
        return ""
    if value is None or value is type(None):
        return "None"
    if isinstance(value, str):
        return value

    public_path = canonical_paths.get(id(value))
    if public_path is not None:
        return public_path

    origin = get_origin(value)
    if origin is not None:
        arguments = get_args(value)

        if origin in {typing.Union, types.UnionType}:
            return " | ".join(_type_name(argument, canonical_paths) for argument in arguments)

        if (
            origin in {typing.Callable, AbcCallable}
            and len(arguments) == 2
            and isinstance(arguments[0], list)
        ):
            parameters = ", ".join(
                _type_name(argument, canonical_paths) for argument in arguments[0]
            )
            result = _type_name(arguments[1], canonical_paths)
            return f"Callable[[{parameters}], {result}]"

        origin_name = _type_name(origin, canonical_paths)
        if arguments:
            argument_names = ", ".join(
                _type_name(argument, canonical_paths) for argument in arguments
            )
            return f"{origin_name}[{argument_names}]"
        return origin_name

    if isinstance(value, type):
        if value.__module__ == "builtins":
            return value.__qualname__
        module_name = _normalized_module_name(value.__module__)
        return f"{module_name}.{value.__qualname__}"

    rendered = repr(value)
    return rendered.replace("typing.", "typing.")


def _default_value(value: Any, canonical_paths: dict[int, str]) -> Any:
    if value is inspect.Signature.empty:
        return {"required": True}
    if value is None or isinstance(value, (bool, int, float, str)):
        return {"required": False, "value": value}
    if type(value).__module__ == "dataclasses" and repr(value) == "<factory>":
        return {"required": False, "value": "<factory>"}
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        public_type = canonical_paths.get(id(type(value)))
        if public_type is not None:
            state: dict[str, Any] = {}
            for field in dataclasses.fields(value):
                if field.name.startswith("_"):
                    continue
                field_value = _default_value(getattr(value, field.name), canonical_paths)
                state[field.name] = field_value["value"]
            return {
                "required": False,
                "value": {
                    "dataclass": public_type,
                    "state": state,
                },
            }
    if isinstance(value, enum.Enum):
        public_path = canonical_paths.get(id(type(value)))
        if public_path is not None:
            return {"required": False, "value": f"{public_path}.{value.name}"}
    if isinstance(value, tuple):
        return {
            "required": False,
            "value": [_default_value(item, canonical_paths)["value"] for item in value],
        }

    public_path = canonical_paths.get(id(value))
    if public_path is not None:
        return {"required": False, "value": public_path}

    module_name = _normalized_module_name(type(value).__module__)
    return {
        "required": False,
        "value": f"<{module_name}.{type(value).__qualname__}>",
    }


def _signature(
    value: Any,
    canonical_paths: dict[int, str],
) -> dict[str, Any] | None:
    try:
        signature = inspect.signature(value, eval_str=False)
    except (TypeError, ValueError):
        return None

    parameters: list[dict[str, Any]] = []
    for parameter in signature.parameters.values():
        item: dict[str, Any] = {
            "name": parameter.name,
            "kind": parameter.kind.name,
        }
        annotation = _type_name(parameter.annotation, canonical_paths)
        if annotation:
            item["annotation"] = annotation
        item.update(_default_value(parameter.default, canonical_paths))
        parameters.append(item)

    result: dict[str, Any] = {"parameters": parameters}
    return_annotation = _type_name(signature.return_annotation, canonical_paths)
    if return_annotation:
        result["return"] = return_annotation
    return result


def _member_descriptor(
    raw: Any,
    canonical_paths: dict[int, str],
) -> dict[str, Any] | None:
    binding = "instance"
    value = raw

    if isinstance(raw, staticmethod):
        binding = "static"
        value = raw.__func__
    elif isinstance(raw, classmethod):
        binding = "class"
        value = raw.__func__

    if isinstance(raw, property):
        descriptor: dict[str, Any] = {"kind": "property"}
        if raw.fget is not None:
            signature = _signature(raw.fget, canonical_paths)
            if signature is not None:
                descriptor["signature"] = signature
        return descriptor

    if inspect.isfunction(value):
        descriptor = {
            "kind": "method",
            "binding": binding,
        }
        signature = _signature(value, canonical_paths)
        if signature is not None:
            descriptor["signature"] = signature
        if getattr(value, "__isabstractmethod__", False):
            descriptor["abstract"] = True
        return descriptor

    return None


def _dataclass_fields(
    cls: type[Any],
    canonical_paths: dict[int, str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for field in dataclasses.fields(cls):
        if field.name.startswith("_"):
            continue

        item: dict[str, Any] = {
            "name": field.name,
            "type": _type_name(field.type, canonical_paths),
            "init": field.init,
            "kw_only": field.kw_only,
        }
        if field.default is not dataclasses.MISSING:
            item["default"] = _default_value(field.default, canonical_paths)["value"]
        elif field.default_factory is not dataclasses.MISSING:
            factory = field.default_factory
            public_path = canonical_paths.get(id(factory))
            item["default_factory"] = public_path or getattr(
                factory,
                "__qualname__",
                type(factory).__qualname__,
            )
        else:
            item["required"] = True
        result.append(item)

    return result


def _public_class_bases(
    cls: type[Any],
    canonical_paths: dict[int, str],
) -> list[str]:
    bases: list[str] = []
    for base in cls.__bases__:
        public_path = canonical_paths.get(id(base))
        if public_path is not None:
            bases.append(public_path)
        elif base is object:
            bases.append("object")
        elif base.__module__ in {"builtins", "typing", "enum"}:
            bases.append(f"{base.__module__}.{base.__qualname__}")
    return bases


def _public_exception_bases(
    cls: type[BaseException],
    canonical_paths: dict[int, str],
) -> list[str]:
    bases: list[str] = []
    for base in cls.__bases__:
        public_path = canonical_paths.get(id(base))
        if public_path is not None:
            bases.append(public_path)
        elif base is Exception:
            bases.append("Exception")
        elif base is BaseException:
            bases.append("BaseException")
        else:
            bases.append(f"{base.__module__}.{base.__qualname__}")
    return bases


def _class_descriptor(
    cls: type[Any],
    canonical_paths: dict[int, str],
) -> dict[str, Any]:
    if issubclass(cls, BaseException):
        return {
            "kind": "exception",
            "bases": _public_exception_bases(cls, canonical_paths),
        }

    if issubclass(cls, enum.Enum):
        return {
            "kind": "enum",
            "members": {member.name: member.value for member in cls},
        }

    descriptor: dict[str, Any] = {
        "kind": "protocol" if getattr(cls, "_is_protocol", False) else "class",
        "bases": _public_class_bases(cls, canonical_paths),
    }
    if inspect.isabstract(cls):
        descriptor["abstract"] = True

    signature = _signature(cls, canonical_paths)
    if signature is not None:
        descriptor["signature"] = signature

    if dataclasses.is_dataclass(cls):
        params = cls.__dataclass_params__
        descriptor["dataclass"] = {
            "eq": params.eq,
            "frozen": params.frozen,
            "order": params.order,
            "unsafe_hash": params.unsafe_hash,
            "fields": _dataclass_fields(cls, canonical_paths),
        }

    members: dict[str, Any] = {}
    for name, raw in cls.__dict__.items():
        if name.startswith("_"):
            continue
        member = _member_descriptor(raw, canonical_paths)
        if member is not None:
            members[name] = member
    if members:
        descriptor["members"] = dict(sorted(members.items()))

    return descriptor


def _symbol_descriptor(
    value: Any,
    canonical_paths: dict[int, str],
) -> dict[str, Any]:
    if inspect.isclass(value):
        return _class_descriptor(value, canonical_paths)

    if inspect.isfunction(value):
        descriptor: dict[str, Any] = {"kind": "function"}
        signature = _signature(value, canonical_paths)
        if signature is not None:
            descriptor["signature"] = signature
        return descriptor

    origin = get_origin(value)
    if origin is not None:
        return {
            "kind": "type_alias",
            "type": _type_name(value, canonical_paths),
        }

    if isinstance(value, (str, int, float, bool)) or value is None:
        return {
            "kind": "constant",
            "type": type(value).__name__,
            "value": value,
        }

    return {
        "kind": "object",
        "type": _type_name(type(value), canonical_paths),
    }


def build_snapshot() -> dict[str, Any]:
    inventory = _load_toml(PUBLIC_API_PATH)
    deprecations = _load_toml(DEPRECATIONS_PATH)
    modules = _public_modules(inventory)
    canonical_paths = _canonical_paths(modules)

    stable_facades: dict[str, Any] = {}
    provisional_facades: dict[str, Any] = {}

    for module_inventory in modules:
        module_name = module_inventory["name"]
        classification = module_inventory["classification"]
        exports = module_inventory["exports"]
        if not isinstance(module_name, str) or not isinstance(classification, str):
            raise TypeError("Invalid public module inventory.")
        if not isinstance(exports, list):
            raise TypeError(f"{module_name} exports must be a list.")

        if classification == "stable":
            module = importlib.import_module(module_name)
            symbols: dict[str, Any] = {}
            for export_name in exports:
                if not isinstance(export_name, str):
                    raise TypeError("Public export name must be a string.")
                if export_name == "__version__":
                    symbols[export_name] = {"kind": "version"}
                else:
                    symbols[export_name] = _symbol_descriptor(
                        getattr(module, export_name),
                        canonical_paths,
                    )
            stable_facades[module_name] = {
                "exports": exports,
                "symbols": symbols,
            }
        elif classification == "provisional_public":
            provisional_facades[module_name] = {
                "frozen": False,
            }

    return {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "target_release": TARGET_RELEASE,
        "stable_facades": stable_facades,
        "provisional_facades": provisional_facades,
        "operational_contracts": {
            "cli": inventory["cli"],
            "extensions": inventory["extensions"],
            "typing": inventory["typing"],
        },
        "active_deprecations": deprecations["deprecations"],
    }


def render_snapshot() -> str:
    """Return canonical formatted JSON for the current runtime contract."""

    return (
        json.dumps(
            build_snapshot(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )


def main() -> None:
    print(render_snapshot(), end="")


if __name__ == "__main__":
    main()
