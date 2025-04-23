import logging
import os
import tempfile
import yt_dlp
import essentia.standard as es

logger = logging.getLogger(__name__)

def download_youtube_audio(
    youtube_url: str, 
    start_time: str, 
    end_time: str
    ):
    """
    YouTube에서 특정 시간 구간의 오디오를 다운로드하여 오디오 데이터를 반환합니다.

    Args:
        youtube_url (str): YouTube 비디오 URL
        start_time (str): 시작 시간 (HH:MM:SS 형식)
        end_time (str): 종료 시간 (HH:MM:SS 형식)

    Returns:
        ndarray: 다운로드된 오디오 데이터

    Raises:
        ValueError: 입력 매개변수에 문제가 있는 경우
        RuntimeError: 다운로드 또는 처리 중 오류 발생 시
        FileNotFoundError: 예상된 출력 파일이 생성되지 않은 경우
    """
    try:
        # 비디오 정보 가져오기
        logger.info(f"비디오 정보 가져오는 중: {youtube_url}")
        with yt_dlp.YoutubeDL({"skip_download": True}) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            title = info.get("title", "Unknown Title")

        logger.info(f"{title} 오디오를 {start_time}부터 {end_time}까지 다운로드 중...")
        audio_data, audio_samplerate, audio_length = get_audio_segment(youtube_url, start_time, end_time)

        metadata = {
            "name": title,
            "duration": audio_length,
            "sample_rate": audio_samplerate
        }
        return audio_data, metadata
    
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"YouTube 다운로드 오류: {e}")
        raise ValueError(f"YouTube에서 다운로드 실패: {e}")
    except Exception as e:
        logger.error(f"오디오 처리 오류: {e}", exc_info=True)
        raise RuntimeError(f"오디오 처리 실패: {e}")

def get_audio_segment(youtube_url, start_time, end_time, audio_format = "wav", audio_quality="192"):
    # 유튜브 오디오 저장할 임시 디렉토리
    temp_dir = tempfile.mkdtemp()
    file_name = "audio_segment"
    file_path = f"{temp_dir}/{file_name}.{audio_format}"

    # yt-dlp 옵션 설정
    ydl_opts = {
        "format": "bestaudio/best",
        "paths": {"home": temp_dir},
        "outtmpl": {"default": f"{file_name}.%(ext)s"},
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": audio_quality,
            }
        ],
        "postprocessor_args": ["-ss", start_time, "-to", end_time],
        "concurrent_fragment_downloads": 10,
        # "quiet": True,  # 로그 출력 최소화
        "no_warnings": True,  # 경고 숨기기
    }
    
    # 오디오 다운로드 및 처리
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    # 오디오 메타데이터 추출
    metadata = es.MetadataReader(filename=file_path)()
    audio_length = int(metadata[-4])
    audio_samplerate = int(metadata[-2])

    # 이제 essentia로 로드
    audio_data = es.MonoLoader(
        filename=file_path,
        sampleRate=audio_samplerate
    )()
    
    # 임시 저장 오디오 파일 삭제
    os.unlink(file_path)

    return audio_data, audio_samplerate, audio_length