import librosa
import numpy as np
import io
import soundfile as sf
from spleeter.separator import Separator
import tempfile
import os

def remove_vocals(audio_bytes, target_sr=44100):
    """
    오디오 바이트 데이터에서 보컬을 제거하는 함수
    
    Parameters:
    -----------
    audio_bytes : bytes
        오디오 파일의 바이트 데이터
    target_sr : int, optional (default=44100)
        목표 샘플링 레이트 (Hz)
        
    Returns:
    - bytes : 보컬이 제거된 반주 데이터의 WAV 형식 바이트
    """
    # 바이트 데이터를 librosa로 로드
    audio_io = io.BytesIO(audio_bytes)
    
    # librosa로 오디오 로드 (모노 채널, 목표 샘플링 레이트 설정)
    y, sr = librosa.load(audio_io, sr=target_sr, mono=True)
    
    # Spleeter 분리기 생성 (2stems: vocals과 accompaniment로 분리)
    separator = Separator('spleeter:2stems')
    
    try:
        # 오디오 분리 시도 (메모리 내 처리)
        prediction = separator.separate(y)
        
        # 반주 데이터 가져오기
        accompaniment = prediction['accompaniment']
        
        # 스테레오인 경우 모노로 변환 (Spleeter는 주로 스테레오 출력 생성)
        if accompaniment.ndim > 1 and accompaniment.shape[0] == 2:
            accompaniment = np.mean(accompaniment, axis=0)
        elif accompaniment.ndim > 1 and accompaniment.shape[1] == 2:
            accompaniment = np.mean(accompaniment, axis=1)
    
    except Exception as e:
        # 메모리 내 처리 실패 시 파일 기반 처리
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name
            sf.write(temp_filename, y, sr, format='wav')
        
        # 임시 디렉토리 생성
        output_dir = tempfile.mkdtemp()
        
        try:
            # 파일 기반 분리
            separator.separate_to_file(temp_filename, output_dir)
            
            # 결과 파일 경로
            accompaniment_path = os.path.join(output_dir, os.path.basename(temp_filename)[:-4], 'accompaniment.wav')
            accompaniment, sr = librosa.load(accompaniment_path, sr=sr, mono=True)
        
        finally:
            # 임시 파일 및 디렉터리 정리
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            
            # 임시 디렉토리 정리 (재귀적으로)
            import shutil
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
    
    # 바이트 데이터로 변환
    output_buffer = io.BytesIO()
    sf.write(output_buffer, accompaniment, sr, format='wav')
    output_buffer.seek(0)
    return output_buffer.getvalue()