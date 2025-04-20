import argparse
from datetime import datetime
import json
import os
import pickle
import essentia.standard as es
from matplotlib import pyplot as plt
import numpy as np
from collections import defaultdict, Counter

def find_song_in_audio(long_audio, fingerprints, window_size=15.0, hop_size=5.0, sample_rate=44100, similarity_threshold=0.15):
    """
    긴 오디오에서 참조 노래들을 찾는 함수
    """
    # 각 노래 시작점 탐지
    detect_results = detect_changpops(long_audio, 
                                      fingerprints, 
                                      window_size, 
                                      sample_rate, 
                                      similarity_threshold)
    print("\n검색 완료")
    
    # 유사도 높은 순으로 정렬
    sorted_results = sorted(detect_results, key=lambda x: x["similarity"], reverse=True)

    # 중복 제거 (같은 노래가 여러 윈도우에서 발견될 수 있음)
    filtered_results = []
    seen_songs = set()
    for detect_window in sorted_results:
        song_name = detect_window["song_name"]
        start_time = detect_window["estimated_start_time"]
        
        # 이미 처리한 노래와 시작 시간이 가까운 경우 (5초 이내) 건너뛰기
        skip = False
        for seen_song, seen_time in seen_songs:
            if song_name == seen_song and abs(start_time - seen_time) < 5.0:
                skip = True
                break
        
        if not skip:
            filtered_results.append(detect_window)
            seen_songs.add((song_name, start_time))
    
    # 시작 시간 순으로 정렬
    filtered_results.sort(key=lambda x: x["estimated_start_time"])
    
    return filtered_results

def detect_changpops(
        long_audio, 
        fingerprints, 
        window_size=15.0, 
        hop_size=5.0, 
        sample_rate=44100, 
        similarity_threshold=0.15):
    # 긴 오디오의 총 길이 (초)
    total_duration = len(long_audio) / float(sample_rate)
    
    # hip_size만큼 각 윈도우 분리 
    window_starts = np.arange(0, total_duration - window_size, hop_size)
    
    # 작업 정보 출력
    print(f"긴 오디오 길이: {total_duration:.2f}초")
    print(f"윈도우 크기: {window_size:.2f}초, 홉 크기: {hop_size:.2f}초")
    print(f"총 {len(window_starts)}개 윈도우 검사")

    # 오디오 탐지 작업 개시
    results = []
    audio_progress = 0
    for i, start_time in enumerate(window_starts):
        # 현재 윈도우에 해당하는 오디오 세그먼트 추출
        start_sample = int(start_time * sample_rate)
        end_sample = int((start_time + window_size) * sample_rate)
        window_audio = long_audio[start_sample:end_sample]
        
        # 진행상황 표시
        print(f"\r윈도우 검사 중: {i+1}/{len(window_starts)} ({(i+1)/len(window_starts)*100:.1f}%)", end="")
        
        # 현재 윈도우의 지문 생성
        window_fingerprint = create()
        
        # 각 참조 노래와 비교
        best_similarity = 0.0
        best_song = None
        best_offset = 0.0
        
        for song_name, fingerprint in fingerprints.items():
            similarity, offset = compare_fingerprints(window_fingerprint, fingerprint)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_song = song_name
                best_offset = offset
        
        # 유사도가 임계값을 넘는 경우만 결과에 추가
        if best_similarity >= similarity_threshold:
            # 예상 시작 시간 계산 (윈도우 시작 시간 - 오프셋)
            song_start_time = start_time - best_offset
            
            # 유효한 시작 시간만 기록 (음수가 아닌 경우)
            if song_start_time >= 0:
                results.append({
                    "window_start": start_time,
                    "window_end": start_time + window_size,
                    "song_name": best_song,
                    "similarity": best_similarity,
                    "estimated_start_time": song_start_time,
                })
                
                audio_progress += fingerprint['duration']
                print(f"\n발견: {best_song} (유사도: {best_similarity:.4f}), 시작 시간: {round(audio_progress / 60)}분 {round(audio_progress % 60)}초")

    return results

# compare_fingerprints 함수 수정 (오프셋 반환)
def compare_fingerprints(fingerprint1, fingerprint2):
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

def main(long_audio, fingerprints, window_size=15.0, hop_size=5.0, sample_rate=44100, similarity_threshold=0.15):
    # 각 노래 시작점 탐지
    print("\n노래 검색 시작...")
    detect_results = detect_changpops(long_audio, 
                                      fingerprints, 
                                      window_size, 
                                      hop_size,
                                      sample_rate, 
                                      similarity_threshold)
    print("\n검색 완료")
    
    # 결과 출력 부분의 오류 수정
    if detect_results:
        print("\n발견된 노래:")
        print("-" * 80)
        print(f"{'시작 시간':^15}{'노래 이름':^30}{'유사도':^15}")
        print("-" * 80)
        
        for result in detect_results:
            start_time = result['estimated_start_time']
            song_name = result['song_name']
            similarity = result['similarity']
            
            # 시간을 MM:SS 형식으로 변환
            minutes = int(start_time // 60)
            seconds = int(start_time % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            
            # 수정된 형식 지정자
            print(f"{time_str:^15}{song_name:^30}{similarity:^15.4f}")
        
        # # 결과 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # result_file = f"song_detection_result_{timestamp}.json"
        
        # with open(result_file, 'w', encoding='utf-8') as f:
        #     json.dump(detect_results, f, indent=2)
        
        # print(f"\n결과가 {result_file}에 저장되었습니다.")
        
        # 결과 시각화
        plt.figure(figsize=(12, 6))
        
        # 긴 오디오의 총 길이
        total_duration = len(long_audio) / 44100  # 샘플링 레이트 44.1kHz 가정
        
        for i, result in enumerate(detect_results):
            start_time = result['estimated_start_time']
            song_name = result['song_name']
            similarity = result['similarity']
            
            # 색상은 유사도에 따라 결정 (높을수록 진한 색)
            color_intensity = 0.3 + 0.7 * similarity
            color = (0, color_intensity, 0)
            
            # 선과 텍스트로 시작 시간 표시
            plt.axvline(x=start_time, color=color, linestyle='-', linewidth=2)
            plt.text(start_time, i % 5 + 1, f"{song_name} ({similarity:.2f})", 
                    rotation=45, ha='right', fontsize=8)
        
        plt.xlim(0, total_duration)
        plt.ylim(0, 6)
        plt.xlabel('시간 (초)')
        plt.title('발견된 노래 시작 지점')
        plt.grid(True, alpha=0.3)
        plt.yticks([])
        
        # X축 틱을 MM:SS 형식으로 변환
        def format_time(x, pos):
            minutes = int(x // 60)
            seconds = int(x % 60)
            return f"{minutes:02d}:{seconds:02d}"
        
        plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(format_time))
        
        # 이미지 저장
        plt.tight_layout()
        plt.savefig(f"song_detection_visualization_{timestamp}.png", dpi=300)
        print(f"시각화 이미지가 song_detection_visualization_{timestamp}.png에 저장되었습니다.")
        
        # 이미지 표시
        plt.show()
    else:
        print("\n노래를 찾을 수 없습니다.")

if __name__ == "__main__":
    main()