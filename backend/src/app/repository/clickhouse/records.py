import types
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Literal, TypeAliasType, cast, get_args, get_origin, get_type_hints


def base_type(kind: Any) -> Any:
    return base_type(kind.__value__) if isinstance(kind, TypeAliasType) else kind


def optional(kind: Any) -> Any:
    args = get_args(kind)
    return next((a for a in args if a is not type(None)), None) if type(None) in args else None


def compound(kind: Any) -> bool:
    return is_dataclass(kind) or get_origin(base_type(kind)) in (list, tuple)


def encode(kind: Any, value: Any) -> Any:
    kind = base_type(kind)
    inner = optional(kind)
    if inner is not None:
        if compound(inner):
            return [] if value is None else [encode(inner, value)]
        return None if value is None else encode(inner, value)
    if is_dataclass(kind):
        hints = get_type_hints(kind)
        return {f.name: encode(hints[f.name], getattr(value, f.name)) for f in fields(kind)}
    origin, args = get_origin(kind), get_args(kind)
    if origin is list:
        return [encode(args[0], item) for item in value]
    if origin is tuple:
        return [encode(k, v) for k, v in zip(args, value, strict=True)]
    return value.value if isinstance(value, Enum) else value


def decode(kind: Any, value: Any) -> Any:
    kind = base_type(kind)
    inner = optional(kind)
    if inner is not None:
        if compound(inner):
            return decode(inner, value[0]) if value else None
        return None if value is None else decode(inner, value)
    if is_dataclass(kind):
        hints = get_type_hints(kind)
        return cast(Any, kind)(
            **{f.name: decode(hints[f.name], value[f.name]) for f in fields(kind)}
        )
    origin, args = get_origin(kind), get_args(kind)
    if origin is list:
        return [decode(args[0], item) for item in value]
    if origin is tuple:
        return tuple(decode(k, v) for k, v in zip(args, value, strict=True))
    if isinstance(kind, type) and issubclass(kind, Enum):
        return kind(value)
    return kind(value) if kind in (float, int, str, bool) else value


def sql_type(kind: Any) -> str:
    kind = base_type(kind)
    origin, args = get_origin(kind), get_args(kind)
    if origin is types.UnionType:
        inner = optional(kind)
        return ("Array(" if compound(inner) else "Nullable(") + sql_type(inner) + ")"
    if is_dataclass(kind):
        hints = get_type_hints(kind)
        return (
            "Tuple("
            + ",".join("`" + f.name + "` " + sql_type(hints[f.name]) for f in fields(kind))
            + ")"
        )
    if origin is list:
        return "Array(" + sql_type(args[0]) + ")"
    if origin is tuple:
        return "Tuple(" + ",".join(sql_type(a) for a in args) + ")"
    if origin is Literal or isinstance(kind, type) and issubclass(kind, Enum):
        return "String"
    return {str: "String", int: "Int64", float: "Float64", bool: "Bool"}[kind]


def columns(kind: Any) -> str:
    return ",".join("`" + f.name + "`" for f in fields(kind))
