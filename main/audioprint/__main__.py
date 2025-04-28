"""
YouTube 오디오 추출 및 지문 생성 배치 처리 애플리케이션 메인 모듈
"""
from dataclasses import dataclass
import re
import traceback
import argparse
import gc
from pathlib import Path
import logging
from typing import Any, List, Tuple
import essentia.standard as es

from src.audioprint_manager.audioprint_generator import AudioprintGenerator
from src.utils.file_db import FileDB
from src.youtube_downloader.audio import AudioDownloader

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_youtube_urls(file_path: Path) -> list:
    logger.info(f"{file_path} 경로에서 YouTube URL 리스트를 가져오는 중...")

    # 파일 여부 검증
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} 경로에서 파일을 못찾았습니다.")
    
    # 파일에서 유튜브 url 읽기
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # 각 줄을 읽고, 빈 줄과 공백을 제거
            for line in file:
                 line = line.strip()
                 if line:
                     urls.append(line)
                     logger.info(f"\tRead URL: {line}")
    except IOError as e:
        logger.error(f"URL 파일을 읽을 때 오류가 발생했습니다: {e}")
        raise
        
    # 로그 출력
    if not urls:
        raise Exception("URL을 하나 아상 가져오지 못했습니다.")

    logger.info(f"읽은 YouTube URL 리스트: {len(urls)}개")
    
    return urls

def download_youtube_audios(
    urls: list,
) -> Path:
    # YouTube URL에서 오디오 다운로드
    AudioDownloader.set_config(start="00:00:00", end="00:00:30")

    downloads_count = AudioDownloader.download_audio_batch(urls)
    if downloads_count == 0:
        raise Exception("오디오를 하나 이상 다운로드 받지 못했습니다.")

def generate_audioprints()-> List[Tuple[str, Any]]:
    logger.info(f"다운로드한 오디오를 오디오 지문으로 변환 중...")

    processed_count = 0 # 지문 변환 성공 횟수
    failed_count = 0 # 지문 변환 실패 횟수
    audioprints = [] # 오디오 지문 저장 변수
    
    # 디렉토리에서 오디오 파일들을 읽어서 오디오 지문 변환
    for audio_path in AudioDownloader.get_downloads_path():
        #오디오의 노래 제목 가져오기
        audio_name = re.sub(r'(.*?)\s+\[[^\]]*\]$', r'\1', Path(audio_path).stem)

        try:
            # 오디오 파일 로드 및 지문 생성
            _, _, sample_rate = AudioDownloader.get_audio_metadata(audio_path)
            audio_path = es.MonoLoader(filename=str(audio_path), sampleRate=sample_rate)()

            # 오디오 지문 생성
            audioprint = AudioprintGenerator.get_spectrogram_fingerprint(audio_path, sample_rate)
        except Exception as e:
            # 지문 생성 실패 시
            failed_count += 1
            logger.error(f"지문 생성 실패: {audio_name}")
            # logger.error(f"{e}")
            traceback.print_exc()
            continue
            
        # 지문 생성 성공 시
        processed_count += 1
        audioprints.append((audio_name, audioprint))

    if processed_count == 0:
        raise Exception("아무 지문도 생성하지 못했습니다.")

    logger.info(f"지문 생성 완료: 성공 {processed_count}개 실패 {failed_count}개")

    return audioprints

def save_audioprints(
    audioprints: List[Tuple[str, Any]],
    worldcup_name: str,
) -> tuple:
    """
    다운로드된 오디오 파일에서 지문을 생성하고 데이터베이스에 저장합니다.
    """
    logger.info(f"오디오 지문 데이터베이스에 저장 중...")

    for name, audioprint in audioprints:
        FileDB.save_audioprint(name, audioprint, worldcup_name)
        logger.info(f"지문 저장 완료: {name}")

# 메임 함수 인자
@dataclass
class TypedArgs:
    url_file: Path
    worldcup_name: str

def get_parameters():
    parser = argparse.ArgumentParser(description="YouTube URL에서 오디오 다운로드 및 지문 생성 도구")
    
    parser.add_argument("-u", "--urls", type=str, required=True, 
                        help="YouTube URL이 포함된 텍스트 파일 경로")
    parser.add_argument("-n", "--name", 
                        help="지문 컬렉션 이름 (지문 생성 시 필수)")
    args = parser.parse_args()

    # 모듈 실행 파라미터 출력
    logger.info(f"URL 파일: {args.urls}")
    logger.info(f"월드컵 지문 이름: {args.name}")

    return TypedArgs(Path(args.urls), args.name)

def main():
    """메인 실행 함수"""
    # 메인 함수 인자 가져오기
    print()
    args = get_parameters()
    
    # 유튜브 url 리스트 읽기
    print()
    youtube_urls = read_youtube_urls(args.url_file)
    
    # 유튜브 오디오 배치 다운로드 수행
    print()
    download_youtube_audios(youtube_urls)

    # 오디오 지문 생성
    try:
        print()
        audioprints = generate_audioprints()

        # 오디오 지문 저장
        print()
        save_audioprints(audioprints, args.worldcup_name)
    finally:
        # 다운로드한 오디오 삭제
        AudioDownloader.clean_out()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"오디오 지문 생성 실패: {e}")
        traceback.print_exc()
    finally:
        gc.collect()