import numpy as np
from dataclasses import dataclass
from typing import Iterator

from src.utils.formatter import TimeFormatter

@dataclass
class AudioChunk:
    """오디오 데이터 청크를 나타내는 데이터 클래스"""
    audio: np.ndarray
    start_time: float  # 시작 시간 (초)
    end_time: float    # 종료 시간 (초)
    samplerate: int    # 샘플레이트 (Hz)

def print_audio_info(
    audio_name: str, 
    audio_length: int, 
    audio_samplerate: int, 
    chunk_size: int, 
    hop_size: int
) -> None:
    """오디오 정보와 추출 설정을 출력합니다."""
    print(f"- 오디오 정보:")
    print(f"\t이름: {audio_name}")
    print(f"\t길이: {audio_length}초")
    print(f"\t샘플레이트: {audio_samplerate}")

    print("- 오디오 추출 설정:")
    print(f"\t윈도우 크기: {chunk_size}초")
    print(f"\t홉 크기: {hop_size}초")
    print()

def read_audio(
    full_audio: np.ndarray, 
    duration,
    sample_rate,
    chunk_size, 
    hop_size
) -> Iterator[AudioChunk]:
    """
    오디오 데이터를 청크 단위로 읽어 제너레이터로 반환합니다.
    """
    # 청크 위치 계산
    chunk_positions = np.arange(0, duration - chunk_size + 1, hop_size)
    chunk_count = len(chunk_positions)
    for idx, chunk_pos in enumerate(chunk_positions):
        chunk_pos = int(chunk_pos)  # numpy type에서 Python float로 변환
        
        # 진행 상황 출력
        print(f"오디오 로드: {idx+1}/{chunk_count} ({(idx+1)/chunk_count*100:.1f}%)")
        
        # 청크의 시작 및 종료 시간 계산
        chunk_start_time = chunk_pos
        chunk_end_time = min(chunk_pos + chunk_size, duration)
        chunk_duration = chunk_end_time - chunk_start_time
        
        start_str = TimeFormatter.format_time_to_str(chunk_start_time)
        end_str = TimeFormatter.format_time_to_str(chunk_end_time)
        print(f"현재 청크: {start_str} ~ {end_str} (second) (길이={chunk_duration}초)")

        start_index = chunk_start_time * sample_rate
        end_index = chunk_end_time * sample_rate

        splited_audio = full_audio[start_index:end_index]
        
        yield AudioChunk(splited_audio, chunk_start_time, chunk_end_time, sample_rate)
        
        # 메모리 관리를 위해 명시적으로 삭제
        del splited_audio
        print()