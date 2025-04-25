from collections import defaultdict
import os
import pickle
import essentia.standard as es
import numpy as np
import numba as nb
from numba import typed, types
from datetime import datetime

from src.timeline_generator.types import convert_to_numba_dict


class FingerprintGenerator:
    def __init__(self, frame_size=2048, hop_size=640):
        # 윈도우 크기와 홉 크기 설정
        self.frame_size = frame_size  # ~42.7ms at 48kHz  
        self.hop_size = hop_size      # 20ms at 48kHz
        
        # 알고리즘 초기화
        self.window = es.Windowing(type='hann')
        self.spectrum = es.Spectrum()
        self.spectral_peaks = es.SpectralPeaks(
            orderBy='magnitude',
            magnitudeThreshold=0.0001,  # 낮은 에너지 피크 무시
            maxPeaks=25,                 # 각 프레임당 최대 피크 수
            minFrequency=100,            # 최소 주파수 (Hz)
            maxFrequency=4095            # 최대 주파수 (Hz)
        )
        
        # 해시 키 생성을 위한 비트 연산 관련 상수
        self.FREQ_BITS = 12  # 주파수 값을 위한 비트 수 (최대 4096Hz 범위 표현)
        self.DELTA_MASK = (1 << 12) - 1  # 주파수 차이를 위한 마스크 (12비트)

    def get_spectrogram_fingerprint(self, audio_data, sample_rate=44100):
        """`
        스펙트로그램 피크 기반 오디오 지문 생성 (Shazam 유사 접근법)
        """
        # 지문 데이터 저장소
        peak_pairs = defaultdict(list) # 피크 쌍을 이용한 해시 테이블
        
        # 프레임 인덱스 (시간 정보로 변환 가능)
        frame_idx = 0
        
        # 각 프레임 처리
        for frame in es.FrameGenerator(audio_data, frameSize=self.frame_size, hopSize=self.hop_size):
            # 윈도우 적용 및 스펙트럼 계산
            windowed_frame = self.window(frame)
            spectrum_values = self.spectrum(windowed_frame)
            
            # 스펙트럼 피크 추출
            frequencies, magnitudes = self.spectral_peaks(spectrum_values)

            # 최적의 피크만 선택 (대역별 선택 방식)
            frequencies, magnitudes = self._select_optimal_peaks(frequencies, magnitudes)
            
            # 개별 피크 정보 저장 (시간, 주파수, 진폭)
            time_sec = frame_idx * self.hop_size / float(sample_rate)
            
            # Shazam 스타일의 해싱 - 앵커 포인트와 타겟 포인트 쌍 형성
            pairs = self._create_peak_pairs_fast(frequencies, time_sec, self.FREQ_BITS, self.DELTA_MASK)
            
            # 피크 쌍 사전에 저장
            for hash_key, time in pairs:
                peak_pairs[hash_key].append(time)
            
            frame_idx += 1
            print(f"\r지문 인식 중: {frame_idx}", end="")
            
        fingerprint = convert_to_numba_dict(dict(peak_pairs))

        # 디버깅 정보
        print(f"\n해시 수: {len(fingerprint)}")

        return fingerprint
    
    
    def _select_optimal_peaks(self, frequencies, magnitudes, num_bands=5, peaks_per_band=6):
        """주파수 대역별로 최적의 피크만 선택"""
        if len(frequencies) == 0:
            return np.array([]), np.array([])
            
        min_freq, max_freq = 100, 5000
        band_width = (max_freq - min_freq) / num_bands
        
        # 최적 피크 데이터 변수
        selected_freqs = []
        selected_mags = []

        for band in range(num_bands):
            band_min = min_freq + band * band_width
            band_max = band_min + band_width
            
            # 현재 대역에 속하는 피크 인덱스 찾기
            indices = [i for i, f in enumerate(frequencies) 
                    if band_min <= f < band_max]
            
            if indices:
                # 진폭 기준 정렬
                sorted_indices = sorted(indices, key=lambda i: magnitudes[i], reverse=True)
                # 상위 피크만 선택
                for idx in sorted_indices[:peaks_per_band]:
                    selected_freqs.append(frequencies[idx])
                    selected_mags.append(magnitudes[idx])

        return np.array(selected_freqs), np.array(selected_mags)
    
    @staticmethod
    @nb.jit(nopython=True)
    def _create_peak_pairs_fast(frequencies, time_sec, freq_bits, delta_mask):
        """Numba로 최적화된 피크 쌍 처리 함수"""
        pairs = []
        for i in range(len(frequencies)):
            freq1 = frequencies[i]
            for j in range(i + 1, min(i + 10, len(frequencies))):
                freq2 = frequencies[j]

                # 주파수 차이가 너무 작거나 큰 경우 무시
                if 30 < freq2 - freq1 < 1000:
                    freq_delta = freq2 - freq1

                    # 정수 해시 키 생성 (비트 연산 사용)
                    # freq1을 상위 비트에, freq_delta를 하위 비트에 배치
                    hash_key = (int(freq1) << freq_bits) | (int(freq_delta) & delta_mask)
                    
                    # 해시 테이블에 시간 정보와 함께 저장
                    pairs.append((hash_key, time_sec))
        return pairs


    def save_fingerprint(self, fingerprint, metadata=None, output_dir="fingerprints", filename=None):
        """
        오디오 지문과 메타데이터를 파일로 저장
        
        매개변수:
            fingerprint (np.array): 오디오 지문 배열
            metadata (dict): 지문 관련 메타데이터
            output_dir (str): 저장할 디렉토리 경로
            filename (str, optional): 저장할 파일 이름(확장자 없이). 지정하지 않으면 타임스탬프 사용
            
        반환:
            str: 저장된 지문 파일 경로
        """
        # 지문이 유효한지 확인
        if fingerprint is None or (isinstance(fingerprint, np.ndarray) and (fingerprint.size == 0 or np.all(fingerprint == fingerprint.flat[0]))):
            print("경고: 저장하려는 지문이 유효하지 않습니다.")
            return None
        
        # 출력 디렉토리가 없으면 생성
        os.makedirs(output_dir, exist_ok=True)
        
        # 파일 이름이 지정되지 않은 경우 현재 시간으로 생성
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fingerprint_{timestamp}"
        else:
            # 확장자가 있으면 제거
            filename = os.path.splitext(os.path.basename(filename))[0]
        
        # 파일 경로 설정
        fingerprint_path = os.path.join(output_dir, f"{filename}.pkl")
        
        # 메타데이터와 함께 지문 저장
        # 지문 저장 (pickle 형식)
        with open(fingerprint_path, 'wb') as f:
            pickle.dump(fingerprint, f)
        
        print(f"지문이 저장되었습니다: {fingerprint_path}")
        print(f"저장된 지문: {fingerprint}")
        
        return fingerprint_path