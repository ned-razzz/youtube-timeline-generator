import argparse
from pathlib import Path
import essentia.standard as es

from ..utils import db_manager, formatter
from .timeline_detector import detect_timeline


def main():
    """
    실제 영상에서 유튜브 타임라인 생성
    """
    parser = argparse.ArgumentParser(description="detect timeline of song list from target youtube audio")
    parser.add_argument("-a", "--audio_path", required=True, help="target audio path to ")
    parser.add_argument("-w", "--worldcup", required=True, help="worldcup name to detect")
    parser.add_argument("-ws", "--window_size", default=15.0, help="size to detect each audio chunks")
    parser.add_argument("-hs", "--hop_size", default=5.0, help="load size to detect next audio chuncks")
    parser.add_argument("-t", "--threshold", default=0.15, help="min similarity threshold to detect")
    args = parser.parse_args()
    
    # 오디오 파일 로드
    audio_path = Path(args.audio_path).resolve()
    audio_loader = es.MonoLoader(filename=str(audio_path))
    audio_data = audio_loader()
    print("오디오 파일 로드.")

    # 월드컵 노래 지문 로드
    sqlite_db = db_manager.DatabaseManager()
    query_datas = sqlite_db.load_changpops_by_worldcup(args.worldcup)
    fingerprints = {}
    for data in query_datas:
        fingerprints[data['name']] = {
            "constellation_map": data['constellation_map'],  
            "peak_pairs": data['peak_pairs'],   
            "total_frames": data['total_frames'],
            "duration": data['duration']
        }
    print("월드컵 지문 데이터 로드.")

    print("노래 탐지 시작...")
    timelines = detect_timeline(long_audio=audio_data, 
                                     detect_fingerprints=fingerprints, 
                                     window_size=args.window_size, 
                                     hop_size=args.hop_size, 
                                     similarity_threshold=args.threshold)
    print("영상 타임라인 탐지 완료.")


    if not timelines:
        print("영상에서 아무 노래도 감지하지 못했습니다.")
        return
    
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