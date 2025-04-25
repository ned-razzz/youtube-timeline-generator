import psutil

def monitor_memory():
    process = psutil.Process()
    memory_info = process.memory_info()
    current_memory =  memory_info.rss / (1024 * 1024)  # MB 단위
    print(f"[memory usage: {current_memory:.2f} MB]")

def monitor_system_memory():
    # 시스템 메모리 정보 가져오기
    memory = psutil.virtual_memory()
    
    # 메모리 정보 출력 (MB 단위)
    total_memory = memory.total / (1024 * 1024)  # 총 메모리
    available_memory = memory.available / (1024 * 1024)  # 사용 가능한 메모리
    used_memory = memory.used / (1024 * 1024)  # 사용 중인 메모리
    percent_used = memory.percent  # 사용 비율 (%)
    
    print(f"[시스템 메모리 정보] (사용 메모리 + 가용 메모리) / 전체 메모리")
    print(f"{used_memory:.0f}MB + {available_memory:.0f}MB / {total_memory:.2f} MB ({percent_used:.2f}%)")