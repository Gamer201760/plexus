from app.domain.projection import SvgFrame
from app.domain.transport import Confidence, Mode, Season
from app.repository.files.json_values import JsonObject, integer, number, text
from app.usecase.dto import (
    EconomyRecord,
    IndexRecord,
    LinkRecord,
    PointRecord,
    RegionRecord,
    SettlementName,
    SettlementRecord,
    SourceRecord,
    WinterRoadRecord,
)


def _choice[E: (Mode, Season, Confidence)](kind: type[E], raw: str | None) -> E | None:
    if raw is None:
        return None
    try:
        return kind(raw)
    except ValueError:
        return None


def region_record(row: JsonObject) -> RegionRecord | None:
    region_id, name = text(row, "id"), text(row, "name")
    if region_id is None or name is None:
        return None
    return RegionRecord(
        id=region_id,
        name=name,
        settlements=integer(row, "settlements") or 0,
        population=integer(row, "population") or 0,
    )


def point_record(row: JsonObject, frame: SvgFrame) -> PointRecord | None:
    point_id, lat, lon = text(row, "id"), number(row, "lat"), number(row, "lon")
    if point_id is None or lat is None or lon is None:
        return None
    x, y = frame.place(lon, lat)
    return PointRecord(
        id=point_id,
        name=text(row, "name") or point_id,
        region_id=text(row, "region") or "",
        lat=lat,
        lon=lon,
        x=x,
        y=y,
    )


def link_record(row: JsonObject) -> LinkRecord | None:
    link_id, mode = text(row, "id"), _choice(Mode, text(row, "mode"))
    if link_id is None or mode is None:
        return None
    from_id, to_id = text(row, "from_id") or "", text(row, "to_id") or ""
    return LinkRecord(
        id=link_id,
        region_id=text(row, "region") or "",
        mode=mode,
        season=_choice(Season, text(row, "season")),
        from_id=from_id,
        from_name=text(row, "from_name") or from_id,
        to_id=to_id,
        to_name=text(row, "to_name") or to_id,
        km=number(row, "km"),
        freq_per_week=number(row, "freq_per_week"),
        freq_note=text(row, "freq_note"),
        vehicle=text(row, "vehicle"),
        confidence=_choice(Confidence, text(row, "confidence")),
        source_url=text(row, "source_url"),
        source_date=text(row, "source_date"),
    )


def economy_record(row: JsonObject) -> EconomyRecord | None:
    region_id = text(row, "region_id")
    if region_id is None:
        return None
    return EconomyRecord(
        region_id=region_id,
        company_rows=integer(row, "company_rows"),
        strict_rows=integer(row, "strict_rows"),
        strict_revenue_rub=number(row, "strict_revenue_rub"),
        fns_matched_rows=integer(row, "fns_matched_rows"),
    )


def settlement_record(row: JsonObject, frame: SvgFrame) -> SettlementRecord | None:
    settlement_id, name = text(row, "point_id"), text(row, "name")
    if settlement_id is None or name is None:
        return None
    lat, lon = number(row, "lat"), number(row, "lon")
    x, y = frame.place(lon, lat) if lat is not None and lon is not None else (None, None)
    return SettlementRecord(
        id=settlement_id,
        name=name,
        region_id=text(row, "region_id") or "",
        population=integer(row, "population"),
        x=x,
        y=y,
        companies=integer(row, "company_rows"),
        revenue_rub=number(row, "revenue_rub"),
    )


def settlement_name(row: JsonObject) -> SettlementName | None:
    settlement_id, name = text(row, "point_id"), text(row, "name")
    if settlement_id is None or name is None:
        return None
    return SettlementName(
        id=settlement_id,
        name=name,
        region_id=text(row, "region_id") or "",
        population=integer(row, "population"),
    )


def winter_road_record(row: JsonObject) -> WinterRoadRecord:
    return WinterRoadRecord(
        district=text(row, "district"),
        route=text(row, "route"),
        road_km=number(row, "road_km"),
        opening_date=text(row, "opening_date"),
        closure_date=text(row, "closure_date"),
        weight_limit_tonnes=number(row, "weight_limit_tonnes"),
        season_end_year=integer(row, "season_end_year"),
        report_date=text(row, "report_date"),
        source_file=text(row, "source_file"),
    )


def source_record(row: JsonObject) -> SourceRecord | None:
    source_id, title = text(row, "id"), text(row, "title")
    if source_id is None or title is None:
        return None
    return SourceRecord(
        id=source_id,
        title=title,
        period=text(row, "period"),
        url=text(row, "url"),
        note=text(row, "note"),
        rows=integer(row, "rows"),
    )


def index_record(row: JsonObject) -> IndexRecord | None:
    region_id, scenario = text(row, "region_id"), text(row, "season")
    if region_id is None or scenario is None:
        return None
    return IndexRecord(
        region_id=region_id,
        scenario=scenario,
        hansen=number(row, "hansen_idx"),
        covered_population=integer(row, "covered_population"),
        total_population=integer(row, "population"),
        covered_settlements=integer(row, "covered_settlements"),
        total_settlements=integer(row, "n_np"),
        model_version=text(row, "model_version"),
        artifact_version=text(row, "artifact_version"),
    )
