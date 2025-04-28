"""
파일 시스템 기반 오디오 지문 관리 모듈
오디오 지문을 .pkl 파일로 저장하고 WorldCup을 폴더로 구현
"""

import pickle
from pathlib import Path
from typing import Dict
import numba as nb
import logging

from src.utils.types import TypeConverter
from src.utils.memory_manager import MemoryMonitor

logger = logging.getLogger(__name__)


class FileDB:
    """오디오 지문을 파일 시스템에 저장하는 관리자 클래스"""

    base_path = Path("fingerprints")

    @classmethod
    def _ensure_directory(cls):
        """데이터베이스 디렉토리가 존재하는지 확인하고, 없으면 생성합니다."""
        if not cls.base_path.exists():
            cls.base_path.mkdir(parents=True)

    @classmethod
    def save_audioprint(
        cls, file_name: str, audioprint: nb.typed.Dict, folder_name: str
    ):
        """오디오 지문을 파일로 저장"""
        # 월드컵 폴더 경로 생성
        worldcup_path = cls.base_path / folder_name

        # 저장 경로 설정
        save_path = worldcup_path / f"{file_name}.pkl"

        # 오디오 지문을 직렬화 가능한 파이썬 딕셔너리로 변환
        audioprint_dict = TypeConverter.convert_python_dict(audioprint)
        with open(save_path, "wb") as f:
            pickle.dump(audioprint_dict, f)

        return str(save_path)

    @classmethod
    def load_audioprint(cls, file_path: Path):
        """오디오 지문 파일을 로드"""
        # 오디오 지문 파일 로드
        with open(file_path, "rb") as f:
            audioprint_data = pickle.load(f)

        # 오디오 지문을 numba 딕셔너리 타입으로 변환
        audioprint = TypeConverter.convert_numba_dict(audioprint_data)

        # 출력
        logger.info(f"오디오 지문 로드: {file_path.stem}")
        MemoryMonitor.monitor_system()
        return audioprint

    @classmethod
    def load_audioprints(cls, folder_name: str) -> Dict[str, nb.typed.Dict]:
        """데이터베이스 폴더의 모든 오디오 지문 로드"""
        folder_path = cls.base_path / folder_name

        if not folder_path.exists():
            return {}

        # 오디오 지문 리스트 저장 변수
        audioprints = {}

        # 모든 .pkl 파일을 찾아서 로드
        for file_path in folder_path.glob("*.pkl"):
            audioprint_name = file_path.stem
            with open(file_path, "rb") as f:
                audioprints[audioprint_name] = cls.load_audioprint(file_path)

        return audioprints


# 모듈 import 즉시 데이터베이스 디렉토리 생성
FileDB._ensure_directory()
