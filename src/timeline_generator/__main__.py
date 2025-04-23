import argparse
from pathlib import Path
from typing import Dict, List, Any
import traceback

from src.timeline_generator.types import convert_to_numba_dict
from src.utils.db_manager import DatabaseManager
from src.timeline_generator.read_audio import read_audio
from src.utils import formatter, memory_manager
from src.utils.chunk_consumer import consume_chunks
from .timeline_detector import analyze_timeline, detect_timeline

def get_fingerprints(worldcup_id: int) -> Dict[str, Any]:
    """
    지정된 월드컵 ID에 해당하는 노래 지문을 데이터베이스에서 로드합니다.
    
    Args:
        worldcup_id: 월드컵 ID
        
    Returns:
        Dict[str, Any]: {노래이름: 지문} 형태의 사전
        
    Raises:
        ValueError: 해당 월드컵 ID가 존재하지 않는 경우
    """
    sqlite_db = DatabaseManager()
    changpops = sqlite_db.load_changpops_by_worldcup(worldcup_id)

    if not changpops:
        raise ValueError(f"해당 worldcup id({worldcup_id})가 존재하지 않습니다.")
    
    fingerprints = {r.name: r.fingerprint for r in changpops}
    return fingerprints

def parse_arguments():
    """명령줄 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(description="대상 유튜브 오디오에서 노래 목록의 타임라인 감지")
    parser.add_argument("-a", "--audio_path", required=True, help="감지할 대상 오디오 경로")
    parser.add_argument("-w", "--worldcup", required=True, help="감지할 월드컵 ID")
    parser.add_argument("-ch", "--chunk", default=15, type=int, help="각 오디오 청크의 감지 크기 (초)")
    parser.add_argument("-hp", "--hop", default=5, type=int, help="다음 오디오 청크를 로드할 크기 (초)")
    parser.add_argument("-th", "--threshold", default=0.02, type=float, help="감지할 최소 유사도 임계값")
    
    return parser.parse_args()

def print_timeline_results(timelines: List[Dict[str, Any]]) -> None:
    """타임라인 결과를 출력합니다."""
    print()
    print("발견된 노래:")
    print(f"{'시작 시간':^15}{'노래 이름':^30}{'유사도':^15}")
    print("-" * 80)
    
    for timeline in timelines:
        start_time = timeline['estimated_start_time']
        song_name = timeline['song_name']
        similarity = timeline['similarity']
        
        # 시간을 HH:MM:SS 형식으로 변환
        time_str = formatter.format_time(start_time)
        
        print(f"{time_str:^15}{song_name:^30}{similarity:^15.4f}")

def main():
    """
    실제 영상에서 유튜브 타임라인을 생성합니다.
    """
    args = parse_arguments()

    # 파라미터 초기화
    audio_path = Path(args.audio_path).resolve()
    worldcup_id = int(args.worldcup)
    chunk_size = args.chunk
    hop_size = args.hop
    threshold = args.threshold
    
    # 초기 메모리 상태 확인
    memory_manager.monitor_memory()

    try:
        # 월드컵 노래 지문 로드
        print()
        fingerprints = get_fingerprints(worldcup_id)
        memory_manager.monitor_memory()
        
        # 오디오 파일 로드 및 타임라인 감지
        if not audio_path.is_file():
            raise FileNotFoundError(f"오류: 오디오 파일을 찾을 수 없습니다 - {audio_path}")
        
        audio_chunks = read_audio(audio_path, chunk_size, hop_size)
        timeline_chunks = detect_timeline(audio_chunks, fingerprints, chunk_size, threshold)
        
        # 타임라인 수집 및 분석
        timelines = []
        for timeline in timeline_chunks:
            timelines.append(timeline)
            memory_manager.monitor_memory()
            
        # 중복 제거 및 정렬
        # timelines = analyze_timeline(timelines)
        
        # 결과 출력
        print_timeline_results(timelines)
        
    except Exception as e:
        print(f"오류 발생: {e}")
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())