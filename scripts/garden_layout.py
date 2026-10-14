"""Shared planting grid used by the renderer and request processor."""
ROWS = "ABCDEF"
COLUMNS = tuple(range(1, 9))
PLOTS = tuple(f"{row}{col}" for row in ROWS for col in COLUMNS)
CAPACITY = len(PLOTS)
