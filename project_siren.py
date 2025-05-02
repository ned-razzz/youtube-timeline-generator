#!/usr/bin/env python
"""
Project Siren - 창팝 월드컵 유튜브 타임라인 자동 생성기
"""
import sys
import os
import argparse


# 실행 환경에서 경로 조정을 위한 코드
def resource_path(relative_path):
    """리소스 경로를 반환하는 함수"""
    try:
        # PyInstaller 번들 환경인 경우
        base_path = sys._MEIPASS
    except Exception:
        # 일반 Python 환경인 경우
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# 필요한 경로 추가
sys.path.insert(0, resource_path("."))


def main():
    parser = argparse.ArgumentParser(
        description="Project Siren - 창팝 월드컵 유튜브 타임라인 자동 생성기",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="실행할 명령")

    # 오디오 지문 생성 명령어
    audioprint_parser = subparsers.add_parser("audioprint", help="오디오 지문 생성")
    audioprint_parser.add_argument(
        "-u", "--urls", required=True, help="YouTube URL이 포함된 텍스트 파일 경로"
    )
    audioprint_parser.add_argument("-n", "--name", required=True, help="지문 컬렉션 이름")

    # 타임라인 생성 명령어
    timeline_parser = subparsers.add_parser("timeline", help="타임라인 생성")
    timeline_parser.add_argument("-u", "--url", required=True, help="월드컵 영상 YouTube URL")
    timeline_parser.add_argument("-w", "--worldcup", required=True, help="감지할 월드컵 이름")
    timeline_parser.add_argument("-st", "--start", default="00:00:00", help="시작 시간 (HH:MM:SS)")
    timeline_parser.add_argument("-ed", "--end", default="00:10:00", help="종료 시간 (HH:MM:SS)")
    timeline_parser.add_argument(
        "-ch", "--chunk", type=int, default=30, help="각 오디오 청크의 감지 크기 (초)"
    )
    timeline_parser.add_argument("-hp", "--hop", type=int, default=20, help="다음 청크 진행 크기")
    timeline_parser.add_argument(
        "-th", "--threshold", type=float, default=0.001, help="감지할 최소 유사도 임계값"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "audioprint":
        # 오디오 지문 생성 모듈 로드 및 실행
        from main.audioprint.__main__ import main as audioprint_main

        sys.argv = ["audioprint", "--urls", args.urls, "--name", args.name]
        audioprint_main()

    elif args.command == "timeline":
        # 타임라인 생성 모듈 로드 및 실행
        from main.timeline.__main__ import main as timeline_main

        sys.argv = [
            "timeline",
            "--url",
            args.url,
            "--worldcup",
            args.worldcup,
            "--start",
            args.start,
            "--end",
            args.end,
            "--chunk",
            str(args.chunk),
            "--hop",
            str(args.hop),
            "--threshold",
            str(args.threshold),
        ]
        timeline_main()


if __name__ == "__main__":
    main()
