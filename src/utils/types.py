from dataclasses import dataclass
from typing import Any, Dict
from numba import types
import numpy as np
import numba as nb

# 타입 힌트를 위한 정의
TimelineData = Dict[str, Any]

class TypeConverter:

    @staticmethod
    def convert_python_dict(numba_dict: nb.typed.Dict) -> dict:
        """
        nb.typed.Dict를 일반 Python dict로 변환합니다.
        """
        return {k: np.asarray(v, dtype=np.float16) for k, v in numba_dict.items()}

    @staticmethod
    def convert_numba_dict(python_dict: dict) -> nb.typed.Dict:
        """
        nb.typed.Dict를 일반 Python dict로 변환합니다.
        """
        # Numba typed Dict 생성
        numba_dict = nb.typed.Dict.empty(
            key_type=types.int32,
            value_type=types.float32[:],
        )

        try:
            # 기존 딕셔너리의 각 항목을 Numba typed Dict에 추가
            for key, value in python_dict.items():
                # 1. 기존 배열 재사용 가능하면 재사용
                numba_dict[np.int32(key)] = np.asarray(value, dtype=np.float32)
        except (ValueError, TypeError):
            raise ValueError(f"key는 정수, value는 실수여야 합니다: key: {type(key)}, value: {type(value)}")
        
        return numba_dict