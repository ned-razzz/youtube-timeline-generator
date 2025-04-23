import yt_dlp
from pathlib import Path
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def download_youtube_audio_batch(
    youtube_urls: list[str], 
    start_time: str = "00:00:00", 
    end_time: str = "00:10:00", 
    audio_format: str = "wav", 
    audio_quality: str = "192",
    download_dir: Optional[Path] = None
):
    """
    여러 YouTube 비디오에서 특정 시간 구간의 오디오를 일괄 다운로드합니다.

    Args:
        youtube_urls (list[str]): YouTube 비디오 URL 목록
        start_time (str): 시작 시간 (HH:MM:SS 형식)
        end_time (str): 종료 시간 (HH:MM:SS 형식)
        audio_format (str, optional): 오디오 형식 (mp3, wav, m4a 등). 기본값 "wav".
        audio_quality (str, optional): 오디오 품질 (kbps). 기본값 "192".
        download_dir (Path, optional): 다운로드할 디렉토리 경로.
                                      기본값은 현재 파일 기준 "../downloads".

    Returns:
        list[tuple[str, str]]: 다운로드된 오디오 파일 경로와 파일명의 튜플 목록
    """
    # 다운로드 디렉토리 설정
    if download_dir is None:
        download_dir = Path(__file__).resolve().parent.parent.parent / "download"
    
    # 다운로드 디렉토리 생성
    download_dir.mkdir(exist_ok=True, parents=True)

    downloaded_file_paths = [] # 다운로드된 파일 정보를 저장할 리스트
    def save_path_hook(data):
        # 다운로드 완료 상태일 때만 처리
        if data['status'] == 'finished':
            file_path = data['filename']
            # 전체 경로 저장
            downloaded_file_paths.append(file_path)
            print(f'\n다운로드 완료: {file_path}')
    
    try:
        # 일괄 다운로드 설정
        logger.info(f"{start_time}부터 {end_time}까지 {len(youtube_urls)}개 오디오 다운로드 시작")
        ydl_opts = {
            "format": "bestaudio/best",
            "paths": {"home": str(download_dir)},
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": audio_quality,
            }],
            "postprocessor_args": ["-ss", start_time, "-to", end_time],
            'progress_hooks': [save_path_hook],
        }
        
        # 일괄 다운로드 실행
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(youtube_urls)
    
    except Exception as e:
        logger.error(f"다운로드 중 오류 발생: {e}", exc_info=True)
    
    logger.info(f"총 {len(downloaded_file_paths)}/{len(youtube_urls)}개 동영상 다운로드 완료")
    return downloaded_file_paths