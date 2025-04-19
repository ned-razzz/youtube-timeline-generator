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
        tuple: (지문 배열, 오디오 길이(초), 메타데이터)
    """
    try:
        sample_rate = 44100
        # 오디오 파일 로드
        loader = es.MonoLoader(filename=audio_file, sampleRate=sample_rate)
        audio = loader()

        # 오디오 길이 계산
        duration = len(audio) / sample_rate

        # 지문 메타데이터
        metadata = {
            "duration": duration,
            "sample_rate":  sample_rate,
            "channels": 1,  # MonoLoader는 단일 채널 반환
            "fingerprint_method": "chromaprint",
            "creation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Chromaprint 지문 생성
        fingerprint = create_fingerprint(audio)

        return fingerprint, duration, metadata

    except Exception as e:
        print(f"지문 생성 중 오류 발생: {e}")
        return None, 0, {}


def create_fingerprint(audio):
    """크로마프린트 기반 지문 생성"""
    # 크로마프린트 설정
    chroma = es.Chromaprinter()
    pool = essentia.Pool()

    # 프레임 설정 (최적화된 값으로 조정)
    frame_size = 4096
    hop_size = 2048

    # 프레임별 처리
    for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
        chroma_value = chroma(frame)
        pool.add("chroma", chroma_value)

    return np.array(pool["chroma"])

def save_fingerprint(fingerprint, output_dir="fingerprints", filename=None):
    """
    오디오 지문과 메타데이터를 파일로 저장
    
    매개변수:
        fingerprint (np.array): 오디오 지문 배열
        metadata (dict): 지문 관련 메타데이터
        output_dir (str): 저장할 디렉토리 경로
        filename (str, optional): 저장할 파일 이름(확장자 없이). 지정하지 않으면 타임스탬프 사용
        
    반환:
        tuple: (fingerprint_path, metadata_path) 저장된 파일 경로들
    """
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
    
    # 지문 저장 (pickle 형식)
    with open(fingerprint_path, 'wb') as f:
        pickle.dump(fingerprint, f)
    
    print(f"지문이 저장되었습니다: {fingerprint_path}")