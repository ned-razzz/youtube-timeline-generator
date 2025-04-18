import io
import os
import numpy as np
import soundfile as sf
from typing import Any, Generator
from numpy import ndarray
import librosa
import numpy as np

def read_chunks(file_path, chunk_size=8192):
    """
    오디오 파일을 청크 단위로 처리하는 제너레이터 함수
    
    Args:
        file_path (str): 처리할 오디오 파일 경로
        chunk_size (int): 각 청크의 크기(샘플 수)
    
    Yields:
        tuple: (audio_chunk, sample_rate) 형태의 튜플
              audio_chunk는 현재 처리 중인 오디오 데이터 부분
              sample_rate는 오디오의 샘플레이트
    """
    # 전체 오디오 파일 로드 (librosa는 기본적으로 전체 파일을 로드함)
    audio_data, sample_rate = librosa.load(file_path, sr=None)
    
    # 전체 오디오 길이
    total_length = len(audio_data)
    
    # 청크 단위로 데이터 생성
    current_processs = 0
    for i in range(0, total_length, chunk_size):
        # 현재 청크의 끝 인덱스 계산 (파일 끝 처리 포함)
        end_idx = min(i + chunk_size, total_length)
        
        # 현재 청크 추출
        current_chunk = audio_data[i:end_idx]
        
        next_processs = round(end_idx / total_length, 2) * 100
        if current_processs != next_processs:
            print(f"처리 중: {next_processs:.0f}%")
            current_processs = next_processs
        
        # 현재 청크와 샘플레이트 반환
        yield current_chunk, sample_rate

def save_audio(chunks: Generator[ndarray, Any, None], file_name="output.wav", samplerate=44100):
    """numpy ndarray 청크를 wav 형식으로 저장합니다."""
    # 출력 디렉토리가 없으면 생성
    os.makedirs("outputs", exist_ok=True)
    
    try:
        # 모든 청크 수집
        all_chunks = []
        chunk_count = 0
        
        for chunk in chunks:
            # 청크를 리스트에 추가
            all_chunks.append(chunk)
            
            # 진행 상황 로깅
            chunk_count += 1
            
        print(f"{chunk_count}개 청크 완료.")
        
        if not all_chunks:
            print("처리할 청크가 없습니다.")
            return
        
        print(f"총 {chunk_count}개 청크를 처리했습니다. WAV 파일로 저장합니다...")
        
        # 모든 청크를 하나의 큰 배열로 합치기
        audio_data = np.concatenate(all_chunks)
        
        # soundfile을 사용하여 WAV 파일로 저장
        output_path = f"outputs/{file_name}"
        sf.write(output_path, audio_data, samplerate)
        print(f"WAV 파일이 성공적으로 저장되었습니다: {output_path}")
        
    except StopIteration:
        print("Generator에서 청크를 가져올 수 없습니다.")
    except Exception as e:
        print(f"오디오 저장 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()