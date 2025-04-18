"""
YouTube 오디오 추출 애플리케이션 메인 모듈
"""

import traceback
from src.file_handle import read_chunks, save_audio
from src.preprocess import preprocess_audio
from src.remove_vocals import remove_vocals
from src.youtube_audio import download_youtube_audio

# 테스트할 YouTube URL
# url = "https://www.youtube.com/watch?v=w-NM1UQ3HnU"
url = "https://www.youtube.com/watch?v=_6E8SWFiz5M"
start = "00:00:00"
end = "00:10:00"

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

        chunks = read_chunks(audio_path)

        # print("오디오 전처리...")
        preprocessed_chunks = preprocess_audio(chunks)

        # print("오디오 저장...")
        save_audio(preprocessed_chunks, file_name)

        # # Consume the generator to process all chunks
        # all_chunks = []
        # for chunk in preprocessed_chunks:
        #     print("process")
        #     all_chunks.append(chunk)

        print()
        print("작업이 완료되었습니다.")

        # print()
        # print("YouTube 오디오 전처리...")
        # preprocessed_audio = preprocess_audio(audio_chunk)
        # print(f"성공")
        
        # result_bytes = remove_vocals(preprocessed_audio, 120)
        
        # output_file = "test/instrumental.wav"
        # with open(output_file, 'wb') as f:
        #     f.write(result_bytes)
            
        # print(f"보컬 제거 완료! 결과가 '{output_file}'에 저장되었습니다.")
    except Exception as e:
        print(f"유튜브 타임라인 생성을 실패하였였습니다:")
        print(e)
        traceback.print_exc()

if __name__ == "__main__":
    main()
