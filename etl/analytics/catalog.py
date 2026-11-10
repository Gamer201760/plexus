import re

KEYS = {
    "np_city_times": ["season", "point_id", "city"],
    "stg_settlements": ["region", "oktmo"],
    "stg_intercity": ["region_from", "city_from"],
    "idx_np": ["region", "season", "point_id"],
    "nodes": ["node"],
    "ways": ["way_idx"],
    "edges": ["way_idx", "src", "dst"],
    "points": ["region", "point_id"],
}


def identifier(value: str) -> str:
    if not re.fullmatch("[a-zA-Z_][a-zA-Z0-9_]*", value):
        raise ValueError(f"Unsupported identifier: {value}")
    return '"' + value + '"'


def column_type(value: str) -> str:
    types = {
        "VARCHAR": "String",
        "BIGINT": "Int64",
        "INTEGER": "Int32",
        "SMALLINT": "Int16",
        "TINYINT": "Int8",
        "UBIGINT": "UInt64",
        "UINTEGER": "UInt32",
        "USMALLINT": "UInt16",
        "UTINYINT": "UInt8",
        "FLOAT": "Float32",
        "DOUBLE": "Float64",
        "BOOLEAN": "Bool",
        "DATE": "String",
        "TIMESTAMP": "DateTime64(6, 'UTC')",
        "HUGEINT": "Int128",
    }
    if value.endswith("[]"):
        return "Nullable(String)"
    if value in types:
        return "Nullable(" + types[value] + ")"
    if re.fullmatch(r"DECIMAL\(\d+,\d+\)", value):
        return "Nullable(" + value.title() + ")"
    raise ValueError(f"Unsupported source type: {value}")


def table_ddl(table: str, name: str, columns: list[tuple]) -> str:
    names = [row[0] for row in columns]
    keys = [
        key
        for key in KEYS.get(name, ["region_id", "region", "point_id", "inn"])
        if key in names
    ]
    order = ",".join(identifier(key) for key in keys) or "tuple()"
    fields = ",".join(identifier(row[0]) + " " + column_type(row[1]) for row in columns)
    return f"CREATE TABLE {table} ({fields}) ENGINE=MergeTree ORDER BY ({order}) SETTINGS allow_nullable_key=1"
