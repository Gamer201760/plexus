from collections.abc import Mapping


HIGHWAYS = {
    "motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "road",
    "residential", "living_street", "track", "service",
    "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link",
}
LOCAL_SERVICE = {"parking_aisle", "driveway", "drive-through", "emergency_access"}


def include_way(tags: Mapping[str, str]) -> bool:
    highway = tags.get("highway")
    if highway not in HIGHWAYS and tags.get("route") != "ferry":
        return False
    if highway != "service":
        return True
    if tags.get("service") in LOCAL_SERVICE or tags.get("area") == "yes":
        return False
    access = next((tags[key] for key in ("motorcar", "motor_vehicle", "vehicle", "access") if key in tags), "yes")
    return access in {"yes", "permissive", "designated"} and not any(
        key in tags for key in ("motorcar:conditional", "motor_vehicle:conditional", "vehicle:conditional", "access:conditional")
    )
