"""
YouTube 오디오 추출 애플리케이션 메인 모듈
"""

from src.preprocess import preprocess_audio
from src.youtube_audio import YouTubeAudioExtractor


def main():
    """메인 실행 함수"""
    # 테스트할 YouTube URL
    # url = "https://www.youtube.com/watch?v=w-NM1UQ3HnU"
    url = "https://www.youtube.com/watch?v=_6E8SWFiz5M"
    start = "00:00:00"
    end = "00:47:00"

    print(f"URL: {url}")
    print(f"구간: {start} ~ {end}")

    print()
    print("YouTube 오디오 추출 시작")
    audio_bytes = downloadYoutubeAudio(url, start, end)

    print()
    print("YouTube 오디오 전처리 시작")
    preprocessed_audio, sampling_rate = preprocess_audio(audio_bytes)
    print(f"성공: 샘플링 레이트 {sampling_rate}")



def downloadYoutubeAudio(url, start, end):
    audio_data, content_type, title = YouTubeAudioExtractor.get_youtube_audio(
        url, start, end, audio_format="mp3"
    )

    if audio_data:
        print(f"성공: {title}")
        print(f"컨텐츠 타입: {content_type}")
        print(f"데이터 크기: {len(audio_data)} 바이트")
    else:
        print("오류: 오디오 구간 추출에 실패했습니다.")

    return audio_data


if __name__ == "__main__":
    main()
