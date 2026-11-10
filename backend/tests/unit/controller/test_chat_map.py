import pytest

from app.repository.files.atlas import JsonAtlasRepository
from app.settings import DEFAULT_DATA_DIR
from app.usecase.chat_map import ChatMap
from app.usecase.regions import RegionQueries


def test_focus_validates_and_deduplicates_real_region_ids() -> None:
    commands = ChatMap(RegionQueries(JsonAtlasRepository(DEFAULT_DATA_DIR)))
    command = commands.command("focus", ["07000000", "07000000"])
    assert command.region_ids == ("07000000",)
    with pytest.raises(ValueError):
        commands.command("focus", ["invented"])
    with pytest.raises(ValueError):
        commands.command("focus", [])
    with pytest.raises(ValueError):
        commands.command("reset", ["07000000"])
    assert commands.command("reset", []).region_ids == ()
    assert commands.command("zoom_in", []).action == "zoom_in"
