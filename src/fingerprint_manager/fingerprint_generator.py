import os
import pickle
import essentia
import essentia.standard as es
import numpy as np
from datetime import datetime


def convert_audio_fingerprint(audio_file):
    """
    오디오 파일에서 Chromaprint 지문 생성

    매개변수:
        audio_file (str): 오디오 파일 경로

    반환:
        tuple: (지문 배열, 메타데이터)
    """
    try:
        sample_rate = 44100
        # 오디오 파일 로드
        loader = es.MonoLoader(filename=audio_file, sampleRate=sample_rate)
        audio = loader()

        # 오디오 데이터 유효성 검사
        if not _is_audio_valid(audio):
            print(f"경고: 오디오 파일 '{audio_file}'의 데이터가 유효하지 않습니다.")
            if np.all(audio == 0):
                print("오디오 데이터가 모두 0입니다. 비어있는 파일일 수 있습니다.")
            return None, {}
        print(f"오디오 통계: 최소={np.min(audio)}, 최대={np.max(audio)}, 평균={np.mean(audio)}")

        # 오디오 길이 계산
        duration = len(audio) / sample_rate

        # Chromaprint 지문 생성
        fingerprint = create_fingerprint(audio)
        
        # 지문 출력 디버깅
        print(f"생성된 지문 모양: {fingerprint.shape}, 타입: {fingerprint.dtype}")
        print(f"지문 통계: 최소={np.min(fingerprint)}, 최대={np.max(fingerprint)}")
        print(f"지문 샘플(처음 5개): {fingerprint[:5]}")

        # 모든 값이 같은지 확인
        if np.all(fingerprint == fingerprint[0]):
            print("경고: 생성된 지문의 모든 값이 동일합니다.")

        # 지문 메타데이터
        metadata = {
            "duration": round(duration),
            "sample_rate": sample_rate,
            "channels": 1,
            "method": "chromaprint_v2",  # 메소드 이름 변경해 구분
            "dtype": str(fingerprint.dtype),
            "shape": str(fingerprint.shape),
        }

        return fingerprint, metadata

    except Exception as e:
        print(f"지문 생성 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None, {}


def _is_audio_valid(audio):
    """오디오 데이터 유효성 검사"""
    if audio is None or len(audio) == 0:
        return False
    
    # 모두 같은 값인지 확인
    if np.all(audio == audio[0]):
        return False
    
    # 진폭이 너무 작은지 확인 (거의 무음)
    if np.max(np.abs(audio)) < 1e-6:
        return False
    
    return True


def create_fingerprint(audio):
    """크로마프린트 기반 지문 생성"""
    try:
        # 방법 1: 전체 오디오에 대한 HPCP 특성 추출
        spectral_peaks = es.SpectralPeaks()
        hpcp = es.HPCP()
        
        # 윈도우 생성
        window = es.Windowing(type='blackmanharris62')
        spectrum = es.Spectrum()
        
        frame_size = 4096
        hop_size = 2048
        
        chroma_features = []
        
        for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
            windowed_frame = window(frame)
            spectrum_frame = spectrum(windowed_frame)
            
            # 스펙트럼 피크 추출
            freqs, mags = spectral_peaks(spectrum_frame)
            
            # HPCP 특성 추출
            hpcp_vals = hpcp(freqs, mags)
            
            # 정규화를 통해 값 범위 조정
            normalized = hpcp_vals / (np.max(hpcp_vals) + 1e-10)
            
            chroma_features.append(normalized)
        
        fingerprint = np.array(chroma_features)
        
        # 디버깅: 특성 벡터의 값 분포 확인
        if len(chroma_features) > 0:
            print(f"첫 번째 특성 벡터: {chroma_features[0]}")
            print(f"특성 벡터 통계: 최소={np.min(fingerprint)}, 최대={np.max(fingerprint)}")
        
        return fingerprint
    
    except Exception as e:
        print(f"크로마프린트 생성 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
        # 오류 발생 시 빈 배열 대신 None을 반환하여 문제 표시
        return None


def save_fingerprint(fingerprint, metadata=None, output_dir="fingerprints", filename=None):
    """
    오디오 지문과 메타데이터를 파일로 저장
    
    매개변수:
        fingerprint (np.array): 오디오 지문 배열
        metadata (dict): 지문 관련 메타데이터
        output_dir (str): 저장할 디렉토리 경로
        filename (str, optional): 저장할 파일 이름(확장자 없이). 지정하지 않으면 타임스탬프 사용
        
    반환:
        str: 저장된 지문 파일 경로
    """
    # 지문이 유효한지 확인
    if fingerprint is None or (isinstance(fingerprint, np.ndarray) and (fingerprint.size == 0 or np.all(fingerprint == fingerprint.flat[0]))):
        print("경고: 저장하려는 지문이 유효하지 않습니다.")
        return None
    
    # 출력 디렉토리가 없으면 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 파일 이름이 지정되지 않은 경우 현재 시간으로 생성
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fingerprint_{timestamp}"
    else:
        # 확장자가 있으면 제거
        filename = os.path.splitext(os.path.basename(filename))[0]
    
    # 파일 경로 설정
    fingerprint_path = os.path.join(output_dir, f"{filename}.pkl")
    
    # 메타데이터와 함께 지문 저장
    data_to_save = {
        'fingerprint': fingerprint,
        'metadata': metadata or {}
    }
    
    # 지문 저장 (pickle 형식)
    with open(fingerprint_path, 'wb') as f:
        pickle.dump(data_to_save, f)
    
    print(f"지문이 저장되었습니다: {fingerprint_path}")
    print(f"저장된 지문 형태: {fingerprint.shape}")
    
    return fingerprint_path