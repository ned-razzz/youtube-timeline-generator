"""
YouTube 오디오 추출 애플리케이션 메인 모듈
"""
import traceback
import soundfile as sf
from src.file_handle import read_chunks, save_audio
from src.preprocess import preprocess_audio
from src.remove_vocals import remove_vocals
from src.youtube_audio import download_youtube_audio

# 테스트할 YouTube URL
url = "https://www.youtube.com/watch?v=w-NM1UQ3HnU"
# url = "https://www.youtube.com/watch?v=_6E8SWFiz5M"
start = "00:14:14"
end = "00:19:00"

def main():
    """메인 실행 함수"""
    print("=======================================")
    print(f"URL: {url}")
    print(f"구간: {start} ~ {end}")

    try:
        print("YouTube 오디오 추출...")
        audio_path, file_name = download_youtube_audio(
            url, start, end, audio_format="wav"
        )        
        print(audio_path)
        
        info = sf.info(audio_path)
        sample_rate= info.samplerate

        audio_chunks = read_chunks(audio_path)

        vocal_removeds = remove_vocals(audio_chunks)

        # print("오디오 저장...")
        save_audio(vocal_removeds, sample_rate, file_name)

        # # Consume the generator to process all chunks
        # for chunk in vocal_removeds:
        #     print(f"오디오 청크 형태: {chunk.shape}, 타입: {chunk.dtype}")

        print()
        print("작업이 완료되었습니다.")

    except Exception as e:
        print(f"유튜브 타임라인 생성을 실패하였였습니다:")
        print(e)
        traceback.print_exc()

if __name__ == "__main__":
    main()
