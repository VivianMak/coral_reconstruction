from dataclasses import dataclass, field

@dataclass
class Point:
    idx: int        # Point index, consistent across frames
    x: float
    y: float
    z: float
    pos_history: list[tuple[float,float,float]]