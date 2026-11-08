from collections.abc import Mapping


def operating_season(tags: Mapping[str, str]) -> str:
    if tags.get("ice_road") == "yes" or tags.get("winter_road") == "yes":
        return "winter"
    season = tags.get("seasonal", "no").lower()
    if season in {"winter", "summer"}:
        return season
    if season not in {"no", "false", "0"}:
        return "unknown"
    if tags.get("route") == "ferry":
        return "unknown"
    return "all"
