"""Placeholder CV / satellite pipeline. Returns deterministic mock values per building id."""


def detect_cooling_tower(building_id: str) -> tuple[bool, float]:
    """
    Mock: pretend we ran vision on satellite tiles.
    Same building_id always yields the same result for demos.
    """
    h = abs(hash(building_id)) % (2**31)
    detected = (h % 5) != 0  # ~80% positive for sales narrative; adjust as needed
    confidence = 0.55 + (h % 45) / 100.0  # 0.55 .. 0.99
    return detected, round(confidence, 2)
