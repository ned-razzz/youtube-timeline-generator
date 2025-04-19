import os
import numpy as np
from typing import Any, Generator
from spleeter.separator import Separator
import gc
import tensorflow as tf

# TensorFlow 불필요한 메시지 제거
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

def remove_vocals(audio_chunks: Generator[np.ndarray, Any, None]) -> Generator[np.ndarray, Any, None]:
    """
    제너레이터에서 받은 오디오 청크의 보컬을 제거하고 처리된 오디오를 NumPy 배열로 반환합니다.
    
    Args:
        audio_chunks: 오디오 데이터(NumPy 배열) 제너레이터
        
    Yields:
        보컬이 제거된 NumPy 배열
    """
    # 모든 청크에서 재사용할 Spleeter 분리기 생성
    separator = Separator('spleeter:2stems')
    
    for chunk_index, audio_chunk in enumerate(audio_chunks):
        print(f"\n처리 중인 청크: {chunk_index+1}")
        
        try:
            # 보컬 분리 수행
            prediction = separator.separate(audio_chunk)
            
            # 반주 부분만 추출하여 반환
            accompaniment = prediction['accompaniment']
            yield accompaniment

            # del result
            
        except Exception as e:
            print(f"청크 {chunk_index+1} 처리 중 오류 발생: {str(e)}")
            # 오류 발생 시 원본 오디오 반환
            yield audio_chunk
        
        # 청크 처리 완료 후 메모리 정리
        gc.collect()