import numpy as np
from typing import Dict, Optional

def find_song_with_fingerprint(
    audio_fingerprint: np.ndarray,
    reference_fingerprints: Dict[str, np.ndarray],
    threshold: float = 0.7
) -> Optional[str]:
    """
    단일 오디오 지문을 사용하여 매칭되는 노래를 찾습니다.
    
    Args:
        audio_fingerprint (np.ndarray): 
            분석할 오디오의 지문
        reference_fingerprints (Dict[str, np.ndarray]): 
            참조 노래 지문 딕셔너리 {노래_이름: 지문}
        threshold (float, optional): 
            매칭 임계값 (0.0~1.0). 기본값 0.7.
            
    Returns:
        Optional[str]: 찾은 노래 이름. 없으면 None.
    """
    if audio_fingerprint is None or not reference_fingerprints:
        return None
    
    best_match = None
    best_similarity = 0.0
    
    # 참조 지문과 매칭
    list = {}
    for song_name, ref_fp in reference_fingerprints.items():
        # 지문 유사도 계산
        similarity = compute_fingerprint_similarity(audio_fingerprint, ref_fp)
        list[song_name] = similarity
        
        # 임계값 이상이고 지금까지 찾은 것보다 더 유사한 경우 업데이트
        # if similarity >= threshold and similarity > best_similarity:
        #     best_match = song_name
        #     best_similarity = similarity
    
    return list

def compute_fingerprint_similarity(fp1: np.ndarray, fp2: np.ndarray) -> float:
    """2D 행렬 간의 코사인 유사도 계산 (Frobenius 내적 사용)"""
    # 행렬 크기가 다른 경우 처리
    min_rows = min(fp1.shape[0], fp2.shape[0])
    min_cols = min(fp1.shape[1], fp2.shape[1])
    
    m1_subset = fp1[:min_rows, :min_cols]
    m2_subset = fp2[:min_rows, :min_cols]
    
    # Frobenius 내적 계산
    frobenius_product = np.sum(m1_subset * m2_subset)
    norm_m1 = np.sqrt(np.sum(m1_subset**2))
    norm_m2 = np.sqrt(np.sum(m2_subset**2))
    
    # 0으로 나누기 방지
    if norm_m1 == 0 or norm_m2 == 0:
        return 0.0
        
    similarity = frobenius_product / (norm_m1 * norm_m2)
    
    # 유사도 범위를 0~1로 제한
    return max(0.0, min(1.0, similarity))

import numpy as np
from utils.db_manager import DatabaseManager

db_manager = DatabaseManager()

# id=1인 노래의 지문 가져오기
results = db_manager.load_changpops_by_worldcup(22)
if not results:
    raise ValueError("노래를 데이터베이스에서 찾을 수 없습니다.")

audio = db_manager.load_changpop_by_id(50)

slist = {}
for result in results:
    slist[result['name']] = result['fingerprint']

simul = find_song_with_fingerprint(audio['fingerprint'], slist)
print(simul)