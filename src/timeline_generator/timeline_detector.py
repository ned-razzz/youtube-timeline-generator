
import numpy as np
from collections import Counter

from ..fingerprint_manager.fingerprint_generator import get_spectrogram_fingerprint

def detect_timeline(
        long_audio, 
        detect_fingerprints, 
        window_size=15.0, 
        hop_size=5.0, 
        sample_rate=44100, 
        similarity_threshold=0.15):
    # 긴 오디오의 총 길이 (초)
    total_duration = len(long_audio) / float(sample_rate)
    
    # hip_size만큼 각 윈도우 분리 
    window_iter = np.arange(0, total_duration - window_size, hop_size)
    window_count = len(window_iter)
    
    # 작업 정보 출력
    print(f"긴 오디오 길이: {total_duration:.2f}초")
    print(f"윈도우 크기: {window_size:.2f}초, 홉 크기: {hop_size:.2f}초")
    print(f"총 {window_count}개 윈도우 검사")

    # 오디오 탐지 작업 개시
    timelines = []
    for i, start_time in enumerate(window_iter):
        # 진행상황 표시
        print()
        print(f"\r윈도우 검사 중: {i+1}/{window_count} ({(i+1)/window_count*100:.1f}%)")

        # 현재 윈도우에 해당하는 오디오 세그먼트 추출
        start_index = int(start_time * sample_rate)
        end_index = int((start_time + window_size) * sample_rate)
        window_audio = long_audio[start_index:end_index]
        
        # 현재 윈도우의 지문 생성
        window_fingerprint = get_spectrogram_fingerprint(window_audio)
        
        # 노래 목록 중 최고 유사도 노래 감지
        best_similarity, best_song_name, best_offset = _detect_songs(window_fingerprint, detect_fingerprints)
        
        # 유사도가 임계값을 넘는 경우만 결과에 추가
        if best_similarity < similarity_threshold:
            continue

        # 예상 시작 시간 계산 (윈도우 시작 시간 - 오프셋)
        song_start_time = start_time - best_offset
        
        # 유효한 시작 시간만 기록 (음수가 아닌 경우)
        if song_start_time < 0:
            continue
        
        # 값 저장
        timelines.append({
            "window_start": start_time,
            "window_end": start_time + window_size,
            "song_name": best_song_name,
            "similarity": best_similarity,
            "estimated_start_time": song_start_time,
        })

        print("============================")
        print(f"발견: {best_song_name} (유사도: {best_similarity:.4f}), 시작 시간: {song_start_time}")
        print("============================")

    return _analyze_timeline(timelines)

def _detect_songs(window_fingerprint, detect_fingerprints):
    """
    노래 목록 중에서 가장 유사도가 높은 노래를 감지.
    감지 데이터 반환.
    """
    best_similarity = 0.0
    best_song_name = None
    best_offset = 0.0
    
    # 각 노래 지문을 순회하면서 지문 유사도 비교
    for song_name, detect_fingerprint in detect_fingerprints.items():
        similarity, offset = _compute_simularity(window_fingerprint, detect_fingerprint)
        
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

def _analyze_timeline(timelines):
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