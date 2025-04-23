"""
YouTube 오디오 추출 및 지문 생성 배치 처리 애플리케이션 메인 모듈
"""
import re
import traceback
import argparse
import gc
from pathlib import Path
import logging
import os
import essentia.standard as es

from src.fingerprint_manager.fingerprint_generator import FingerprintGenerator
from src.utils.file_manager import FingerprintDB
from src.utils.memory_manager import monitor_memory
from src.youtube_downloader.audio_batch_downloader import download_youtube_audio_batch
# from src.youtube_downloader.audio_downloader import download_youtube_audio

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_youtube_urls(file_path: str) -> list:
    """
    텍스트 파일에서 YouTube URL 목록을 읽어옵니다.
    
    Args:
        file_path (str): YouTube URL이 포함된 텍스트 파일 경로
        
    Returns:
        list: YouTube URL 리스트
        
    Raises:
        FileNotFoundError: 파일을 찾을 수 없는 경우
        IOError: 파일을 읽을 수 없는 경우
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"URL 파일을 찾을 수 없습니다: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # 각 줄을 읽고, 빈 줄과 공백을 제거
            urls = [line.strip() for line in file if line.strip()]
        
        if not urls:
            logger.warning("URL 파일이 비어 있습니다.")
        else:
            logger.info(f"{len(urls)}개의 YouTube URL을 로드했습니다.")
        
        return urls
    except IOError as e:
        logger.error(f"URL 파일 읽기 오류: {e}")
        raise

def process_youtube_urls(
    urls: list,
    download_dir: Path = None
):
    """
    여러 YouTube URL에서 오디오를 다운로드합니다.
    
    Args:
        urls (list): YouTube URL 리스트
        start_time (str): 시작 시간 (HH:MM:SS 형식)
        end_time (str): 종료 시간 (HH:MM:SS 형식)
        audio_format (str, optional): 오디오 형식. 기본값 "wav".
        audio_quality (str, optional): 오디오 품질. 기본값 "192".
        download_dir (Path, optional): 다운로드 디렉토리. 기본값 None.
        
    Returns:
        tuple: (성공적으로 다운로드된 파일의 경로 리스트, 실패한 URL 리스트)
    """
    # 메모리 모니터링
    monitor_memory()
    
    # YouTube에서 다운로드
    downloaded_files = download_youtube_audio_batch(youtube_urls=urls, download_dir=download_dir)
    if not downloaded_files:
        raise Exception(f"빈 파일 정보: {downloaded_files}")
    print(f"✓ 다운로드 완료")

    return downloaded_files
        

def generate_fingerprints(
    download_results: list,
    audio_dir: str,
    worldcup_name: str,
) -> tuple:
    """
    다운로드된 오디오 파일에서 지문을 생성하고 데이터베이스에 저장합니다.
    
    Args:
        download_results (list): (오디오 파일 경로, 파일 이름) 튜플의 리스트
        worldcup_id (int): 연결할 월드컵 ID
        fingerprint_generator (FingerprintGenerator): 지문 생성기 인스턴스
        db_manager (DatabaseManager): 데이터베이스 관리자 인스턴스
        
    Returns:
        tuple: (성공적으로 처리된 파일 수, 실패한 파일 수)
    """
    db_manager = FingerprintDB()
    fingerprint_generator = FingerprintGenerator()

    processed_count = 0
    failed_count = 0
    
    for download_path in download_results:
        try:
            #오디오 지문의 이름 가져오기
            audio_name = Path(download_path).stem
            filtered_audio_name = re.sub(r'(.*?)\s+\[[^\]]*\]$', r'\1', audio_name)
            audio_path = audio_dir + '/' + audio_name + '.wav'

            print(f"지문 생성 중: {audio_path}...")
            # 오디오 파일 로드 및 지문 생성
            sample_rate = es.MetadataReader(filename=audio_path)()[-2]
            audio_file = es.MonoLoader(filename=audio_path, sampleRate=sample_rate)()
            fingerprint = fingerprint_generator.get_spectrogram_fingerprint(audio_file, sample_rate)
            
            # 데이터베이스에 저장
            print(f"데이터베이스에 저장 중: {audio_path}...")
            db_manager.insert_changpop(filtered_audio_name, fingerprint, worldcup_name)
            
            processed_count += 1
            print(f"지문 생성 및 저장 완료: {audio_path}")
            
        except Exception as e:
            failed_count += 1
            print(f"지문 생성 실패: {audio_path}, 오류: {str(e)}")
            logger.error(f"지문 생성 실패: {audio_path}, 오류: {str(e)}")
            traceback.print_exc()
            continue
        finally:
            # 메모리 정리
            gc.collect()
    
    return processed_count, failed_count

def get_parameters():
    parser = argparse.ArgumentParser(description="YouTube 오디오 배치 다운로드 및 지문 생성 도구")
    
    # 배치 다운로드 관련 인자
    parser.add_argument("--file", type=str, required=True, 
                        help="YouTube URL이 포함된 텍스트 파일 경로")
    parser.add_argument("--dir", type=str, default="download", 
                        help="다운로드 디렉토리 경로")
    # 지문 생성 관련 인자
    parser.add_argument("--fingerprint", action="store_true", 
                        help="다운로드 후 지문 생성 및 저장 활성화")
    parser.add_argument("-n", "--name", 
                        help="지문 컬렉션 이름 (지문 생성 시 필수)")
    args = parser.parse_args()
    
    # 지문 생성이 활성화된 경우 필수 인자 확인
    if args.fingerprint and not args.name:
        parser.error("지문 생성을 위해서는 --name 및 --genre 인자가 필요합니다.")

    return args

def main():
    """메인 실행 함수"""
    args = get_parameters()
    
    # 메인 헤더 출력``
    print("=======================================")
    print(f"URL 파일: {args.file}")
    print(f"다운로드 디렉토리: {args.dir if args.dir else '기본값'}")
    if args.fingerprint:
        print("지문 생성: 활성화")
        print(f"지문 월드컵 이름: {args.name}")
    print("=======================================")
    
    try:
        monitor_memory()

        # URL 리스트 읽기
        youtube_urls = read_youtube_urls(args.file)
        print(f"처리할 URL 수: {len(youtube_urls)}")
        
        # 다운로드 디렉토리 설정
        download_dir = Path(args.dir)
        download_dir.mkdir(exist_ok=True, parents=True)
        
        # 배치 다운로드 수행
        downloaded_files = process_youtube_urls(
            youtube_urls, 
            download_dir
        )
        
        # 다운로드 결과 출력
        print("=======================================")
        print(f"다운로드 성공: {len(downloaded_files)}개 파일")
        
        # 지문 생성 및 저장
        if args.fingerprint and downloaded_files:
            print("\n=======================================")
            print("지문 생성 및 저장 시작...")
            
            # 지문 생성 및 저장
            processed_count, failed_count = generate_fingerprints(
                downloaded_files,
                download_dir.stem,
                args.name,
            )
            
            # 지문 생성 결과 출력
            print("\n=======================================")
            print(f"지문 생성 성공: {processed_count}개 파일")
            print(f"지문 생성 실패: {failed_count}개 파일")

    except Exception as e:
        print(f"배치 처리 실패: {e}")
        traceback.print_exc()
    finally:
        # 강제 메모리 정리
        gc.collect()
        monitor_memory()

if __name__ == "__main__":
    main()