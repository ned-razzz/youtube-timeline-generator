import numpy as np
from typing import Any, Generator, Dict
import logging
import essentia.standard as es
import json
from ..db_manager import DatabaseManager, ChangPopData


logger = logging.getLogger(__name__)

class SongDetector:
    def __init__(self, db_path: str, sample_rate: int = 44100, sensitivity: float = 0.7):
        """
        essentia를 사용한 노래 감지기 초기화
        
        Args:
            db_path (str): SQLite 데이터베이스 경로
            sample_rate (int): 분석할 오디오의 샘플 레이트
            sensitivity (float): 감지 민감도 (0.0 ~ 1.0), 높을수록 엄격한 매칭
        """
        self.db_path = db_path
        self.sample_rate = sample_rate
        self.sensitivity = sensitivity

        self._reference: ChangPopData = None
        self._reference_fingerprint = None
        self._load_reference_fingerprint()
        
    def _load_reference_fingerprint(self):
        """
        SQLite 데이터베이스에서 id=1인 노래의 지문 로드
        """
        db_manager = DatabaseManager()
        
        # id=1인 노래의 지문 가져오기
        result: ChangPopData = db_manager.load_changpop_by_id(1)
        if not result:
            raise ValueError("ID=1인 노래를 데이터베이스에서 찾을 수 없습니다.")
        
        self._reference = result
        self._reference_fingerprint = result["fingerprint"]
        logger.info("참조 오디오 지문 로드 완료")
    
    def _compare_fingerprints(self, chunk_fingerprint: Any) -> float:
        """
        생성된 지문과 참조 지문 비교
        
        Args:
            chunk_fingerprint: 청크에서 생성된 지문
            
        Returns:
            float: 일치 점수 (0.0 ~ 1.0)
        """
        # essentia 또는 사용자 정의 방법으로 지문 비교
        # 실제 구현은 fingerprint 형식에 따라 달라질 수 있음
        
        # 예시: 간단한 유사도 비교 (실제 구현은 더 복잡할 수 있음)
        # 여기서는 각 프레임 간의 유클리드 거리를 계산
        
        try:
            # 참조 지문과 청크 지문의 길이가 다를 수 있으므로 더 짧은 길이 사용
            min_length = min(len(self._reference_fingerprint), len(chunk_fingerprint))
            
            if min_length == 0:
                return 0.0
            
            # 가장 유사한 구간 찾기
            best_score = 0.0
            window_size = 20  # 비교 윈도우 크기
            
            # 슬라이딩 윈도우로 가장 일치하는 부분 찾기
            for i in range(max(1, len(self._reference_fingerprint) - window_size)):
                ref_window = self._reference_fingerprint[i:i+window_size]
                
                for j in range(max(1, len(chunk_fingerprint) - window_size)):
                    chunk_window = chunk_fingerprint[j:j+window_size]
                    
                    # 각 프레임 간의 유사도 계산
                    similarities = []
                    for k in range(min(len(ref_window), len(chunk_window))):
                        ref_frame = np.array(ref_window[k])
                        chunk_frame = np.array(chunk_window[k])
                        
                        # 유클리드 거리의 역수를 유사도로 사용
                        distance = np.linalg.norm(ref_frame - chunk_frame)
                        similarity = 1.0 / (1.0 + distance)
                        similarities.append(similarity)
                    
                    if similarities:
                        avg_similarity = sum(similarities) / len(similarities)
                        best_score = max(best_score, avg_similarity)
            
            return best_score
            
        except Exception as e:
            logger.error(f"지문 비교 중 오류: {e}")
            return 0.0
    
    def detect_songs(self, audio_chunks: Generator[np.ndarray, Any, None], 
                    chunk_duration: int = 60) -> Generator[Dict[str, Any], None, None]:
        """
        오디오 청크에서 노래 시작 부분 감지
        
        Args:
            audio_chunks: 오디오 데이터 청크의 제너레이터
            chunk_duration: 각 청크의 지속 시간(초)
            
        Yields:
            Dict[str, Any]: 감지된 노래 정보 (id 및 시작 시간)
        """
        chunk_index = 0
        current_time = 0
        
        for audio_chunk in audio_chunks:
            logger.info(f"청크 {chunk_index} 분석 중 (시간: {current_time}초)")
            
            try:
                # 청크에서 지문 생성
                chunk_fingerprint = 
                
                # 참조 지문과 비교
                match_score = self._compare_fingerprints(chunk_fingerprint)
                logger.debug(f"청크 {chunk_index}의 일치 점수: {match_score}")
                
                # 일치 점수가 임계값을 넘으면 노래 감지로 판단
                if match_score >= self.sensitivity:
                    logger.info(f"노래 감지됨! 시간: {current_time}초, 일치 점수: {match_score}")
                    
                    # 감지 결과 반환
                    yield {
                        "id": 1,  # 항상 id=1 검사
                        "time": current_time,
                        "score": float(match_score)
                    }
                
                # 시간 및 인덱스 업데이트
                current_time += chunk_duration
                chunk_index += 1
                
            except Exception as e:
                logger.error(f"청크 {chunk_index} 처리 중 오류: {e}")
                # 오류 발생해도 다음 청크 계속 처리
                current_time += chunk_duration
                chunk_index += 1
                continue
                
def detect_songs_in_chunks(db_path: str, 
                          audio_chunks: Generator[np.ndarray, Any, None],
                          sample_rate: int = 44100, 
                          chunk_duration: int = 60,
                          sensitivity: float = 0.7) -> Generator[Dict[str, Any], None, None]:
    """
    오디오 청크에서 노래 감지하는 편의 함수
    
    Args:
        db_path (str): SQLite 데이터베이스 경로
        audio_chunks: 오디오 데이터 청크의 제너레이터
        sample_rate (int): 오디오 샘플 레이트
        chunk_duration (int): 각 청크의 지속 시간(초)
        sensitivity (float): 감지 민감도 (0.0 ~ 1.0)
        
    Yields:
        Dict[str, Any]: 감지된 노래 정보 (id 및 시작 시간)
    """
    detector = SongDetector(db_path, sample_rate, sensitivity)
    yield from detector.detect_songs(audio_chunks, chunk_duration)