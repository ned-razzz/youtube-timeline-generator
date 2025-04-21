from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

# 타입 힌트를 위한 정의
FingerprintType = Dict[Tuple[int, int], List[float]]
TimelineDataType = Dict[str, Any]

@dataclass
class DetectionResult:
    """노래 감지 결과를 저장하는 데이터 클래스"""
    similarity: float
    song_name: str
    offset: float