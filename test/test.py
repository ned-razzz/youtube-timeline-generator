from spleeter.separator import Separator
import soundfile as sf

# Spleeter 모델 로드 (예: 2stems)
separator = Separator("spleeter:2stems")

# 오디오 파일을 waveform으로 로드
audio, sample_rate = sf.read(
    "downloads/눈물나는_창팝__리미제라블__몰아보기_000000_000100.wav"
)

# 오디오 분리 실행 (딕셔너리 반환)
prediction = separator.separate(audio)

# 결과 접근 예시
vocals = prediction["vocals"]
accompaniment = prediction["accompaniment"]
print(accompaniment)
