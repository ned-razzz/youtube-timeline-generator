import os
import numpy as np
from typing import Any, Generator
from spleeter.separator import Separator
import gc
import tensorflow as tf
import threading

# TensorFlow 불필요한 메시지 제거
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

# 단일 Separator 인스턴스를 전역으로 생성 (모든 청크에서 재사용)
_separator = None
_separator_lock = threading.Lock()

def get_separator():
    """
    Spleeter 분리기의 싱글톤 인스턴스를 반환합니다.
    메모리 사용을 최적화하기 위해 한 번만 로드합니다.
    """
    global _separator
    with _separator_lock:
        if _separator is None:
            # TensorFlow의 메모리 증가를 제한
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                try:
                    # 필요한 메모리만 할당하도록 설정
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                except RuntimeError as e:
                    print(f"GPU 메모리 설정 중 오류: {e}")
            
            # CPU 사용 시 연산 스레드 제한
            tf.config.threading.set_intra_op_parallelism_threads(2)
            tf.config.threading.set_inter_op_parallelism_threads(1)
            
            print("Spleeter 모델 로딩 중...")
            _separator = Separator('spleeter:2stems')
            print("Spleeter 모델 로딩 완료")
    
    return _separator

def remove_vocals(audio_chunks: Generator[np.ndarray, Any, None]) -> Generator[np.ndarray, Any, None]:
    """
    제너레이터에서 받은 오디오 청크의 보컬을 제거하고 처리된 오디오를 NumPy 배열로 반환합니다.
    
    Args:
        audio_chunks: 오디오 데이터(NumPy 배열) 제너레이터
        
    Yields:
        보컬이 제거된 NumPy 배열
    """
    # 분리기 인스턴스 한 번만 생성 (모든 청크에서 공유)
    separator = get_separator()
    
    for chunk_index, audio_chunk in enumerate(audio_chunks):
        print(f"\n처리 중인 청크: {chunk_index+1}")
        
        try:
            # 메모리 사용량 확인 (선택 사항)
            # print(f"현재 메모리 사용량: {psutil.Process().memory_info().rss / (1024 * 1024):.2f} MB")
            
            # 보컬 분리 수행
            prediction = separator.separate(audio_chunk)
            
            # 반주 부분만 추출하여 반환
            accompaniment = prediction['accompaniment']
            
            # 필요없는 데이터 명시적 삭제
            del prediction
            
            # 가비지 컬렉션 실행 (선택적으로 비활성화하여 성능 테스트)
            if chunk_index % 5 == 0:  # 5개 청크마다 GC 실행
                gc.collect()
                
            yield accompaniment
            
        except Exception as e:
            print(f"청크 {chunk_index+1} 처리 중 오류 발생: {str(e)}")
            # 오류 발생 시 원본 오디오 반환
            yield audio_chunk
        
    # 모든 처리 완료 후 메모리 정리
    gc.collect()