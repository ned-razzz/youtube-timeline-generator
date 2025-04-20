import traceback
from typing import Any, Generator
import librosa
import io
import soundfile as sf

def preprocess_audio(audio_chunks: Generator[bytes, Any, None], target_sr=48000, normalize=True):
    """
    오디오 청크를 전처리하는 제너레이터 함수
    
    Parameters:
    -----------
    audio_chunk : np.ndarray
        처리할 오디오 청크 데이터
    sr : int, optional (default=44100)
        입력 오디오 청크의 샘플링 레이트 (Hz)
    target_sr : int, optional (default=44100)
        목표 샘플링 레이트 (Hz)
    normalize : bool, optional (default=True)
        볼륨 노멀라이제이션 적용 여부
        
    Yields:
    -------
    processed_chunk : np.ndarray
        처리된 오디오 청크 데이터
        
    Raises:
    -------
    Exception
        오디오 처리 중 발생하는 모든 예외
    """
    try:
        for audio_chunk, sr in audio_chunks:
            # 리샘플링
            processed_chunk = librosa.resample(audio_chunk, orig_sr=sr, target_sr=target_sr)

            # 볼륨 정규화
            # processed_chunk = librosa.util.normalize(audio_chunk)
            
            yield processed_chunk
        
    except Exception as e:
        # 모든 예외를 상위로 전달
        raise Exception(f"오디오 전처리 실패: {e}")