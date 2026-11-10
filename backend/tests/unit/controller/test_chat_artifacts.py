import json

import pytest
from pydantic_ai import ModelRetry

from app.adapter.chat.artifacts import ChatRun
from app.domain.transport import NetworkMode, Season
from app.usecase.chat_artifacts import ChatColumn, ChatTable
from app.usecase.dto.chat import ChatContext


def test_chart_reuses_table_values_and_rejects_unknown_columns() -> None:
    run = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    table = ChatTable(
        "", "regions", (ChatColumn("name"), ChatColumn("hansen", "number")),
        ({"id": "one", "name": "One", "hansen": 2.5},), 1, False, "/api/v1/regions",
    )
    stored = json.loads(run.table(table))
    run.chart(stored["id"], "name", "hansen")
    assert [event.type for event in run.pending] == ["table", "chart"]
    assert run.pending[0].table is not None
    assert run.pending[0].table.rows == table.rows
    assert run.pending[1].chart is not None
    assert run.pending[1].chart.table_id == stored["id"]
    with pytest.raises(ModelRetry):
        run.chart(stored["id"], "name", "invented")
    with pytest.raises(ModelRetry):
        run.chart("unknown", "name", "hansen")
    with pytest.raises(ModelRetry):
        run.chart(stored["id"], "name", "name")
    assert len(run.pending) == 2


def test_tables_are_isolated_between_turns() -> None:
    first = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    second = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    first.table(ChatTable("", "regions", (), (), 0, False, "/api/v1/regions"))
    assert not second.tables
    with pytest.raises(ModelRetry):
        first.chart("table_1", "name", "hansen")
