"""
YouTube 오디오 추출 애플리케이션 메인 모듈
"""
from pathlib import Path
import sys
import traceback
import argparse
import gc

from src.timeline_generator.read_audio import read_audio
from src.timeline_generator.timeline_detector import analyze_timeline, detect_timeline
from src.timeline_generator.write_timelines import print_timeline_results
from src.utils.db_manager import DatabaseManager
from src.utils.formatter import deformat_time, format_time
from src.youtube_downloader.audio_downloader import download_youtube_audio
from src.utils.memory_manager import monitor_memory

def parse_arguments():
    """명령줄 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(description="유튜브 영상에서 노래 목록의 타임라인 감지")
    parser.add_argument("-w", "--worldcup", required=True, help="감지할 월드컵 ID")
    parser.add_argument("-u", "--url", type=str, help="월드컵 영상 YouTube URL")
    parser.add_argument("-st", "--start", type=str, default="00:00:00", help="시작 시간 (HH:MM:SS)")
    parser.add_argument("-ed", "--end", type=str, default="00:10:00", help="종료 시간 (HH:MM:SS)")
    parser.add_argument("-ch", "--chunk", default=60, type=int, help="각 오디오 청크의 감지 크기 (초)")
    parser.add_argument("-th", "--threshold", default=0.01, type=float, help="감지할 최소 유사도 임계값")
    parser.add_argument("--trace", action="store_true", help="오류 로그 반환 설정")
    return parser.parse_args()

def download_youtube(url, start, end, if_trace):
    try:
        audio_path, _ = download_youtube_audio(
            url, start, end, audio_format="wav"
        )
        print(f"유튜브 오디오를 다운로드 받았습니다: {audio_path}")
        return audio_path
    except Exception as e:
        print(f"유튜브 오디오 파일을 받아오는 작업을 실패하였습니다:\n{e}")
        if if_trace:
            traceback.print_exc()
        sys.exit()
    finally:
        gc.collect()

def get_fingerprints(worldcup_id: int, if_trace):
    try:
        # DB 데이터 불러오기
        sqlite_db = DatabaseManager()
        changpops = sqlite_db.load_changpops_by_worldcup(worldcup_id)
        if not changpops:
            raise ValueError(f"해당 worldcup id({worldcup_id})가 존재하지 않습니다.")
        # 데이터 변환
        fingerprints = {r.name: r.fingerprint for r in changpops}
        return fingerprints
    except Exception as e:
        print(f"DB에서 월드컵 오디오 지문을 가져오는데 실패하였습니다:\n{e}")
        if if_trace:
            traceback.print_exc()
        sys.exit()
    finally:
        gc.collect()

def generate_timelines(audio_path, fingerprints, chunk_size, threshold, if_trace):
    try: 
        audio_path = Path(audio_path)
        audio_chunks = read_audio(audio_path, chunk_size, chunk_size)
        timeline_chunks = detect_timeline(audio_chunks, fingerprints, chunk_size, threshold)
        
        # 타임라인 수집 및 분석
        timelines = []
        for timeline in timeline_chunks:
            timelines.append(timeline)
            monitor_memory()
            
        # 중복 제거 및 정렬
        timelines = analyze_timeline(timelines)

        return timelines
    except Exception as e:
        print(f"오디오 분석 및 타임라인 생성 작업을 실패하였습니다:\n{e}")
        if if_trace:
            traceback.print_exc()
        sys.exit()
    finally:
        gc.collect()

def print_timeline_results(timelines, start_time) -> None:
    """타임라인 결과를 출력합니다."""
    start_seconds = deformat_time(start_time)

    print("발견된 노래:")
    print(f"{'노래 이름':^20}{'시작 시간':^10}{'유사도':^10}")
    print("-" * 80)
    for timeline in timelines:
        start_time = timeline['estimated_start_time']
        song_name = timeline['song_name']
        similarity = timeline['similarity']
        
        # 시간을 HH:MM:SS 형식으로 변환
        time_str = format_time(start_time + start_seconds)
        
        print(f"{song_name:^20}{time_str:^10}{similarity*10:^10.2f}")
    print("프로그램으로 돌려서 부정확할 수 있습니다.")

def main():
    """메인 실행 함수"""
    args = parse_arguments()

    # 파라미터 초기화
    youtube_url = args.url
    start_time = args.start
    end_time = args.end
    worldcup_id = int(args.worldcup)
    chunk_size = args.chunk
    threshold = args.threshold
    if_trace_error = args.trace

    print("영상 오디오 다운로드 중...")
    print(f"URL: {youtube_url}")
    print(f"구간: {start_time} ~ {end_time}")
    audio_path = download_youtube(youtube_url, start_time, end_time, if_trace_error)
    monitor_memory()

    print("DB에서 오디오 지문 불러오는 중...")
    fingerprints = get_fingerprints(worldcup_id, if_trace_error)
    monitor_memory()

    print("유튜브 타임라인 생성 중...")
    timelines = generate_timelines(audio_path, fingerprints, chunk_size, threshold, if_trace_error)
    monitor_memory()
            
    print("유튜브 타임라인을 출력합니다.")
    print_timeline_results(timelines, start_time)

if __name__ == "__main__":
    main()