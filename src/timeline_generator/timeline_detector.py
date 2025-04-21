
from typing import Any, Generator
import numpy as np
from collections import Counter

from src.timeline_generator.read_audio import AudioChunk

from src.fingerprint_manager.fingerprint_generator import get_spectrogram_fingerprint

def detect_timeline(
        audio_chunks: Generator[AudioChunk, Any, None], 
        detect_fingerprints,
        chunk_size,
        similarity_threshold=0.15):
    
    for chunk in audio_chunks:
        # 현재 윈도우의 지문 생성
        chunk_fingerprint = get_spectrogram_fingerprint(chunk.audio, chunk.samplerate)
        
        # 노래 목록 중 최고 유사도 노래 감지
        best_similarity, best_song_name, best_offset = _detect_songs(chunk_fingerprint, detect_fingerprints)
        
        # 유사도가 임계값을 넘는 경우만 결과에 추가
        if best_similarity < similarity_threshold:
            continue

        # 예상 시작 시간 계산
        audio_start_time = chunk.start_time - best_offset
        if audio_start_time < 0:
            continue
        
        # 값 저장
        timeline = {
            "window_start": chunk.start_time,
            "window_end": chunk.start_time + chunk_size,
            "song_name": best_song_name,
            "similarity": best_similarity,
            "estimated_start_time": audio_start_time,
        }

        print("============================")
        print(f"발견: {best_song_name} (유사도: {best_similarity:.4f}), 시작 시간: {audio_start_time}")
        print("============================")
        yield timeline

def _detect_songs(chunk_fingerprint, compare_fingerprints):
    """
    노래 목록 중에서 가장 유사도가 높은 노래를 감지.
    감지 데이터 반환.
    """
    best_similarity = 0.0
    best_song_name = None
    best_offset = 0.0
    
    # 각 노래 지문을 순회하면서 지문 유사도 비교
    for song_name, detect_fingerprint in compare_fingerprints.items():
        similarity, offset = _compute_simularity(chunk_fingerprint, detect_fingerprint)
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_song_name = song_name
            best_offset = offset
    return best_similarity, best_song_name, best_offset

def _compute_simularity(fingerprint1, fingerprint2):
    """
    두 오디오 지문 간의 유사도 계산 및 오프셋 반환
    """
    # 해시 테이블로부터 일치하는 피크 쌍 찾기
    matches = []
    
    # 각 해시 키에 대해 시간 오프셋 계산
    time_offsets = []
    
    for hash_key, time_points1 in fingerprint1["peak_pairs"].items():
        if hash_key in fingerprint2["peak_pairs"]:
            time_points2 = fingerprint2["peak_pairs"][hash_key]
            
            # 모든 가능한 시간 오프셋 계산
            for t1 in time_points1:
                for t2 in time_points2:
                    # 시간 오프셋 = 두 번째 오디오에서의 시간 - 첫 번째 오디오에서의 시간
                    time_offset = t2 - t1
                    time_offsets.append(round(time_offset, 2))  # 반올림하여 비슷한 오프셋 그룹화
                    matches.append((hash_key, t1, t2))
    
    # 가장 많이 발생하는 시간 오프셋 찾기 (일치하는 부분이 있다면)
    if not time_offsets:
        return 0.0, 0.0
    
    offset_counts = Counter(time_offsets)
    most_common_offset, most_common_count = offset_counts.most_common(1)[0]
    
    # 가장 많이 발생한 오프셋의 비율 계산
    total_hash_count = min(len(fingerprint1["peak_pairs"]), len(fingerprint2["peak_pairs"]))
    
    # 유사도 점수 계산 (정규화된 매치 수)
    similarity = most_common_count / (total_hash_count * 0.5)  # 50% 이상 매치되면 1.0으로 포화
    similarity = min(similarity, 1.0)  # 1.0을 초과하지 않도록
    
    return similarity, most_common_offset

def analyze_timeline(timelines):
    # 유사도 높은 순으로 정렬
    sorted_timelines = sorted(timelines, key=lambda x: x["similarity"], reverse=True)

    # 중복 제거 (같은 노래가 여러 윈도우에서 발견될 수 있음)
    filtered_timelines = []
    seen_songs = set()
    for timeline_data in sorted_timelines:
        song_name = timeline_data["song_name"]
        start_time = timeline_data["estimated_start_time"]
        
        # 이미 처리한 노래와 시작 시간이 가까운 경우 (5초 이내) 건너뛰기
        skip = False
        for seen_song, seen_time in seen_songs:
            if song_name == seen_song and abs(start_time - seen_time) < 5.0:
                skip = True
                break
        
        if not skip:
            filtered_timelines.append(timeline_data)
            seen_songs.add((song_name, start_time))
    
    # 시작 시간 순으로 정렬
    filtered_timelines.sort(key=lambda x: x["estimated_start_time"])
    
    return filtered_timelines