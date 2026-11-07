import pytest

from app.domain.projection import CANVAS_CENTER, SvgFrame, lambert, path_bbox


def test_lambert_origin_lies_on_central_meridian_at_origin_latitude() -> None:
    x, y = lambert(100.0, 60.0)

    assert x == pytest.approx(0.0, abs=1e-12)
    assert y == pytest.approx(0.0, abs=1e-12)


def test_negative_longitude_wraps_east_of_antimeridian() -> None:
    assert lambert(-170.0, 66.0) == lambert(190.0, 66.0)


def test_frame_centres_its_bounds_on_canvas() -> None:
    frame = SvgFrame.enclosing([lambert(30.0, 45.0), lambert(170.0, 75.0)])
    middle = (
        (frame.min_x + frame.max_x) / 2,
        (frame.min_y + frame.max_y) / 2,
    )

    assert frame.scale > 0
    assert frame.place(100.0, 60.0)[0] == pytest.approx(
        CANVAS_CENTER[0] + (0 - middle[0]) * frame.scale, abs=0.06
    )


def test_frame_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        SvgFrame.enclosing([])


def test_path_bbox_spans_all_rings() -> None:
    assert path_bbox("M10,20L30,25L15,40ZM5,22L6,23Z") == (5.0, 20.0, 25.0, 20.0)
    assert path_bbox("") is None
