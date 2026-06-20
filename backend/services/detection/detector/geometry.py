def point_in_polygon(
    px: float, py: float,
    polygon: list[tuple[float, float]],
) -> bool:
    n = len(polygon)
    inside = False
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        if ((y1 > py) != (y2 > py)) and (px < (x2 - x1) * (py - y1) / (y2 - y1) + x1):
            inside = not inside
    return inside


def filter_detections_by_roi(
    detections: list,
    roi_polygon: list[tuple[float, float]] | None,
    frame_width: int,
    frame_height: int,
):
    if not roi_polygon:
        return detections
    return [
        d for d in detections
        if d.bbox and point_in_polygon(
            d.bbox.center[0] / frame_width,
            d.bbox.center[1] / frame_height,
            roi_polygon,
        )
    ]
