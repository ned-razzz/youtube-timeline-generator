from src.utils import formatter

def print_timeline_results(timelines) -> None:
    """타임라인 결과를 출력합니다."""
    print()
    print("발견된 노래:")
    print(f"{'노래 이름':^20}{'시작 시간':^10}{'유사도':^10}")
    print("-" * 80)
    
    for timeline in timelines:
        start_time = timeline['estimated_start_time']
        song_name = timeline['song_name']
        similarity = timeline['similarity']
        
        # 시간을 HH:MM:SS 형식으로 변환
        time_str = formatter.format_time(start_time)
        
        print(f"{song_name:} {time_str:} {similarity*10:.2f}%")