import os
import numpy as np
import soundfile as sf
import librosa
import numpy as np

def read_chunks(file_path, chunk_size_seconds=60, sample_rate=44100):
    """
    오디오 파일을 청크 단위로 처리하는 제너레이터 함수
    
    Args:
        file_path (str): 처리할 오디오 파일 경로
        chunk_size (int): 각 청크의 크기(샘플 수)
    
    Yields:
        tuple: (audio_chunk, sample_rate) 형태의 튜플
              audio_chunk는 현재 처리 중인 오디오 데이터 부분
              sample_rate는 오디오의 샘플레이트
    """
    # 오디오 파일 정보 얻기 (전체 파일을 메모리에 로드하지 않음)
    info = sf.info(file_path)
    total_samples = info.frames
    print(f"샘플레이트: {info.samplerate}, 총 샘플: {total_samples}, 채널: {info.channels}")

    # 청크 크기 계산 (샘플 수)
    chunk_size = int(chunk_size_seconds * sample_rate)

    # 현재 처리 진행률 초기화
    current_process = 0

        # 청크 단위로 데이터 읽기
    for start_idx in range(0, total_samples, chunk_size):
        # 현재 청크의 끝 인덱스 계산 (파일 끝 처리 포함)
        end_idx = min(start_idx + chunk_size, total_samples)
        
        # 현재 청크만 파일에서 읽기 (메모리 효율적)
        with sf.SoundFile(file_path) as f:
            # 시작 위치로 이동
            f.seek(start_idx)
            # 현재 청크 크기만큼 읽기
            current_chunk = f.read(frames=end_idx - start_idx, dtype='float32')
        
        # 처리 진행률 계산 및 출력
        next_process = round(end_idx / total_samples, 2) * 100
        if current_process != next_process:
            print(f"처리 중: {next_process:.0f}%")
            current_process = next_process
        
        # 현재 청크와 샘플레이트 반환
        yield current_chunk

    # # 전체 오디오 파일 로드 (librosa는 기본적으로 전체 파일을 로드함)
    # audio_data, sample_rate = librosa.load(file_path, sr=44100, mono=False)
    
    # # 전체 오디오 길이
    # total_length = len(audio_data)
    
    # # 청크 단위로 데이터 생성
    # current_processs = 0
    # for i in range(0, total_length, chunk_size):
    #     # 현재 청크의 끝 인덱스 계산 (파일 끝 처리 포함)
    #     end_idx = min(i + chunk_size, total_length)
        
    #     # 현재 청크 추출
    #     current_chunk = audio_data[i:end_idx]
    #     print(f"합쳐진 오디오 형태: {current_chunk.shape}, 타입: {current_chunk.dtype}")
        
    #     next_processs = round(end_idx / total_length, 2) * 100
    #     if current_processs != next_processs:
    #         print(f"처리 중: {next_processs:.0f}%")
    #         current_processs = next_processs
        
    #     # 현재 청크와 샘플레이트 반환
    #     yield current_chunk, sample_rate

def save_audio(audio_chunks, sample_rate, file_name):
    # 출력 디렉토리가 없으면 생성
    os.makedirs("output", exist_ok=True)

    file_path = os.path.join("output", f"instrumental_{file_name}")

    # 제너레이터에서 첫 번째 값 가져오기 (형식과 샘플 레이트 확인용)
    try:
        # 나머지 모든 청크 처리
        all_chunks = []
        chunk_count = 0
        for chunk in audio_chunks:
            print(f"청크 {chunk_count + 1} 처리 중: 형태={chunk.shape}")
            all_chunks.append(chunk)
            chunk_count += 1

        if not all_chunks:
            raise Exception("청크가 비어 있습니다.")
        
        # 모든 청크 결합하여 저장
        combined_audio = np.concatenate(all_chunks, axis=0)
        print(f"합쳐진 오디오 형태: {combined_audio.shape}, 타입: {combined_audio.dtype}")

        # soundfile이나 librosa 등으로 저장
        sf.write(file_path, combined_audio, sample_rate, format='WAV')
    except StopIteration:
        print("경고: 처리할 오디오 청크가 없습니다.")
        return None
    except Exception as e:
        print(f"오디오 저장 중 오류 발생: {str(e)}")
        raise