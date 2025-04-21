
from typing import List, Tuple
import numba as nb
from collections import Counter

import numpy as np

from src.timeline_generator.types import FingerprintType

TIME_OFFSET_PRECISION = 2  # 시간 오프셋 반올림 정밀도
SIMILARITY_NORMALIZATION_FACTOR = 0.5  # 유사도 정규화 요소

@nb.jit(forceobj=True)
def compute_time_offsets(
    fingerprint1: FingerprintType, 
    fingerprint2: FingerprintType
) -> List[float]:
    """
    두 오디오 지문 간의 시간 오프셋을 계산합니다.
    
    Args:
        fingerprint1: 첫 번째 오디오 지문
        fingerprint2: 두 번째 오디오 지문
        
    Returns:
        List[float]: 계산된 시간 오프셋 목록
    """
    time_offsets = []
    
    # 공통 해시 키에 대해 시간 오프셋 계산
    for hash_key, time_points1 in fingerprint1.items():
        if hash_key in fingerprint2:
            time_points2 = fingerprint2[hash_key]
            
            # 모든 가능한 시간 오프셋 계산
            for t1 in time_points1:
                for t2 in time_points2:
                    # 시간 오프셋 = 두 번째 오디오에서의 시간 - 첫 번째 오디오에서의 시간
                    time_offset = t2 - t1
                    time_offsets.append(round(time_offset, TIME_OFFSET_PRECISION))
    return time_offsets

def compute_similarity(
    time_offsets: List[float], 
    fingerprint1: FingerprintType, 
    fingerprint2: FingerprintType
) -> Tuple[float, float]:
    """
    시간 오프셋을 기반으로 유사도와 최빈 오프셋을 계산합니다.
    
    Args:
        time_offsets: 계산된 시간 오프셋 목록
        fingerprint1: 첫 번째 오디오 지문
        fingerprint2: 두 번째 오디오 지문
        
    Returns:
        Tuple[float, float]: (유사도, 최빈 오프셋)
    """
    offset_counts = Counter(time_offsets)
    most_common_offset, most_common_count = offset_counts.most_common(1)[0]
    
    # 가장 많이 발생한 오프셋의 비율 계산
    total_hash_count = min(len(fingerprint1), len(fingerprint2))
    
    # 유사도 점수 계산 (정규화된 매치 수)
    # SIMILARITY_NORMALIZATION_FACTOR = 0.5는 50% 이상 매치되면 1.0으로 포화시키기 위한 값
    similarity = most_common_count / (total_hash_count * SIMILARITY_NORMALIZATION_FACTOR)
    similarity = min(similarity, 1.0)  # 1.0을 초과하지 않도록

    return similarity, most_common_offset