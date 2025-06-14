from typing import Tuple
import numba as nb
import numpy as np
from numpy.typing import NDArray
from numba import typed, types

TIME_OFFSET_PRECISION = 2  # 시간 오프셋 반올림 정밀도
SIMILARITY_NORMALIZATION_FACTOR = 0.5  # 유사도 정규화 요소


@nb.njit(fastmath=True, cache=True)
def compute_time_offsets(
    fingerprint1: typed.Dict, fingerprint2: typed.Dict, precision=TIME_OFFSET_PRECISION
):
    """
    두 오디오 지문 간의 시간 오프셋을 계산합니다.

    Args:
        fingerprint1: 첫 번째 오디오 지문
        fingerprint2: 두 번째 오디오 지문

    Returns:
        List[float]: 계산된 시간 오프셋 목록
    """
    time_offsets = typed.List.empty_list(types.float64)

    for hash_key in fingerprint1:
        if hash_key in fingerprint2:
            time_points1 = fingerprint1[hash_key]
            time_points2 = fingerprint2[hash_key]

            for t1 in time_points1:
                for t2 in time_points2:
                    time_offset = t2 - t1
                    round_offset = np.round(time_offset, precision)
                    time_offsets.append(round_offset)
    return time_offsets


@nb.njit(fastmath=True, parallel=True)
def compute_similarity_numpy(
    time_offsets, fp1_length: int, fp2_length: int, normalization_factor: float = 0.5
) -> Tuple[float, float]:
    """NumPy를 사용한 고속 유사도 계산"""

    # 빈 입력 처리
    if not len(time_offsets):
        return 0.0, 0.0

    # 모든 값이 0인지 확인
    if np.all(time_offsets == 0):
        return 0.0, 0.0

    # 부동소수점 오프셋을 정수로 변환 (정밀도 유지)
    scale_factor = 1000  # 밀리초 단위 정밀도
    scaled_offsets = (time_offsets * scale_factor).astype(np.int64)

    # 5. 최대 발생 횟수와 해당 오프셋 찾기
    unique_counts = get_unique_counts(scaled_offsets)
    key, value = find_max_of_hash_table(unique_counts)

    most_common_count = value
    most_common_offset = key / scale_factor  # 원래 스케일로 변환

    # 6. 유사도 계산
    total_hash_count = min(fp1_length, fp2_length)
    similarity = most_common_count / (total_hash_count * normalization_factor)
    similarity = min(similarity, 1.0)  # 최대값 1.0으로 제한

    return similarity, most_common_offset


@nb.njit(fastmath=True, cache=True)
def get_unique_counts(arr: NDArray[np.int64]):
    """
    numba로 최적화된 np.unique(arr, return_counts=True) 대체 함수
    """
    value_counts = typed.Dict.empty(nb.types.int64, nb.types.int64)
    for index, value in np.ndenumerate(arr):
        if value in value_counts:
            value_counts[value] += 1
        else:
            value_counts[value] = 1
    return value_counts


@nb.njit(fastmath=True, cache=True)
def find_max_of_hash_table(hash_table):
    max_key = None
    max_value = 0

    for k in hash_table.keys():
        v = hash_table[k]
        if v > max_value:
            max_value = v
            max_key = k

    if max_key is None:
        return 0, 0
    else:
        return max_key, max_value


def compute_similarity(
    time_offsets: np.ndarray,
    fp1_length: int,
    fp2_length: int,
    normalization_factor: float = 0.5,
) -> Tuple[float, float]:
    """NumPy를 사용한 고속 유사도 계산"""

    # 1. 빈 입력 처리
    if not len(time_offsets):
        return 0.0, 0.0

    # 3. 부동소수점 오프셋을 정수로 변환 (정밀도 유지)
    scale_factor = 1000  # 밀리초 단위 정밀도
    scaled_offsets = np.round(time_offsets * scale_factor).astype(np.int64)

    # 4. NumPy의 고유값 카운팅 기능 사용
    unique_vals, counts = np.unique(scaled_offsets, return_counts=True)

    # 5. 최대 발생 횟수와 해당 오프셋 찾기
    max_idx = np.argmax(counts)
    most_common_count = counts[max_idx]
    most_common_offset = unique_vals[max_idx] / scale_factor  # 원래 스케일로 변환

    # 6. 유사도 계산
    total_hash_count = min(fp1_length, fp2_length)
    similarity = most_common_count / (total_hash_count * normalization_factor)
    similarity = min(similarity, 1.0)  # 최대값 1.0으로 제한

    return similarity, most_common_offset
