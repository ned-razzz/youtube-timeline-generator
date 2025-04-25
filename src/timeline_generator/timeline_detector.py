from typing import Any, Dict, Generator, List, Tuple, Set

import numpy as np
from numba import typed

from src.timeline_generator.read_audio import AudioChunk
from src.fingerprint_manager.fingerprint_generator import FingerprintGenerator
from src.timeline_generator.similarity_processor import compute_similarity_numpy, compute_time_offsets
from src.timeline_generator.types import DetectionResult, TimelineDataType, convert_to_numba_dict
from src.utils.memory_manager import monitor_system_memory

# 상수 정의
DEFAULT_SIMILARITY_THRESHOLD = 0.01
DUPLICATE_TIME_THRESHOLD = 5.0  # 중복 감지 시간 임계값 (초)

def print_detection_result(song_name: str, similarity: float, start_time: float) -> None:
    """감지 결과를 출력합니다."""
    print("============================")
    print(f"발견: {song_name} (유사도: {similarity:.4f}), 시작 시간: {start_time}")
    print("============================")

def detect_best_match(
    audio_fingerprint: typed.Dict, 
    song_fingerprints: Dict[str, typed.Dict]
) -> DetectionResult:
    """
    노래 목록 중에서 가장 유사도가 높은 노래를 감지합니다.
    
    Args:
        audio_fingerprint: 감지할 오디오의 지문
        compare_fingerprints: 비교할 노래 지문들의 사전
        
    Returns:
        DetectionResult: 가장 유사한 노래의 감지 결과
    """
    best_result = DetectionResult(
        similarity=0.0,
        song_name="",
        offset=0.0
    )

    # 각 노래 지문을 순회하면서 지문 유사도 비교
    for name, song_fingerprint in song_fingerprints.items():
        time_offsets = compute_time_offsets(audio_fingerprint, song_fingerprint)
        numpy_offsets = np.array(time_offsets)

        # 가장 많이 발생하는 시간 오프셋 찾기 (일치하는 부분이 있다면)
        similarity, offset = compute_similarity_numpy(numpy_offsets, 
                                                      len(audio_fingerprint),
                                                      len(song_fingerprint))
        print("\033[K", end="\r")
        print(f"{name}: {similarity}, {offset}", end="\r")

        if similarity > best_result.similarity:
            best_result.similarity = similarity
            best_result.song_name = name
            best_result.offset = offset
    print("\033[K", end="\r")
    print()
        
    return best_result

def detect_timeline(
        audio_chunks: Generator[AudioChunk, Any, None], 
        song_fingerprints: Dict[str, typed.Dict],
        chunk_size: int,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD
) -> Generator[TimelineDataType, None, None]:
    """
    오디오 청크에서 노래를 감지하고 타임라인을 생성합니다.
    
    Args:
        audio_chunks: 오디오 청크 제너레이터
        detect_fingerprints: 감지할 노래의 지문 사전 {노래이름: 지문}
        chunk_size: 오디오 청크의 크기 (초)
        similarity_threshold: 유사도 임계값 (기본값: 0.15)
        
    Yields:
        타임라인 데이터 사전
    """
    fingerprint_generator = FingerprintGenerator()
    
    for chunk in audio_chunks:
        # 현재 윈도우의 지문 생성
        chunk_fingerprint = fingerprint_generator.get_spectrogram_fingerprint(
            chunk.audio, chunk.samplerate
        )

        # 노래 목록 중 최고 유사도 노래 감지
        detection_result = detect_best_match(
            chunk_fingerprint, 
            song_fingerprints
        )
        print(f"유사도: {detection_result.similarity:.4f}, {detection_result.offset} ({detection_result.song_name})")
        monitor_system_memory()
        
        # 예상 시작 시간 계산
        audio_start_time = chunk.start_time - detection_result.offset
        if audio_start_time < 0:
            continue

        # 유사도가 임계값을 넘는 경우만 결과에 추가
        if detection_result.similarity < similarity_threshold:
            continue
        
        print_detection_result(detection_result.song_name, detection_result.similarity, audio_start_time)
        # 값 저장
        timeline = {
            "song_name": detection_result.song_name,
            "similarity": detection_result.similarity,
            "estimated_start_time": audio_start_time,
        }
        yield timeline

def is_duplicate_detection(
    seen_songs: Set[str], 
    song_name: str, 
) -> bool:
    """
    현재 감지된 노래가 이미 감지된 노래와 중복되는지 확인합니다.
    """
    for seen_name in seen_songs:
        if song_name == seen_name:
            return True
    return False

def analyze_timeline(timelines: List[TimelineDataType]) -> List[TimelineDataType]:
    """
    감지된 타임라인을 분석하여 중복을 제거하고 시간순으로 정렬합니다.
    """
    # 유사도 높은 순으로 정렬
    # sorted_timelines = sorted(timelines, key=lambda x: x["similarity"], reverse=True)
    timelines.sort(key=lambda x: x["estimated_start_time"])

    # 중복 제거 (같은 노래가 여러 윈도우에서 발견될 수 있음)
    filtered_timelines = []
    seen_songs = set()
    
    for timeline_data in timelines:
        song_name = timeline_data["song_name"]
        start_time = timeline_data["estimated_start_time"]
        
        # 이미 
        if is_duplicate_detection(seen_songs, song_name):
            continue
        
        filtered_timelines.append(timeline_data)
        seen_songs.add(song_name)
    
    # 시작 시간 순으로 정렬
    filtered_timelines.sort(key=lambda x: x["estimated_start_time"])
    
    return filtered_timelines