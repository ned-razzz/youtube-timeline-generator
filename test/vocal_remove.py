from src.remove_vocals import remove_vocals


with open("test/song.mp3", "rb") as f:
    audio_bytes = f.read()

# 보컬 제거 및 배열 데이터로 받기
instrumental = remove_vocals(audio_bytes)

# 파일로 저장하기
output_filename = "instrumental.wav"
with open(output_filename, "wb") as f:
    f.write(instrumental)

print(f"파일이 저장되었습니다: {output_filename}")