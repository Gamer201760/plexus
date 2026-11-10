from typing import Any

import pyarrow as pa
from pyarrow import ipc


def arrow_value(kind: Any, value: Any) -> Any:
    if value is None:
        return None
    if pa.types.is_struct(kind):
        if isinstance(value, (list, tuple)):
            value = {field.name: item for field, item in zip(kind, value, strict=True)}
        return {field.name: arrow_value(field.type, value[field.name]) for field in kind}
    if pa.types.is_list(kind):
        return [arrow_value(kind.value_type, item) for item in value]
    return value


def arrow_body(schema: Any, rows: list[dict[str, Any]]) -> bytes:
    converted = [{f.name: arrow_value(f.type, row[f.name]) for f in schema} for row in rows]
    table = pa.Table.from_pylist(converted, schema=schema)
    sink = pa.BufferOutputStream()
    with ipc.new_stream(sink, schema) as writer:
        writer.write_table(table)
    value: bytes = sink.getvalue().to_pybytes()
    return value
