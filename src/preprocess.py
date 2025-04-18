import librosa
import io

def preprocess_audio(audio_bytes, target_sr=44100, normalize=True):
    """
    오디오 바이트 데이터를 전처리하는 함수
    
    Parameters:
    -----------
    audio_bytes : bytes
        오디오 파일의 바이트 데이터
    target_sr : int, optional (default=44100)
        목표 샘플링 레이트 (Hz)
    normalize : bool, optional (default=True)
        볼륨 노멀라이제이션 적용 여부
        
    Returns:
    --------
    y : np.ndarray
        오디오 신호 데이터 (모노 채널)
    """
    # 바이트 데이터를 librosa로 로드
    audio_io = io.BytesIO(audio_bytes)
    
    # librosa로 오디오 로드 (모노 채널, 목표 샘플링 레이트 설정)
    y, sr = librosa.load(audio_io, sr=target_sr, mono=True)
    
    # 볼륨 노멀라이제이션 적용 (선택 사항)
    if normalize:
        y = librosa.util.normalize(y)
    
    return y, sr