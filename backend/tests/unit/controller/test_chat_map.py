import pytest
from tests.unit.usecase.test_atlas_usecases import FakeAtlas

from app.usecase.chat_map import ChatMap
from app.usecase.regions import RegionQueries


def test_focus_validates_and_deduplicates_real_region_ids() -> None:
    commands = ChatMap(RegionQueries(FakeAtlas()))
    command = commands.command("focus", ["R1", "R1"])
    assert command.region_ids == ("R1",)
    with pytest.raises(ValueError):
        commands.command("focus", ["invented"])
    with pytest.raises(ValueError):
        commands.command("focus", [])
    with pytest.raises(ValueError):
        commands.command("reset", ["R1"])
    assert commands.command("reset", []).region_ids == ()
    assert commands.command("zoom_in", []).action == "zoom_in"
