"""
YouTube 오디오 추출 애플리케이션 메인 모듈
"""
import traceback
import argparse
import psutil
import gc

from .audio_downloader import download_youtube_audio

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="YouTube 오디오에서 보컬 제거 도구")
    parser.add_argument("--url", type=str, help="YouTube URL")
    parser.add_argument("--start", type=str, default="00:00:00", help="시작 시간 (HH:MM:SS)")
    parser.add_argument("--end", type=str, default="00:10:00", help="종료 시간 (HH:MM:SS)")
    parser.add_argument("--chunk-size", type=int, default=60, 
                        help="청크 크기(초), 메모리 부족 시 줄이세요 (기본값: 30)")
    parser.add_argument("--input-file", type=str, help="로컬 오디오 파일 경로 (YouTube 대신 사용)")
    parser.add_argument("--output-format", type=str, default="wav", help="출력 포맷 (wav, mp3)")
    
    args = parser.parse_args()
    
    print("=======================================")
    if args.input_file:
        print(f"로컬 파일: {args.input_file}")
    else:
        print(f"URL: {args.url}")
        print(f"구간: {args.start} ~ {args.end}")
    print(f"청크 크기: {args.chunk_size}초")
    
    try:
        # 메모리 모니터링 설정
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 * 1024)
        print(f"시작 메모리 사용량: {initial_memory:.2f} MB")
        
        # YouTube에서 다운로드
        print("YouTube 오디오 추출...")
        audio_path, file_name = download_youtube_audio(
            args.url, args.start, args.end, audio_format="wav"
        )
        print(f"처리할 오디오 파일: {audio_path}")

    except Exception as e:
        print(f"유튜브 타임라인 생성을 실패하였습니다: {e}")
        traceback.print_exc()
    finally:
        # 강제 메모리 정리
        gc.collect()

if __name__ == "__main__":
    main()