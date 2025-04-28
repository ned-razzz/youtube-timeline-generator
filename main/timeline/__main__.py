"""
YouTube 오디오 추출 애플리케이션 메인 모듈
"""
from dataclasses import dataclass
import sys
import traceback
import argparse
import gc

from src.timeline.read_audio import read_audio
from src.timeline.timeline_detector import TimelineDetector
from src.timeline.timeline_manager import print_not_detected, print_timelines
from src.utils.file_db import FileDB
from src.utils.formatter import TimeFormatter
from src.utils.memory_manager import MemoryMonitor
from src.youtube_download.audio import AudioDownloader

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

@dataclass
class AudioMetadata:
    name: str
    duration: int
    sample_rate: str

@handle_exception(msg="유튜브 오디오 파일을 받아오는 작업을 실패하였습니다")
def download_youtube(url, start, end):
    AudioDownloader.set_config(start=start, end=end)
    audio_data, audio_path = AudioDownloader.load_audio(url)
    if audio_data.size == 0:
        raise ValueError("오디오 다운로드 실패")
    name, duration, sample_rate = AudioDownloader.get_audio_metadata(audio_path)

    return audio_data, AudioMetadata(name, duration, sample_rate)

@handle_exception(msg="DB에서 월드컵 오디오 지문을 가져오는데 실패하였습니다")
def get_audioprints(worldcup_name: str):
    # DB 데이터 불러오기
    fingerprints = FileDB.load_audioprints(worldcup_name)
    if not fingerprints:
        raise ValueError(f"해당 worldcup id({worldcup_name})가 존재하지 않습니다.")
    # 데이터 변환
    return fingerprints

@handle_exception(msg="오디오 분석 및 타임라인 생성 작업을 실패하였습니다")
def generate_timelines(audio_data, 
                       metadata: AudioMetadata, 
                       fingerprints, 
                       chunk_size, hop_size, threshold):
    # 오디오 지연 로딩
    audio_chunks = read_audio(audio_data,
                              metadata.duration, 
                              metadata.sample_rate, 
                              chunk_size, 
                              hop_size)
    
    # 오디오에서 타임라인 탐지
    timeline_chunks = TimelineDetector.detect_timeline(audio_chunks, 
                                                       fingerprints, 
                                                       hop_size, 
                                                       threshold)
    
    # 최종 타인라인 데이터 정리
    timelines = TimelineDetector.analyze_timeline(timeline_chunks)
    return timelines

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
    parser.add_argument("-th", "--threshold", default=0.001, type=float, help="감지할 최소 유사도 임계값")
    parser.add_argument("--trace", action="store_true", help="오류 로그 반환 설정")
    args = parser.parse_args()

    # 오류 로그 출력 설정
    global IF_TRACE
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
    print(f"\t이름: {metadata.name}")
    print(f"\t길이: {metadata.duration}초")
    print(f"\t샘플레이트: {metadata.sample_rate}")
    MemoryMonitor.monitor_system()

    print()
    print("DB에서 오디오 지문 불러오는 중...")
    audioprints = get_audioprints(args.worldcup)
    MemoryMonitor.monitor_system()

    print("\n")
    print("유튜브 타임라인 생성 중...")
    print(f"\t 청크 크기: {args.chunk_size}초")
    print(f"\t 청크 진행 크기: {args.hop_size}초")
    print()
    timelines = generate_timelines(audio_data,
                                   metadata, 
                                   audioprints, 
                                   args.chunk_size, 
                                   args.hop_size, 
                                   args.threshold)
    MemoryMonitor.monitor_system()
    
    print("\n")
    print("유튜브 타임라인을 출력합니다.")
    print_timelines(timelines, TimeFormatter.format_time_to_int(args.start_time), True)
    print_timelines(timelines, TimeFormatter.format_time_to_int(args.start_time))
    print_not_detected(audioprints, timelines)

if __name__ == "__main__":
    try:
        main()
    finally:
        AudioDownloader.clean_out()