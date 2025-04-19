from .db_manager import DatabaseManager
from .fingerprint_generator import convert_audio_fingerprint, save_fingerprint
import os

def main():
    """
    오디오 파일에서 지문을 생성하고 저장하는 메인 함수
    """
    # 처리할 오디오 파일 경로
    audio_file = "audio/rimi_1.wav"
    print(f"오디오 파일 '{audio_file}'의 지문을 생성합니다...")
    
    # 지문 생성
    fingerprint, duration, metadata = convert_audio_fingerprint(audio_file)
    if fingerprint is not None:
        print(f"생성된 지문 정보:")
        print(f"- 오디오 길이: {duration:.2f}초")
        print(f"- 지문 형태: {fingerprint.shape}")
        print(f"- 메타데이터: {metadata}")
        print(f"작업이 완료되었습니다.")
    else:
        print(f"지문 생성에 실패했습니다.")
        return

    db = DatabaseManager()
    db.insert_changpop({
        'name': '리미제라블 1화', 
        'artist': None, 
        'duration': duration,
        'fingerprint_method': metadata['fingerprint_method'],
        'fingerprint': fingerprint.tobytes(),
        'worldcup_id': None,
        })

if __name__ == "__main__":
    main()