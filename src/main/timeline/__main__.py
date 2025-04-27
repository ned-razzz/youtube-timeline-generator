"""
YouTube 오디오 추출 애플리케이션 메인 모듈
"""
from dataclasses import dataclass
import sys
import traceback
import argparse
import gc

from src.timeline_generator.read_audio import generate_audio_chunks
from src.timeline_generator.timeline_detector import analyze_timeline, detect_timeline
from src.timeline_generator.write_timelines import print_timelines
from src.utils.file_db import FileDB
from src.utils.formatter import Fommatter
from src.utils.memory_manager import MemoryMonitor
from src.youtube_downloader.audio_loader import download_youtube_audio

IF_TRACE = False

# 각 작업 예외 처리 데코레이터 패턴
def handle_exception(msg):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"{msg}: {e}")
                if IF_TRACE:
                    traceback.print_exc()
                sys.exit()
            finally:
                gc.collect()
        return wrapper
    return decorator

@handle_exception(msg="유튜브 오디오 파일을 받아오는 작업을 실패하였습니다")
def download_youtube(url, start, end):
    audio_data, metadata = download_youtube_audio(
        url, start, end
    )
    return audio_data, metadata

@handle_exception(msg="DB에서 월드컵 오디오 지문을 가져오는데 실패하였습니다")
def get_fingerprints(worldcup_name: str):
    # DB 데이터 불러오기
    fingerprints = FileDB.load_audioprints(worldcup_name)
    if not fingerprints:
        raise ValueError(f"해당 worldcup id({worldcup_name})가 존재하지 않습니다.")
    # 데이터 변환
    return fingerprints

@handle_exception(msg="오디오 분석 및 타임라인 생성 작업을 실패하였습니다")
def generate_timelines(audio_data, metadata, fingerprints, chunk_size, hop_size, threshold):
    audio_chunks = generate_audio_chunks(audio_data, metadata, chunk_size, hop_size)
    timeline_chunks = detect_timeline(audio_chunks, fingerprints, hop_size, threshold)
    
    # 타임라인 수집 및 분석
    timelines = []
    for timeline in timeline_chunks:
        timelines.append(timeline)
        
    # 중복 제거 및 정렬
    timelines = analyze_timeline(timelines)
    return timelines

def print_timelines(timelines, audio_start_seconds):
    """타임라인 결과를 출력합니다."""
    print("발견된 노래:")
    print(f"{'노래 이름':^30}{'시작 시간':^10}{'유사도':^10}")
    print("-" * 80)
    for timeline in timelines:
        start_seconds = timeline['estimated_start_time']
        song_name = timeline['song_name']
        similarity = timeline['similarity']
        
        # 시간을 HH:MM:SS 형식으로 변환
        time_str = Fommatter.format_time_to_str(audio_start_seconds + start_seconds)
        
        print(f"{song_name} {time_str}")
    print(f"프로그램으로 돌려서 부정확할 수 있습니다: {len(timelines)}개")

# 메인 함수 인자
@dataclass
class TypedArgs:
    youtube_url: str
    worldcup: str
    start_time: str
    end_time: str
    chunk_size: int
    hop_size: int
    threshold: float

def parse_arguments():
    """명령줄 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(description="유튜브 영상에서 노래 목록의 타임라인 감지")
    parser.add_argument("-u", "--url", type=str, help="월드컵 영상 YouTube URL")
    parser.add_argument("-w", "--worldcup", required=True, help="감지할 월드컵 이름")
    parser.add_argument("-st", "--start", type=str, default="00:00:00", help="시작 시간 (HH:MM:SS)")
    parser.add_argument("-ed", "--end", type=str, default="00:10:00", help="종료 시간 (HH:MM:SS)")
    parser.add_argument("-ch", "--chunk", default=60, type=int, help="각 오디오 청크의 감지 크기 (초)")
    parser.add_argument("-hp", "--hop", default=30, type=int, help="다음 청크 진행 크기")
    parser.add_argument("-th", "--threshold", default=0.003, type=float, help="감지할 최소 유사도 임계값")
    parser.add_argument("--trace", action="store_true", help="오류 로그 반환 설정")
    args = parser.parse_args()

    # 오류 로그 출력 설정
    IF_TRACE = args.trace

    return TypedArgs(youtube_url=args.url, 
                     worldcup=args.worldcup, 
                     start_time=args.start,
                     end_time=args.end,
                     chunk_size=args.chunk,
                     hop_size=args.hop,
                     threshold=args.threshold)

def main():
    """메인 실행 함수"""
    args = parse_arguments()

    # 시작 메모리
    MemoryMonitor.monitor_system()

    print()
    print("영상 오디오 다운로드 중...")
    print(f"URL: {args.youtube_url}")
    print(f"구간: {args.start_time} ~ {args.end_time}")
    audio_data, metadata = download_youtube(args.youtube_url, 
                                            args.start_time, 
                                            args.end_time)

    print(f"- 오디오 정보:")
    print(f"\t이름: {metadata['name']}")
    print(f"\t길이: {metadata['duration']}초")
    print(f"\t샘플레이트: {metadata['sample_rate']}")
    MemoryMonitor.monitor_system()

    print()
    print("DB에서 오디오 지문 불러오는 중...")
    fingerprints = get_fingerprints(args.worldcup)
    MemoryMonitor.monitor_system()

    print("\n\n")
    print("유튜브 타임라인 생성 중...")
    print(f"\t 청크 크기: {args.chunk_size}초")
    print(f"\t 청크 진행 크기: {args.hop_size}초")
    print()
    timelines = generate_timelines(audio_data, 
                                   metadata, 
                                   fingerprints, 
                                   args.chunk_size, 
                                   args.hop_size, 
                                   args.threshold)
            
    print("유튜브 타임라인을 출력합니다.")
    timelines = analyze_timeline(timelines)
    print_timelines(timelines, Fommatter.format_time_to_int( args.start_time))

if __name__ == "__main__":
    main()