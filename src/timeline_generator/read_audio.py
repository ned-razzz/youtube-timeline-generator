from pathlib import Path
import numpy as np
import essentia.standard as es
from dataclasses import dataclass
from typing import Iterator

from src.utils import memory_manager

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
    audio_path: Path, 
    chunk_size: int = 15, 
    hop_size: int = 5
) -> Iterator[AudioChunk]:
    """
    오디오 파일을 청크 단위로 읽어 제너레이터로 반환합니다.
    
    Args:
        audio_path: 오디오 파일 경로
        chunk_size: 각 청크의 크기 (초)
        hop_size: 다음 청크로 이동할 때의 크기 (초)
        
    Yields:
        AudioChunk: 오디오 데이터와 시간 정보가 포함된 청크
        
    Raises:
        ValueError: 오디오 파일을 찾을 수 없는 경우
    """
    # 파라미터 검증
    if not audio_path.is_file():
        raise ValueError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

    # 오디오 메타데이터 추출
    metadata = es.MetadataReader(filename=str(audio_path))()
    metadata = metadata[7:]  # 메타데이터 필터링
    audio_length = int(metadata[-4])
    audio_samplerate = int(metadata[-2])

    print_audio_info(audio_path.name, audio_length, audio_samplerate, chunk_size, hop_size)
     
    # 해당 chunk 구간만 로드
    full_audio = es.MonoLoader(
        filename=str(audio_path)
    )()
    memory_manager.monitor_memory()

    # 청크 위치 계산
    chunk_positions = np.arange(0, audio_length - chunk_size + 1, hop_size)
    chunk_count = len(chunk_positions)
    for idx, chunk_pos in enumerate(chunk_positions):
        chunk_pos = int(chunk_pos)  # numpy type에서 Python float로 변환
        
        # 진행 상황 출력
        print(f"오디오 로드: {idx+1}/{chunk_count} ({(idx+1)/chunk_count*100:.1f}%)")
        
        # 청크의 시작 및 종료 시간 계산
        chunk_start_time = chunk_pos
        chunk_end_time = min(chunk_pos + chunk_size, audio_length)
        chunk_duration = chunk_end_time - chunk_start_time
        
        print(f"현재 청크: {chunk_start_time:.3f} ~ {chunk_end_time:.3f} (second) (길이={chunk_duration:.3f}초)")

        start_index = chunk_start_time * audio_samplerate
        end_index = chunk_end_time * audio_samplerate

        splited_audio = full_audio[start_index:end_index]
        
        yield AudioChunk(splited_audio, chunk_start_time, chunk_end_time, audio_samplerate)
        
        # 메모리 관리를 위해 명시적으로 삭제
        del splited_audio
        print()