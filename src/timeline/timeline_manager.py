from typing import Dict, Generator, List

from src.utils.formatter import TimeFormatter
from src.utils.types import TimelineData

def print_timelines(timelines: List[TimelineData], start_offset, if_data = False):
    """타임라인 결과를 출력합니다."""
    print("-" * 80)
    print(f"발견된 노래 {len(timelines)}개:")
    for timeline in timelines:
        # 시간을 HH:MM:SS 형식으로 변환
        time_str = TimeFormatter.format_time_to_str(start_offset + timeline.start_time)
        
        if if_data:
            print(f"{timeline.name} {time_str} {timeline.similarity:.3f}")
        else:
            print(f"{timeline.name} {time_str}")

def print_not_detected(audioprints: list, timelines: List[TimelineData]):
    # 타인라인 탐지한 오디오 이름 리스트
    detected_audios = [t.name for t in timelines]

    # 오디오 목록 중에서 타임라인 탐지 못한 오디오 찾기
    not_detected = [name for name in audioprints.keys() if name not in detected_audios]

    print("-" * 80)
    print("타임라인 탐지 못한 오디오")
    for audio_name in not_detected:
        print(audio_name, end=", ")
    print()
