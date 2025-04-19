import essentia
import essentia.standard as es
import numpy as np
from datetime import datetime


def compare_fingerprints(fp1, fp2, method="cosine"):
    """
    두 Chromaprint 지문의 유사도 계산

    매개변수:
        fp1 (numpy.ndarray): 첫 번째 지문
        fp2 (numpy.ndarray): 두 번째 지문
        method (str): 비교 방식 ('euclidean', 'cosine')

    반환:
        float: 유사도 점수 (낮을수록 유사)
    """
    if fp1 is None or fp2 is None:
        return float("inf")

    if fp1.shape != fp2.shape:
        # 길이가 다른 경우 최소 길이로 자르기
        min_length = min(fp1.shape[0], fp2.shape[0])
        fp1 = fp1[:min_length]
        fp2 = fp2[:min_length]

    if method == "euclidean":
        # 유클리드 거리 계산
        distance = np.mean(np.sqrt(np.sum((fp1 - fp2) ** 2, axis=1)))
    elif method == "cosine":
        # 코사인 유사도 계산 (1에서 빼서 거리로 변환)
        # 코사인 유사도는 Chromaprint에 더 적합함
        similarity = np.mean(
            [
                np.dot(fp1[i], fp2[i])
                / (np.linalg.norm(fp1[i]) * np.linalg.norm(fp2[i]) + 1e-10)
                for i in range(len(fp1))
            ]
        )
        distance = 1 - similarity
    else:
        raise ValueError(f"지원되지 않는 비교 방식: {method}")

    return distance


def find_song_timestamp(
    video_audio, reference_fingerprint, window_size=5, hop_size=0.5, threshold=0.7
):
    """
    오디오/비디오에서 참조 노래가 시작되는 시점을 탐지

    매개변수:
        video_audio: 분석할 오디오 데이터
        reference_fingerprint: 찾고자 하는 노래의 지문
        window_size: 분석 윈도우 크기(초)
        hop_size: 윈도우 이동 간격(초)
        threshold: 매칭 임계값 (0-1 사이, 낮을수록 더 엄격한 매칭)

    반환:
        float: 노래 시작 시점 (초), 못 찾으면 None
    """
    sample_rate = 44100  # 일반적인 오디오 샘플레이트

    best_match_time = None
    best_match_score = float("inf")

    # 비디오를 윈도우 단위로 분석
    for start_time in np.arange(
        0, len(video_audio) / sample_rate - window_size, hop_size
    ):
        start_sample = int(start_time * sample_rate)
        end_sample = int((start_time + window_size) * sample_rate)

        # 현재 윈도우의 오디오 추출
        window_audio = video_audio[start_sample:end_sample]

        # 현재 윈도우의 지문 생성
        window_fingerprint = _create_chromaprint_fingerprint(window_audio)

        # 지문 유사도 계산
        distance = compare_fingerprints(
            (
                reference_fingerprint[: len(window_fingerprint)]
                if len(reference_fingerprint) > len(window_fingerprint)
                else reference_fingerprint
            ),
            window_fingerprint,
            method="cosine",
        )

        # 더 좋은 매칭을 찾았다면 업데이트
        if distance < best_match_score:
            best_match_score = distance
            best_match_time = start_time

    # 임계값 체크
    if best_match_score < threshold:
        return best_match_time
    return None
