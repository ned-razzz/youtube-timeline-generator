from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
from numba import typed, types
import numpy as np
import numba as nb

# 타입 힌트를 위한 정의
# FingerprintType = Dict[Tuple[int, int], List[float]]
TimelineDataType = Dict[str, Any]

@dataclass
class DetectionResult:
    """노래 감지 결과를 저장하는 데이터 클래스"""
    similarity: float
    song_name: str
    offset: float

def convert_to_python_dict(numba_dict: typed.Dict):
    """
    numba.typed.Dict를 일반 Python dict로 변환합니다.
    
    Args:
        typed_dict: numba.typed.Dict 객체
        
    Returns:
        일반 Python dict
    """
    return {k: v for k, v in numba_dict.items()}

def convert_to_numba_dict(python_dict: dict) -> typed.Dict:
    """
    numba.typed.Dict를 일반 Python dict로 변환합니다.
    
    Args:
        typed_dict: numba.typed.Dict 객체
        
    Returns:
        일반 Python dict
    """
    # Numba typed Dict 생성
    numba_dict = typed.Dict.empty(
        key_type=types.UniTuple(types.int64, 2),
        value_type=types.float64[:],
    )
    
    # 기존 딕셔너리의 각 항목을 Numba typed Dict에 추가
    for key, value in python_dict.items():
        # 키가 정확히 2개의 정수로 구성된 튜플인지 확인
        if not isinstance(key, tuple) or len(key) != 2:
            raise ValueError(f"키는 2개 정수로 구성된 튜플이어야 합니다. 받은 키: {key}")
        
        # 정수 튜플로 변환 (int64 타입으로)
        numba_key = (np.int64(key[0]), np.int64(key[1]))
        
        # 시간 포인트를 NumPy 배열로 변환 (float64 타입으로)
        numba_value = np.array(value, dtype=np.float64)
        
        # Numba 딕셔너리에 추가
        numba_dict[numba_key] = numba_value
    
    return numba_dict