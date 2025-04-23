"""
파일 시스템 기반 오디오 지문 관리 모듈
오디오 지문을 .pkl 파일로 저장하고 WorldCup을 폴더로 구현
"""
import pickle
import os
from pathlib import Path
from typing import List, Dict, Union
import numba as nb

from src.timeline_generator.types import convert_to_python_dict, convert_to_numba_dict

class FingerprintDB:
    """오디오 지문을 파일 시스템에 저장하는 관리자 클래스"""
    
    def __init__(self, base_path: Union[str, Path] = "fingerprints"):
        """
        파일 시스템 관리자 초기화
        
        Args:
            base_path: 데이터 저장 기본 경로
        """
        self.base_path = Path(base_path)
        self._ensure_directory(self.base_path)
    
    def _ensure_directory(self, path: Path):
        """디렉토리가 존재하는지 확인하고, 없으면 생성합니다."""
        if not path.exists():
            path.mkdir(parents=True)
    
    def insert_changpop(self, changpop_name: str, fingerprint: nb.typed.Dict, worldcup: str):
        """
        오디오 지문을 파일로 저장
        
        Args:
            changpop_name: 곡 이름 (파일명으로 사용됨)
            fingerprint: 오디오 지문 데이터
            worldcup: 월드컵 폴더 이름
            
        Returns:
            str: 저장된 파일의 경로
        """
        # 월드컵 폴더 경로 생성
        worldcup_path = self.base_path / worldcup
        self._ensure_directory(worldcup_path)
        
        # 저장 경로 설정
        save_path = worldcup_path / f"{changpop_name}.pkl"
        
        # fingerprint 데이터를 파이썬 딕셔너리로 변환하여 저장
        dict_fingerprint = convert_to_python_dict(fingerprint)
        with open(save_path, 'wb') as f:
            pickle.dump(dict_fingerprint, f)
        
        return str(save_path)
    
    def load_changpops(self, worldcup: str) -> Dict[str, nb.typed.Dict]:
        """
        특정 WorldCup 폴더의 모든 오디오 지문 로드
        
        Args:
            worldcup: 월드컵 폴더 이름
            
        Returns:
            Dict[str, nb.typed.Dict]: 곡 이름을 키로, 오디오 지문을 값으로 하는 딕셔너리
        """
        worldcup_path = self.base_path / worldcup
        
        if not worldcup_path.exists():
            return {}
        
        result = {}
        
        # 모든 .pkl 파일을 찾아서 로드
        for file_path in worldcup_path.glob("*.pkl"):
            changpop_name = file_path.stem
            
            try:
                with open(file_path, 'rb') as f:
                    fingerprint_dict = pickle.load(f)
                    fingerprint = convert_to_numba_dict(fingerprint_dict)
                    result[changpop_name] = fingerprint
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                continue
        
        return result