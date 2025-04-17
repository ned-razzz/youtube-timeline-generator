"""
YouTube 오디오 추출 애플리케이션 메인 모듈
"""
from youtube_audio import YouTubeAudioExtractor

def main():
    """메인 실행 함수"""

    # 테스트할 YouTube URL
    url = "https://www.youtube.com/watch?v=_6E8SWFiz5M"
    start = "00:10:00"
    end = "00:40:00"
    
    print(f"YouTube 오디오 구간 추출 시작")
    print(f"URL: {url}")
    print(f"구간: {start} ~ {end}")
    
    # 메모리에서 처리하는 방법
    audio_data, content_type, title = YouTubeAudioExtractor.get_youtube_audio(
        url, start, end, audio_format="mp3"
    )
    
    if audio_data:
        print(f"성공: '{title}' 영상에서 오디오 구간을 추출했습니다.")
        print(f"컨텐츠 타입: {content_type}")
        print(f"데이터 크기: {len(audio_data)} 바이트")
    else:
        print("오류: 오디오 구간 추출에 실패했습니다.")
    
    # 파일 저장 데모
    output_file = "downloads/extracted_audio.mp3"
    with open(output_file, "wb") as f:
        f.write(audio_data)
    print(f"파일 저장 완료: {output_file}")

if __name__ == "__main__":
    main()