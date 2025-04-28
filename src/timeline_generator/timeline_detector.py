from dataclasses import dataclass
from typing import Any, Dict, Generator

import numpy as np
import numba as nb

from src.timeline_generator.read_audio import AudioChunk
from src.audioprint_manager.audioprint_generator import AudioprintGenerator
from src.timeline_generator.similarity_processor import compute_similarity, compute_time_offsets
from src.utils.types import TimelineData
from src.utils.memory_manager import MemoryMonitor

class TimelineDetector:
    """노래 타임라인을 감지하는 클래스"""
    
    # 클래스 변수 정의
    BEST_SIMILARITY_THRESHOLD = 0.01
    
    @dataclass
    class DetectionResult:
        """노래 감지 결과를 저장하는 데이터 클래스"""
        similarity: float
        song_name: str
        offset: float
    
    @staticmethod
    def print_detection_result(song_name: str, similarity: float, start_time: float) -> None:
        """감지 결과를 출력합니다."""
        print("============================")
        print(f"발견: {song_name} (유사도: {similarity:.4f}), 시작 시간: {start_time}")
        print("============================")

    @classmethod
    def detect_best_match(
        cls,
        audio_fingerprint: nb.typed.Dict, 
        song_fingerprints: Dict[str, nb.typed.Dict]
    ) -> 'TimelineDetector.DetectionResult':
        """
        노래 목록 중에서 가장 유사도가 높은 노래를 감지합니다.
        """
        best_result = cls.DetectionResult(
            similarity=0.0,
            song_name="",
            offset=0.0
        )

        # 각 노래 지문을 순회하면서 지문 유사도 비교
        for name, song_fingerprint in song_fingerprints.items():
            time_offsets = compute_time_offsets(audio_fingerprint, song_fingerprint)
            numpy_offsets = np.array(time_offsets)

            # 가장 많이 발생하는 시간 오프셋 찾기 (일치하는 부분이 있다면)
            similarity, offset = compute_similarity(numpy_offsets,
                                                    len(audio_fingerprint),
                                                    len(song_fingerprint))
            print("\033[K", end="\r")
            print(f"{name}: {similarity}, {offset}", end="\r")

            if similarity > best_result.similarity:
                best_result.similarity = similarity
                best_result.song_name = name
                best_result.offset = offset
        print("\033[K", end="\r")
            
        return best_result

    @classmethod
    def detect_timeline(
            cls,
            audio_chunks: Generator[AudioChunk, Any, None], 
            song_fingerprints: Dict[str, nb.typed.Dict],
            hop_size: int,
            similarity_threshold: float
    ) -> Generator[TimelineData, None, None]:
        """
        오디오 청크에서 노래를 감지하고 타임라인을 생성합니다.
        """
        skip_counts = 0
        
        for chunk in audio_chunks:
            if skip_counts > 0:
                skip_counts -= 1
                continue

            # 현재 윈도우의 지문 생성
            chunk_fingerprint = AudioprintGenerator.get_spectrogram_fingerprint(
                chunk.audio, chunk.samplerate
            )

            # 노래 목록 중 최고 유사도 노래 감지
            detection = cls.detect_best_match(
                chunk_fingerprint, 
                song_fingerprints
            )
            print(f"유사도: {detection.similarity:.4f}, {detection.offset} ({detection.song_name})")
            MemoryMonitor.monitor_system()
            
            # 예상 시작 시간 계산
            audio_start_time = chunk.start_time - detection.offset
            if audio_start_time < 0:
                continue

            # 유사도가 임계값을 넘는 경우만 결과에 추가
            if detection.similarity < similarity_threshold:
                continue

            # 유사도 0.01 넘을 시 다음 90초의 청크는 무시
            if detection.similarity > cls.BEST_SIMILARITY_THRESHOLD:
                skip_counts += 90 // hop_size
            
            cls.print_detection_result(detection.song_name, detection.similarity, audio_start_time)
            # 값 저장
            timeline = {
                "song_name": detection.song_name,
                "similarity": detection.similarity,
                "start_time": round(audio_start_time),
            }
            yield timeline
