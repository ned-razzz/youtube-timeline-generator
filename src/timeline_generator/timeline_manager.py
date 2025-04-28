from datetime import datetime
import json
from typing import List
from matplotlib import pyplot as plt

from src.utils.formatter import TimeFormatter
from src.utils.types import TimelineData

def print_timelines(timelines, audio_start_offset):
    """타임라인 결과를 출력합니다."""
    print("-" * 80)
    print("발견된 노래:")
    for timeline in timelines:
        start_seconds = timeline['start_time']
        song_name = timeline['song_name']
        similarity = timeline['similarity']
        
        # 시간을 HH:MM:SS 형식으로 변환
        time_str = TimeFomatter.format_time_to_str(audio_start_offset + start_seconds)
        
        print(f"{song_name} {time_str} {similarity:.3f}")
    print(f"프로그램으로 돌려서 부정확할 수 있습니다: {len(timelines)}개")

def analyze_timeline(timelines: List[TimelineData]) -> List[TimelineData]:
    """감지된 타임라인을 분석하여 중복을 제거하고 시간순으로 정렬합니다."""
    # 유사도 높은 순으로 정렬
    timelines.sort(key=lambda x: x["start_time"])

    # 중복 제거 (같은 노래가 여러 윈도우에서 발견될 수 있음)
    filtered_timelines = []
    saved_songs = set()
    
    for timeline_data in timelines:
        name = timeline_data["song_name"]
        time = timeline_data["start_time"]
        # similarity = timeline_data["similarity"]
        
        # 이미 감지된 노래이면 제외
        for saved_name, saved_time in saved_songs:
            if name == saved_name and time == saved_time:
                continue
        
        filtered_timelines.append(timeline_data)
        saved_songs.add((name, time))
    
    # 시작 시간 순으로 정렬
    filtered_timelines.sort(key=lambda x: x["start_time"])
    
    return filtered_timelines