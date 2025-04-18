import os
import yt_dlp
from pathlib import Path

class YouTubeAudioExtractor:
    """YouTube 오디오 구간 추출기"""

    @staticmethod
    def get_youtube_audio(
        youtube_url, start_time: str, end_time: str, audio_format="mp3", audio_quality="192"
    ):
        """
        YouTube 비디오에서 특정 시간 구간의 오디오를 추출하여 바이트로 반환

        Args:
            youtube_url (str): YouTube 비디오 URL
            start_time (str): 시작 시간 (HH:MM:SS 형식)
            end_time (str): 종료 시간 (HH:MM:SS 형식)
            audio_format (str): 오디오 형식 (mp3, wav, m4a 등)
            audio_quality (str): 오디오 품질 (kbps)

        Returns:
            tuple: (audio_bytes, content_type, title)
                - audio_bytes: 오디오 데이터 바이트
                - content_type: 오디오 MIME 타입
                - title: 원본 비디오 제목
        """

        try:
            # 비디오 정보 먼저 가져오기
            with yt_dlp.YoutubeDL({"skip_download": True}) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                title = info.get("title", "Unknown Title")

            file_name = f"{title}_{start_time.replace(':', '')}_{end_time.replace(':', '')}"
            current_folder = str(Path(__file__).resolve().parent.parent / "downloads")
            file_path = os.path.join(current_folder, f"{file_name}.{audio_format}")

            # yt-dlp 옵션 설정
            ydl_opts = {
                "format": "bestaudio/best",
                "paths": {"home": current_folder},
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

            # 처리된 오디오를 메모리로 읽기
            return YouTubeAudioExtractor._read_audio_file(
                file_path, audio_format, file_name
            )

        except Exception as e:
            print(f"오디오 처리 오류: {e}")
            return None, None, None

    @staticmethod
    def _read_audio_file(file_path, format_type, title):
        """파일에서 오디오 데이터 읽기"""
        with open(file_path, "rb") as f:
            audio_bytes = f.read()

        # MIME 타입 결정
        content_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "m4a": "audio/mp4",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
        }
        content_type = content_types.get(format_type, f"audio/{format_type}")

        return audio_bytes, content_type, title
