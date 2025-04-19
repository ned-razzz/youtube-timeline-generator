import os
import shutil
import tempfile
import wave
import numpy as np
import soundfile as sf
import gc
from typing import Generator, Any

def read_chunks(file_path, chunk_size_seconds=30) -> Generator[np.ndarray, Any, None]:
    """
    오디오 파일을 청크 단위로 처리하는 제너레이터 함수
    
    Args:
        file_path (str): 처리할 오디오 파일 경로
        chunk_size_seconds (int): 각 청크의 길이(초)
        sample_rate (int): 원하는 샘플레이트
    
    Yields:
        numpy.ndarray: 현재 처리 중인 오디오 데이터 부분
    """
    # 오디오 파일 정보 얻기 (전체 파일을 메모리에 로드하지 않음)
    info = sf.info(file_path)
    file_sample_rate = info.samplerate
    total_samples = info.frames
    channels = info.channels
    print(f"샘플레이트: {file_sample_rate}, 총 샘플: {total_samples}, 채널: {channels}")

    # 청크 크기 계산 (샘플 수)
    chunk_size = int(chunk_size_seconds * file_sample_rate)

    # 현재 처리 진행률 초기화
    current_process = 0

    # 청크 단위로 데이터 읽기
    for start_idx in range(0, total_samples, chunk_size):
        # 현재 청크의 끝 인덱스 계산 (파일 끝 처리 포함)
        end_idx = min(start_idx + chunk_size, total_samples)
        
        # 현재 청크만 파일에서 읽기 (메모리 효율적)
        with sf.SoundFile(file_path) as f:
            # 시작 위치로 이동
            f.seek(start_idx)
            # 현재 청크 크기만큼 읽기
            current_chunk = f.read(frames=end_idx - start_idx, dtype='float32')
        
        # 모노로 변환 (Spleeter는 모노 입력 처리에 최적화됨)
        if channels > 1:
            current_chunk = np.mean(current_chunk, axis=1)
        
        # 2D 배열로 형태 변환 (Spleeter 요구사항)
        if current_chunk.ndim == 1:
            current_chunk = current_chunk.reshape(-1, 1)
        
        # 처리 진행률 계산 및 출력
        next_process = int(end_idx / total_samples * 100)
        if next_process > current_process:
            print(f"청크 로딩 중: {next_process}%")
            current_process = next_process
        
        # 현재 청크 반환
        yield current_chunk
        
        # 청크 처리 후 메모리 해제
        del current_chunk
        if start_idx % (chunk_size * 5) == 0:  # 5개 청크마다 GC 실행
            gc.collect()

def save_audio(audio_chunks, file_name, sample_rate=44100):
    """
    오디오 청크를 파일로 저장 (스트리밍 방식)
    
    Args:
        audio_chunks: 오디오 데이터(NumPy 배열) 제너레이터
        sample_rate: 샘플 레이트
        file_name: 출력 파일 이름
    """
    # 출력 디렉토리가 없으면 생성
    os.makedirs("output", exist_ok=True)
    final_output_path = os.path.join("output", f"instrumental_{file_name}")
    
    # 청크 수 카운터
    chunk_count = 0
    
    try:
        # 임시 WAV 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_path = temp_file.name
        
        # WAV 파일 헤더 정보 (나중에 업데이트됨)
        channels = 2  # 스테레오 기본값
        sample_width = 2  # 16-bit
        
        # 빈 WAV 파일 생성
        with wave.open(temp_path, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            
            # 각 청크를 순차적으로 파일에 추가
            for chunk in audio_chunks:
                chunk_count += 1
                print(f"청크 {chunk_count} 처리 중: 형태={chunk.shape}")
                
                # 첫 번째 청크에서 채널 수 확인 및 설정
                if chunk_count == 1:
                    # 2D 배열이면 형태에서 채널 수 확인
                    if chunk.ndim > 1:
                        channels = chunk.shape[1]
                        wav_file.setnchannels(channels)
                    else:
                        channels = 1
                        wav_file.setnchannels(1)
                
                # 채널에 따라 데이터 형태 조정
                audio_data = chunk
                if audio_data.ndim > 1 and audio_data.shape[1] == 1:
                    audio_data = audio_data.flatten()
                
                # float32를 16비트 정수로 변환
                if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                    audio_data = (audio_data * 32767).astype(np.int16)
                
                # WAV 파일에 데이터 쓰기
                wav_file.writeframes(audio_data.tobytes())
                
                # 메모리 정리
                del audio_data
                del chunk
                if chunk_count % 5 == 0:
                    gc.collect()
        
        # 완료된 임시 파일을 최종 위치로 이동
        print(f"최종 파일로 이동 중: {final_output_path}")
        shutil.move(temp_path, final_output_path)
        print(f"오디오 저장 완료: {final_output_path} ({chunk_count} 청크)")
        
    except Exception as e:
        print(f"오디오 저장 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        # 임시 파일 정리
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        raise