from pathlib import Path
import numpy as np
import essentia.standard as es
from dataclasses import dataclass

@dataclass
class AudioChunk:
    audio: np.ndarray
    start_time: int
    end_time: int
    samplerate: int

def read_audio(audio_path: Path, chunk_size : int = 15, hop_size: int = 5):

    # 파라미터 검증
    if not audio_path.is_file():
        raise ValueError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

    # 오디오 메타데이터 추출
    metadata = es.MetadataReader(filename=str(audio_path))()
    metadata = metadata[7:]
    audio_length = int(metadata[-4])
    audio_samplerate = int(metadata[-2])

    print(f"- 오디오 정보:")
    print(f"\t이름: {audio_path.name}")
    print(f"\t길이: {audio_length}초")
    print(f"\t샘플레이트: {audio_samplerate}")

    print("- 오디오 추출 설정:")
    print(f"\t윈도우 크기: {chunk_size}초")
    print(f"\t홉 크기: {hop_size}초")
    print()

    # hip_size만큼 각 윈도우 분리
    chunk_iterator = np.arange(0, audio_length - chunk_size + 1, hop_size) # 0초부터 ~ audio_length - chunk_size만큼 순회
    chunk_count = len(chunk_iterator)
  
    for idx, chunk_pos in enumerate(chunk_iterator):
        chunk_pos = chunk_pos.item()
        print(f"오디오 로드: {idx+1}/{chunk_count} ({(idx+1)/chunk_count*100:.1f}%)")
        
        # 청크의 시작 및 종료 시간 계산
        chunk_start_time = chunk_pos
        chunk_end_time = min(chunk_pos + chunk_size, audio_length)
        chunk_duration = chunk_end_time - chunk_start_time
        print(f"현재 청크: {chunk_start_time:.3f} ~ {chunk_end_time:.3f} (second) (길이={chunk_duration:.3f}초)")

        # 해당 chunk 구간만 로드
        audio_data = es.EasyLoader(
            filename=str(audio_path),
            sampleRate=audio_samplerate,
            startTime=chunk_start_time,
            endTime=chunk_end_time
        )()
        yield AudioChunk(audio_data, chunk_start_time, chunk_end_time, audio_samplerate)
        del audio_data
        print()