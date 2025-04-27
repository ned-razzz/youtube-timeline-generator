import re
import tempfile
import yt_dlp
from pathlib import Path
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

def download_youtube_audio_batch(
    youtube_urls: List[str], 
    start_time: str = "00:00:00", 
    end_time: str = "00:10:00", 
    audio_format: str = "wav", 
    audio_quality: str = "192",
) -> Tuple[int, Path]:
    """
    여러 YouTube 비디오에서 특정 시간 구간의 오디오를 일괄 다운로드합니다.
    """
    # 일시적인 다운로드 디렉토리 생성
    download_dir = tempfile.mkdtemp()

    # 유튜브 오디오 성공 횟수 hook
    success_downloads = 0
    def save_path_hook(data):
        # 다운로드 완료 상태일 때만 처리
        if data["status"] == "finished":
             nonlocal success_downloads
             success_downloads += 1
    
    try:
        # 일괄 다운로드 설정
        logger.info(f"{start_time}부터 {end_time}까지 {len(youtube_urls)}개 오디오 다운로드 시작")
        ydl_opts = {
            "format": "bestaudio/best",
            "paths": {"home": download_dir},
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
    
    logger.info(f"총 {success_downloads}/{len(youtube_urls)}개 동영상 다운로드 완료")
    return  success_downloads, Path(download_dir)