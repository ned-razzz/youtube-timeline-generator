from datetime import datetime
import json
from matplotlib import pyplot as plt
import numpy as np
from collections import Counter

def handle_timelines(timelines, audio_data):
    # 결과 출력 부분의 오류 수정
    if timelines:
        print("\n발견된 노래:")
        print("-" * 80)
        print(f"{'시작 시간':^15}{'노래 이름':^30}{'유사도':^15}")
        print("-" * 80)
        
        for result in timelines:
            start_time = result['estimated_start_time']
            song_name = result['song_name']
            similarity = result['similarity']
            
            # 시간을 MM:SS 형식으로 변환
            minutes = int(start_time // 60)
            seconds = int(start_time % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            
            # 수정된 형식 지정자
            print(f"{time_str:^15}{song_name:^30}{similarity:^15.4f}")
        
        # 결과 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"song_detection_result_{timestamp}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(timelines, f, indent=2)
        
        print(f"\n결과가 {result_file}에 저장되었습니다.")
        
        # 결과 시각화
        plt.figure(figsize=(12, 6))
        
        # 긴 오디오의 총 길이
        total_duration = len(audio_data) / 44100  # 샘플링 레이트 44.1kHz 가정
        
        for i, result in enumerate(timelines):
            start_time = result['estimated_start_time']
            song_name = result['song_name']
            similarity = result['similarity']
            
            # 색상은 유사도에 따라 결정 (높을수록 진한 색)
            color_intensity = 0.3 + 0.7 * similarity
            color = (0, color_intensity, 0)
            
            # 선과 텍스트로 시작 시간 표시
            plt.axvline(x=start_time, color=color, linestyle='-', linewidth=2)
            plt.text(start_time, i % 5 + 1, f"{song_name} ({similarity:.2f})", 
                    rotation=45, ha='right', fontsize=8)
        
        plt.xlim(0, total_duration)
        plt.ylim(0, 6)
        plt.xlabel('시간 (초)')
        plt.title('발견된 노래 시작 지점')
        plt.grid(True, alpha=0.3)
        plt.yticks([])
        
        # X축 틱을 MM:SS 형식으로 변환
        def format_time(x, pos):
            minutes = int(x // 60)
            seconds = int(x % 60)
            return f"{minutes:02d}:{seconds:02d}"
        
        plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(format_time))
        
        # 이미지 저장
        plt.tight_layout()
        plt.savefig(f"song_detection_visualization_{timestamp}.png", dpi=300)
        print(f"시각화 이미지가 song_detection_visualization_{timestamp}.png에 저장되었습니다.")
        
        # 이미지 표시
        plt.show()
    else:
        print("\n노래를 찾을 수 없습니다.")