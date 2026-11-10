import json
import types
from dataclasses import asdict, fields
from enum import Enum
from typing import TypeAliasType, get_args, get_origin, get_type_hints

import pyarrow.ipc as ipc
from app.repository.clickhouse.arrow_rows import arrow_body

from client import ClickHouse


def sql_type(annotation: object) -> str:
    if isinstance(annotation, TypeAliasType):
        return sql_type(annotation.__value__)
    origin, args = get_origin(annotation), get_args(annotation)
    if origin is types.UnionType:
        return 'Nullable(' + sql_type(next(a for a in args if a is not type(None))) + ')'
    if origin is list:
        return 'Array(' + sql_type(args[0]) + ')'
    if origin is tuple:
        return 'Tuple(' + ','.join(sql_type(a) for a in args) + ')'
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return 'String'
    return {str: 'String', int: 'Int64', float: 'Float64', bool: 'Bool'}[annotation]


def write_records(client: ClickHouse, name: str, kind: type, records: list, order: str,
                  extra: dict[str, str] | None = None) -> dict:
    hints = get_type_hints(kind)
    columns = [(f.name, sql_type(hints[f.name])) for f in fields(kind)]
    target = 'plexus_atlas.' + name
    stage = target + '__loading'
    client.request(f'DROP TABLE IF EXISTS {stage}')
    definition = ','.join('`'+key+'` '+value for key,value in columns)
    extra_fields = ''.join(',' + key + ' ' + value for key,value in (extra or {}).items())
    client.request(f'CREATE TABLE {stage} ({definition}, ordinal UInt32{extra_fields}) ENGINE=MergeTree ORDER BY ({order}) SETTINGS allow_nullable_key=1,index_granularity=1024')
    schema=ipc.open_stream(client.request(f'SELECT * FROM {stage} LIMIT 0 FORMAT ArrowStream')).schema
    for first in range(0,len(records),5000):
        rows = [{**asdict(record),'ordinal':first+i} for i,record in enumerate(records[first:first+5000])]
        rows = json.loads(json.dumps(rows,ensure_ascii=False,default=lambda v:v.value))
        client.request(f'INSERT INTO {stage} FORMAT ArrowStream',arrow_body(schema,rows))
    count=int(client.rows(f'SELECT count() AS n FROM {stage}')[0]['n'])
    if count!=len(records):raise RuntimeError(f'Incomplete {name}')
    exists=client.rows(f'EXISTS TABLE {target}')[0]['result']
    if exists:
        client.request(f'EXCHANGE TABLES {target} AND {stage}')
        client.request(f'DROP TABLE {stage}')
    else:client.request(f'RENAME TABLE {stage} TO {target}')
    return {'table':target,'rows':count}
