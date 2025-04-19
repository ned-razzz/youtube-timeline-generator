import os
from pathlib import Path

# 상대 경로를 절대 경로로 변환
audio_path = Path("audio").resolve()

# 경로 확인
print(f"Absolute path: {audio_path}")

# 해당 경로가 존재하는지 확인
if audio_path.exists():
    print("The path exists!")
else:
    print("The path does not exist.")