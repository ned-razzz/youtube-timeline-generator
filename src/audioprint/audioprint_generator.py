from collections import defaultdict
import essentia.standard as es
import numpy as np
import numba as nb

from src.utils.types import TypeConverter


class AudioprintGenerator:
    # 윈도우 크기와 홉 크기 설정 (클래스 변수)
    frame_size = 2048  # ~42.7ms at 48kHz
    hop_size = 640  # 20ms at 48kHz

    # 알고리즘 초기화 (클래스 변수)
    window = es.Windowing(type="hann")
    spectrum = es.Spectrum()
    spectral_peaks = es.SpectralPeaks(
        orderBy="magnitude",
        magnitudeThreshold=0.0001,  # 낮은 에너지 피크 무시
        maxPeaks=25,  # 각 프레임당 최대 피크 수
        minFrequency=100,  # 최소 주파수 (Hz)
        maxFrequency=4095,  # 최대 주파수 (Hz)
    )

    # 해시 키 생성을 위한 비트 연산 관련 상수 (클래스 변수)
    FREQ_BITS = 12  # 주파수 값을 위한 비트 수 (최대 4096Hz 범위 표현)
    DELTA_MASK = (1 << 12) - 1  # 주파수 차이를 위한 마스크 (12비트)

    @classmethod
    def get_spectrogram_fingerprint(cls, audio_data, sample_rate=44100):
        """
        스펙트로그램 피크 기반 오디오 지문 생성 (Shazam 유사 접근법)
        """
        # 지문 데이터 저장소
        peak_pairs = defaultdict(list)  # 피크 쌍을 이용한 해시 테이블

        # 프레임 인덱스 (시간 정보로 변환 가능)
        frame_idx = 0

        # 각 프레임 처리
        for frame in es.FrameGenerator(
            audio_data, frameSize=cls.frame_size, hopSize=cls.hop_size
        ):
            # 윈도우 적용 및 스펙트럼 계산
            windowed_frame = cls.window(frame)
            spectrum_values = cls.spectrum(windowed_frame)

            # 스펙트럼 피크 추출
            frequencies, magnitudes = cls.spectral_peaks(spectrum_values)
            # 최적의 피크만 선택 (대역별 선택 방식)
            frequencies, magnitudes = cls._select_optimal_peaks(frequencies, magnitudes)
            # 개별 피크 정보 저장 (시간, 주파수, 진폭)
            time_sec = frame_idx * cls.hop_size / float(sample_rate)

            # Shazam 스타일의 해싱 - 앵커 포인트와 타겟 포인트 쌍 형성
            pairs = cls._create_peak_pairs_fast(
                frequencies, time_sec, cls.FREQ_BITS, cls.DELTA_MASK
            )

            # 피크 쌍 사전에 저장
            for hash_key, time in pairs:
                peak_pairs[hash_key].append(time)

            frame_idx += 1
            print(f"\r지문 인식 중: {frame_idx}", end="")

        audioprint = TypeConverter.convert_numba_dict(dict(peak_pairs))

        # 디버깅 정보
        print(f" => 해시 수: {len(audioprint)}")

        return audioprint

    @staticmethod
    def _select_optimal_peaks(frequencies, magnitudes, num_bands=5, peaks_per_band=6):
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
            indices = [i for i, f in enumerate(frequencies) if band_min <= f < band_max]

            if indices:
                # 진폭 기준 정렬
                sorted_indices = sorted(
                    indices, key=lambda i: magnitudes[i], reverse=True
                )
                # 상위 피크만 선택
                for idx in sorted_indices[:peaks_per_band]:
                    selected_freqs.append(frequencies[idx])
                    selected_mags.append(magnitudes[idx])

        return np.array(selected_freqs), np.array(selected_mags)

    @staticmethod
    @nb.njit(fastmath=True)
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
                    hash_key = (int(freq1) << freq_bits) | (
                        int(freq_delta) & delta_mask
                    )

                    # 해시 테이블에 시간 정보와 함께 저장
                    pairs.append((hash_key, time_sec))
        return pairs
