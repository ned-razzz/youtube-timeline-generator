import math
import librosa
import numpy as np
import io
import soundfile as sf
from spleeter.separator import Separator
import tempfile
import os
import gc
import psutil
import shutil

def remove_vocals(audio_bytes, chunk_duration=60, target_sr=22050):
    """
    오디오 바이트 데이터에서 보컬을 제거하는 함수 (청크 단위로 처리)
    
    Parameters:
    -----------
    audio_bytes : bytes
        오디오 파일의 바이트 데이터
    chunk_duration : int, optional (default=60)
        각 청크의 길이(초) - 메모리 소비 줄이기 위해 180초에서 60초로 감소
    target_sr : int, optional (default=22050)
        목표 샘플링 레이트 (Hz) - 44100에서 22050으로 감소하여 메모리 사용량 절반으로 줄임
        
    Returns:
    --------
    - bytes : 보컬이 제거된 반주 데이터의 WAV 형식 바이트
    """
    # 바이트 데이터로부터 오디오 로드
    audio_io = io.BytesIO(audio_bytes)
    
    # 메모리 사용량 출력 함수
    def print_memory_usage():
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        print(f"현재 메모리 사용량: {memory_info.rss / (1024 * 1024):.2f} MB")
    
    print_memory_usage()
    
    # 오디오의 샘플링 레이트 확인 (전체 길이 로드하지 않음)
    temp_y, sr = librosa.load(audio_io, sr=target_sr, mono=False, duration=5)
    audio_io.seek(0)  # 다시 처음으로 이동
    
    # 전체 오디오 길이 계산
    with sf.SoundFile(audio_io) as sound_file:
        total_frames = len(sound_file)
        total_duration = total_frames / sound_file.samplerate
        print(f"오디오 총 길이: {total_duration:.2f}초")
    
    audio_io.seek(0)  # 다시 처음으로 이동
    
    # 청크 개수 계산
    num_chunks = math.ceil(total_duration / chunk_duration)
    print(f"처리할 청크 개수: {num_chunks}")
    
    # Spleeter 분리기 생성 - 저품질 모델 사용 (메모리 소비 감소)
    separator = Separator('spleeter:2stems-16kHz')
    
    # 처리된 청크들을 저장할 임시 파일들
    temp_output_files = []
    
    try:
        for i in range(num_chunks):
            chunk_start = i * chunk_duration
            chunk_end = min((i + 1) * chunk_duration, total_duration)
            chunk_duration_actual = chunk_end - chunk_start
            
            print()
            print(f"청크 {i+1}/{num_chunks} 처리 중 ({chunk_start:.2f}초 ~ {chunk_end:.2f}초)...")
            print_memory_usage()
            
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_in_file:
                temp_in_filename = temp_in_file.name
            
            # 임시 출력 파일 생성
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_out_file:
                temp_out_filename = temp_out_file.name
                temp_output_files.append(temp_out_filename)
            
            try:
                # 현재 청크만 로드하여 임시 파일로 저장 (메모리 효율성)
                audio_io.seek(0)
                y_chunk, _ = librosa.load(audio_io, sr=target_sr, mono=False, 
                                        offset=chunk_start, duration=chunk_duration_actual)
                sf.write(temp_in_filename, y_chunk, target_sr, format='wav')
                
                # 변수 명시적으로 제거하여 메모리 확보
                del y_chunk
                gc.collect()
                
                # 임시 출력 디렉토리 생성
                output_dir = tempfile.mkdtemp()
                
                try:
                    # 파일 기반 분리 (메모리 효율적인 방법)
                    separator.separate_to_file(temp_in_filename, output_dir)
                    
                    # 결과 파일 경로
                    accompaniment_path = os.path.join(output_dir, os.path.basename(temp_in_filename)[:-4], 'accompaniment.wav')
                    
                    # 반주 데이터를 새 임시 파일로 복사 (직접 덮어쓰기)
                    shutil.copy(accompaniment_path, temp_out_filename)
                    
                except Exception as e:
                    print(f"청크 {i+1} 처리 중 오류 발생: {str(e)}")
                    # 오류 발생 시 원본 청크를 사용 (보컬 제거 실패)
                    shutil.copy(temp_in_filename, temp_out_filename)
                
                finally:
                    # 임시 디렉토리 정리 (재귀적으로)
                    if os.path.exists(output_dir):
                        shutil.rmtree(output_dir)
            
            finally:
                # 입력 임시 파일 정리
                if os.path.exists(temp_in_filename):
                    os.remove(temp_in_filename)
            
            # 명시적인 메모리 정리
            gc.collect()
            print_memory_usage()
        
        # 모든 청크 합치기 (파일 기반 방식으로 메모리 효율적)
        print("\n모든 청크 처리 완료, 결과 합치는 중...")
        output_buffer = io.BytesIO()
        
        # 첫 번째 파일 정보 가져오기 (샘플링 레이트 확인)
        info = sf.info(temp_output_files[0])
        
        # 출력 파일 준비
        with sf.SoundFile(output_buffer, 
                         mode='w', 
                         samplerate=info.samplerate,
                         channels=2, 
                         format='wav') as outfile:
            
            # 각 청크 파일을 순차적으로 읽어서 출력 파일에 쓰기
            for temp_file in temp_output_files:
                with sf.SoundFile(temp_file, mode='r') as infile:
                    # 작은 블록으로 나눠서 읽기 (메모리 효율성)
                    block_size = 4096
                    for block in infile.blocks(blocksize=block_size):
                        outfile.write(block)
        
        output_buffer.seek(0)
        return output_buffer.getvalue()
    
    finally:
        # 임시 파일 정리
        for temp_file in temp_output_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

# 더 작은 파일에서 테스트하기 위한 래퍼 함수
def test_on_small_file(input_file, output_file, test_duration=120):
    """
    더 작은 오디오 파일에서 보컬 제거 테스트
    
    Parameters:
    -----------
    input_file : str
        입력 오디오 파일 경로
    output_file : str
        출력 오디오 파일 경로
    test_duration : int, optional (default=120)
        테스트할 오디오 길이(초)
    """
    print(f"'{input_file}'에서 처음 {test_duration}초만 테스트합니다...")
    
    # 짧은 구간만 로드
    y, sr = librosa.load(input_file, sr=22050, mono=True, duration=test_duration)
    
    # 바이트로 변환
    temp_buffer = io.BytesIO()
    sf.write(temp_buffer, y, sr, format='wav')
    temp_buffer.seek(0)
    
    # 보컬 제거 함수 호출
    result_bytes = remove_vocals_chunked(temp_buffer.getvalue(), chunk_duration=30)
    
    # 결과 저장
    with open(output_file, 'wb') as f:
        f.write(result_bytes)
    
    print(f"테스트 완료! 결과가 '{output_file}'에 저장되었습니다.")