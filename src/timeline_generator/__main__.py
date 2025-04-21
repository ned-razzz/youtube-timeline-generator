import argparse
from pathlib import Path
import essentia.standard as es

from src.timeline_generator.read_audio import read_audio

from src.utils import db_manager, formatter, memory_manager
from src.utils.chunk_consumer import consume_chunks
from .timeline_detector import analyze_timeline, detect_timeline

def get_fingerprints(worldcup_id: int):
    sqlite_db = db_manager.DatabaseManager()
    query_results = sqlite_db.load_changpops_by_worldcup(worldcup_id)
    if not query_results:
        raise ValueError("해당 worldcup id가 존재하지 않습니다.")

    fingerprints = {}
    for data in query_results:
        fingerprints[data['name']] = {
            "constellation_map": data['constellation_map'],  
            "peak_pairs": data['peak_pairs'],   
            "total_frames": data['total_frames'],
            "duration": data['duration']
        }
    return fingerprints

def main():
    """
    실제 영상에서 유튜브 타임라인 생성
    """
    parser = argparse.ArgumentParser(description="detect timeline of song list from target youtube audio")
    parser.add_argument("-a", "--audio_path", required=True, help="target audio path to ")
    parser.add_argument("-w", "--worldcup", required=True, help="worldcup name to detect")
    parser.add_argument("-ch", "--chunk", default=15, help="size to detect each audio chunks")
    parser.add_argument("-hp", "--hop", default=5, help="load size to detect next audio chuncks")
    parser.add_argument("-t", "--threshold", default=0.15, help="min similarity threshold to detect")
    args = parser.parse_args()

    # 파라미터 초기화
    audio_path = Path(args.audio_path).resolve()
    worldcup_id = int(args.worldcup)
    chunk_size = int(args.chunk)
    hop_size = int(args.hop)
    threshold = int(args.threshold)
    
    # 초기 메모리 상태 확인
    memory_manager.monitor_memory()

    # 월드컵 노래 지문 로드
    fingerprints = get_fingerprints(worldcup_id)
    memory_manager.monitor_memory()
    print()
    
    # 오디오 파일 로드
    if not audio_path.is_file():
        print(f"오류: 오디오 파일을 찾을 수 없습니다 - {audio_path}")
        exit()

    audio_chunks = read_audio(audio_path, chunk_size, hop_size)
    timeline_chunks = detect_timeline(audio_chunks, fingerprints, chunk_size)
    memory_manager.monitor_memory()
    
    timelines = []
    for timeline in timeline_chunks:
        timelines.append(timeline)
    timelines = analyze_timeline(timelines)
          
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
        
        # 수정된 형식 지정자
        print(f"{time_str:^15}{song_name:^30}{similarity:^15.4f}")


if __name__ == "__main__":
    main()