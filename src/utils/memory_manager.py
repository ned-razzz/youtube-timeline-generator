import psutil

def monitor_memory():
    process = psutil.Process()
    memory_info = process.memory_info()
    current_memory =  memory_info.rss / (1024 * 1024)  # MB 단위
    print(f"Current memory usage: {current_memory:.2f} MB")