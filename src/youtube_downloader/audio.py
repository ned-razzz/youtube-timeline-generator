import os
import shutil
import tempfile
from pathlib import Path
import logging
from typing import List, Tuple
import numpy as np
import yt_dlp
import essentia.standard as es

logger = logging.getLogger(__name__)

class AudioDownloader:
    audio_format = 'wav'
    audio_quality = 192
    download_start = '00:00:00'
    download_end = '00:10:00'
    download_dir: Path = Path(tempfile.mkdtemp())

    @classmethod
    def _get_ydl_opts(cls, hooks: list = []):
        """ydl_opts 다운로드 옵션 반환"""
        return {
            'format': 'bestaudio/best',
            'paths': {'home': str(cls.download_dir)},
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': cls.audio_format,
                'preferredquality': f'{cls.audio_quality}',
            }],
            'postprocessor_args': ['-ss', cls.download_start, '-to', cls.download_end],
            'progress_hooks': hooks,
            'no_warnings': True,
            }
    
    @classmethod
    def set_config(cls, 
                   format: str = None, 
                   quality: int = None, 
                   start: str = None, 
                   end: str = None,
                   download_dir: Path = None):
        """오디오 다운로드 관련 설정"""
        if format:
            cls.audio_format = format
        if quality:
            cls.audio_quality = quality
        if start:
            cls.download_start = start
        if end:
            cls.download_end = end
        if download_dir:
            cls.download_dir = download_dir

    @classmethod
    def get_downloads_path(cls):
        """다운로드 오디오의 Path 리스트 반환"""
        for file_path in cls.download_dir.glob("*.wav"):
            yield file_path
    
    @classmethod
    def clean_out(cls):
        """다운로드 오디오 전체 삭제"""
        shutil.rmtree(cls.download_dir)
    
    @classmethod
    def _download(cls, urls: list, opts: dict):
        """유튜브 오디오 다운로드"""
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download(urls)
        return True

    @classmethod
    def download_audio_batch(cls, youtube_urls: List[str]) -> int:
        """다수의 유튜브 오디오 일괄 다운로드"""
        # 유튜브 오디오 성공 횟수 hook
        download_counts = 0
        def save_path_hook(data):
            # 다운로드 완료 상태일 때만 처리
            if data['status'] == 'finished':
                nonlocal download_counts
                download_counts += 1
        
        logger.info(f'{len(youtube_urls)}개 유튜브 오디오 다운로드: {cls.download_start} ~ {cls.download_end}')

        # 오디오 일괄 다운로드
        ydl_opts = cls._get_ydl_opts(save_path_hook)
        cls._download(youtube_urls, ydl_opts)

        logger.info(f'다운로드 완료: {download_counts}/{len(youtube_urls)}')

        return download_counts

    @classmethod
    def load_audio(cls, youtube_url: str) -> Tuple[np.ndarray, Path]:
        """하나의 유튜브 오디오 다운로드"""
        try:
            #오디오 다운로드
            ydl_opts = cls._get_ydl_opts()
            cls._download([youtube_url], ydl_opts)

            audio_path = next(cls.get_downloads_path())
            _, _, sample_rate = cls.get_audio_metadata(audio_path)

            audio_data = es.MonoLoader(
                filename=str(audio_path),
                sampleRate=sample_rate
            )()
            print(type(audio_data))

            return audio_data, audio_path
        except Exception as e:
            logger.error(f'유튜브 다운로드 실패: {e}')
            return None

    @classmethod
    def get_audio_metadata(cls, audio_path: Path):
        """오디오 메타데이터 추출"""
        metadata = es.MetadataReader(filename=str(audio_path))()
        duration = int(metadata[-4])
        sample_rate = int(metadata[-2])
        name = audio_path.stem
        return name, duration, sample_rate