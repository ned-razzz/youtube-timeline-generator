"""
YouTube 오디오 추출 애플리케이션 메인 모듈
"""
import traceback
import soundfile as sf
import argparse
import sys
import os
import psutil
import gc
from pathlib import Path
from .file_handler import read_chunks, save_audio
from .vocal_remover import remove_vocals
from .audio_downloader import download_youtube_audio

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="YouTube 오디오에서 보컬 제거 도구")
    parser.add_argument("--url", type=str, help="YouTube URL")
    parser.add_argument("--start", type=str, default="00:00:00", help="시작 시간 (HH:MM:SS)")
    parser.add_argument("--end", type=str, help="종료 시간 (HH:MM:SS)")
    parser.add_argument("--chunk-size", type=int, default=60, 
                        help="청크 크기(초), 메모리 부족 시 줄이세요 (기본값: 30)")
    parser.add_argument("--input-file", type=str, help="로컬 오디오 파일 경로 (YouTube 대신 사용)")
    parser.add_argument("--output-format", type=str, default="wav", help="출력 포맷 (wav, mp3)")
    
    args = parser.parse_args()
    
    # 명령줄 인수가 없으면 기본값 설정
    if len(sys.argv) == 1:
        # 기본 YouTube URL (테스트용)
        args.url = "https://www.youtube.com/watch?v=w-NM1UQ3HnU"
        args.start = "00:14:14"
        args.end = "00:19:00"
    
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
        
        audio_path = None
        file_name = None
        
        if args.input_file:
            # 로컬 파일 사용
            audio_path = args.input_file
            file_name = os.path.basename(audio_path)
        else:
            # YouTube에서 다운로드
            print("YouTube 오디오 추출...")
            audio_path, file_name = download_youtube_audio(
                args.url, args.start, args.end, audio_format="wav"
            )
            
        print(f"처리할 오디오 파일: {audio_path}")
        
        # 오디오 파일 정보 확인
        info = sf.info(audio_path)
        sample_rate = info.samplerate
        
        # 메모리 상태 로깅
        print(f"다운로드 후 메모리 사용량: {process.memory_info().rss / (1024 * 1024):.2f} MB")
        
        # 청크 단위로 파일 읽기
        print(f"청크 크기 {args.chunk_size}초로 오디오 파일 읽는 중...")
        audio_chunks = read_chunks(audio_path, chunk_size_seconds=args.chunk_size)
        
        # 보컬 제거 처리
        print("보컬 제거 처리 중...")
        vocal_removed_chunks = remove_vocals(audio_chunks)
        
        # 처리된 오디오 저장
        print("처리된 오디오 저장 중...")
        save_audio(vocal_removed_chunks, file_name)
        
        # 최종 메모리 상태
        final_memory = process.memory_info().rss / (1024 * 1024)
        print(f"최종 메모리 사용량: {final_memory:.2f} MB (변화: {final_memory - initial_memory:.2f} MB)")
        
        print("\n작업이 완료되었습니다.")
        print(f"결과 파일: output/instrumental_{file_name}")

    except Exception as e:
        traceback.print_exc()
        print(f"유튜브 타임라인 생성을 실패하였습니다:")
        print(e)
    finally:
        # 강제 메모리 정리
        gc.collect()

if __name__ == "__main__":
    main()