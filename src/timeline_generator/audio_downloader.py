import traceback
import yt_dlp
from pathlib import Path
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def download_youtube_audio(
    youtube_url: str, 
    start_time: str, 
    end_time: str, 
    audio_format: str = "mp3", 
    audio_quality: str = "192",
    download_dir: Optional[Path] = None
) -> str:
    """
    YouTube 비디오에서 특정 시간 구간의 오디오를 다운로드합니다.

    Args:
        youtube_url (str): YouTube 비디오 URL
        start_time (str): 시작 시간 (HH:MM:SS 형식)
        end_time (str): 종료 시간 (HH:MM:SS 형식)
        audio_format (str, optional): 오디오 형식 (mp3, wav, m4a 등). 기본값 "wav".
        audio_quality (str, optional): 오디오 품질 (kbps). 기본값 "192".
        download_dir (Path, optional): 다운로드할 디렉토리 경로.
                                      기본값은 현재 파일 기준 "../downloads".

    Returns:
        str: 다운로드된 오디오 파일 경로

    Raises:
        ValueError: 입력 매개변수에 문제가 있는 경우
        RuntimeError: 다운로드 또는 처리 중 오류 발생 시
        FileNotFoundError: 예상된 출력 파일이 생성되지 않은 경우
    """
    try:
        # 다운로드 디렉토리 설정
        if download_dir is None:
            download_dir = Path(__file__).resolve().parent.parent.parent / "download"
        
        # 다운로드 디렉토리 생성 (없는 경우)
        download_dir.mkdir(exist_ok=True, parents=True)
        
        # 비디오 정보 가져오기
        logger.info(f"비디오 정보 가져오는 중: {youtube_url}")
        with yt_dlp.YoutubeDL({"skip_download": True}) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            title = info.get("title", "Unknown Title")
        
        # 안전한 파일명 생성
        safe_title = re.sub(r'[^\w\-_.]', '_', title)
        file_name = f"{safe_title}_{start_time.replace(':', '')}_{end_time.replace(':', '')}"
        file_path = download_dir / f"{file_name}.{audio_format}"
        
        logger.info(f"{start_time}부터 {end_time}까지 오디오 다운로드 중: {file_path}")
        
        # yt-dlp 옵션 설정
        ydl_opts = {
            "format": "bestaudio/best",
            "paths": {"home": str(download_dir)},
            "outtmpl": {"default": f"{file_name}.%(ext)s"},
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                    "preferredquality": audio_quality,
                }
            ],
            "postprocessor_args": ["-ss", start_time, "-to", end_time],
        }
        
        # 오디오 다운로드 및 처리
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        
        # 파일 존재 여부 확인
        if not file_path.exists():
            raise FileNotFoundError(f"예상된 출력 파일이 생성되지 않았습니다: {file_path}")
        
        logger.info(f"오디오 다운로드 완료: {file_path}")
        return str(file_path), f"{file_name}.{audio_format}"
    
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"YouTube 다운로드 오류: {e}")
        raise ValueError(f"YouTube에서 다운로드 실패: {e}")
    except Exception as e:
        logger.error(f"오디오 처리 오류: {e}", exc_info=True)
        traceback.print_exc()
        raise RuntimeError(f"오디오 처리 실패: {e}")