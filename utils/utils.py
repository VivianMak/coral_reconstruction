from dataclasses import dataclass

@dataclass
class Point:
    idx: int        # Point index, consistent across frames
    x: float
    y: float
    z: float
    pos_history: list[float]
