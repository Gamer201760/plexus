import json
from dataclasses import asdict, dataclass, field, replace

from pydantic_ai import ModelRetry

from app.usecase.chat import ChatContext, ChatEvent
from app.usecase.chat_artifacts import ChatChart, ChatTable


@dataclass
class ChatRun:
    context: ChatContext
    tables: dict[str, ChatTable] = field(default_factory=dict)
    pending: list[ChatEvent] = field(default_factory=list)

    def table(self, table: ChatTable) -> str:
        stored = replace(table, id=f"table_{len(self.tables) + 1}")
        self.tables[stored.id] = stored
        self.pending.append(ChatEvent("table", table=stored))
        return json.dumps(asdict(stored), ensure_ascii=False)

    def chart(self, table_id: str, x: str, y: str) -> str:
        table = self.tables.get(table_id)
        if table is None:
            raise ModelRetry("Unknown table_id; load a table first")
        columns = {column.key: column for column in table.columns}
        if x not in columns or y not in columns or columns[y].format == "text":
            raise ModelRetry("Chart must use existing x and numeric y columns")
        if not any(isinstance(row.get(y), (int, float)) for row in table.rows):
            raise ModelRetry("No numeric values to chart")
        self.pending.append(ChatEvent("chart", chart=ChatChart(table_id, x, y)))
        return "Chart displayed from the stored table; do not repeat the full table in prose."
