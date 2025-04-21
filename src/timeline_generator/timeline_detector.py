from typing import Any, Dict, Generator, List, Tuple, Set

from src.timeline_generator.read_audio import AudioChunk
from src.fingerprint_manager.fingerprint_generator import FingerprintGenerator
from src.timeline_generator.similarity_processor import compute_similarity, compute_time_offsets
from src.timeline_generator.types import DetectionResult, FingerprintType, TimelineDataType

# 상수 정의
DEFAULT_SIMILARITY_THRESHOLD = 0.15
DUPLICATE_TIME_THRESHOLD = 5.0  # 중복 감지 시간 임계값 (초)

def print_detection_result(song_name: str, similarity: float, start_time: float) -> None:
    """감지 결과를 출력합니다."""
    print("============================")
    print(f"발견: {song_name} (유사도: {similarity:.4f}), 시작 시간: {start_time}")
    print("============================")

def detect_best_match(
    audio_fingerprint: FingerprintType, 
    compare_fingerprints: Dict[str, FingerprintType]
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
    for name, compare_fingerprint in compare_fingerprints.items():
        time_offsets = compute_time_offsets(audio_fingerprint, compare_fingerprint)

        # 가장 많이 발생하는 시간 오프셋 찾기 (일치하는 부분이 있다면)
        if time_offsets:
            similarity, offset = compute_similarity(time_offsets, audio_fingerprint, compare_fingerprint)
            print(f"\r{name}: {similarity}, {offset}", end="")
            if similarity > best_result.similarity:
                best_result.similarity = similarity
                best_result.song_name = name
                best_result.offset = offset
    print()
        
    best_result.similarity = best_result.similarity*10
    return best_result

def is_duplicate_detection(
    seen_songs: Set[Tuple[str, float]], 
    song_name: str, 
    start_time: float
) -> bool:
    """
    현재 감지된 노래가 이미 감지된 노래와 중복되는지 확인합니다.
    
    Args:
        seen_songs: 이미 감지된 노래와 시작 시간 집합
        song_name: 현재 노래 이름
        start_time: 현재 노래 시작 시간
        
    Returns:
        bool: 중복되면 True, 아니면 False
    """
    for seen_song, seen_time in seen_songs:
        if song_name == seen_song and abs(start_time - seen_time) < DUPLICATE_TIME_THRESHOLD:
            return True
    return False

def detect_timeline(
        audio_chunks: Generator[AudioChunk, Any, None], 
        detect_fingerprints: Dict[str, FingerprintType],
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
        chunk_fingerprint_data = fingerprint_generator.get_spectrogram_fingerprint(
            chunk.audio, chunk.samplerate
        )

        # 노래 목록 중 최고 유사도 노래 감지
        detection_result = detect_best_match(
            chunk_fingerprint_data['peak_pairs'], 
            detect_fingerprints
        )
        
        print(f"유사도: {detection_result.similarity:.4f}, {detection_result.offset} ({detection_result.song_name})")
        
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
            "window_start": chunk.start_time,
            "window_end": chunk.start_time + chunk_size,
            "song_name": detection_result.song_name,
            "similarity": detection_result.similarity,
            "estimated_start_time": audio_start_time,
        }
        yield timeline

def analyze_timeline(timelines: List[TimelineDataType]) -> List[TimelineDataType]:
    """
    감지된 타임라인을 분석하여 중복을 제거하고 시간순으로 정렬합니다.
    
    Args:
        timelines: 감지된 타임라인 목록
        
    Returns:
        List[TimelineDataType]: 중복이 제거되고 정렬된 타임라인 목록
    """
    # 유사도 높은 순으로 정렬
    sorted_timelines = sorted(timelines, key=lambda x: x["similarity"], reverse=True)

    # 중복 제거 (같은 노래가 여러 윈도우에서 발견될 수 있음)
    filtered_timelines = []
    seen_songs = set()
    
    for timeline_data in sorted_timelines:
        song_name = timeline_data["song_name"]
        start_time = timeline_data["estimated_start_time"]
        
        # 이미 처리한 노래와 시작 시간이 가까운 경우 건너뛰기
        if is_duplicate_detection(seen_songs, song_name, start_time):
            continue
        
        filtered_timelines.append(timeline_data)
        seen_songs.add((song_name, start_time))
    
    # 시작 시간 순으로 정렬
    filtered_timelines.sort(key=lambda x: x["estimated_start_time"])
    
    return filtered_timelines