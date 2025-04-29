#!/bin/bash
echo "Project Siren - 창팝 월드컵 유튜브 타임라인 자동 생성기"
echo "======================================================="
echo

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
  echo "Docker가 설치되어 있지 않습니다."
  echo "https://www.docker.com/products/docker-desktop 에서 Docker Desktop을 설치해주세요."
  exit 1
fi

# 메뉴 표시
echo "실행할 작업을 선택하세요:"
echo "1. 오디오 지문 생성"
echo "2. 타임라인 생성"
echo
read -p "선택 (1 또는 2): " CHOICE

if [ "$CHOICE" = "1" ]; then
  echo
  echo "오디오 지문 생성 모드"
  echo
  read -p "노래 목록 파일 경로: " SONGLIST
  read -p "월드컵 이름: " WORLDCUP
  
  docker run -it --rm -v "$(pwd):/data" yourusername/project-siren audioprint --urls /data/$SONGLIST --name "$WORLDCUP"
elif [ "$CHOICE" = "2" ]; then
  echo
  echo "타임라인 생성 모드"
  echo
  read -p "유튜브 URL: " URL
  read -p "월드컵 이름: " WORLDCUP
  read -p "시작 시간 (HH:MM:SS) [기본값: 00:00:00]: " START
  START=${START:-00:00:00}
  read -p "종료 시간 (HH:MM:SS) [기본값: 00:10:00]: " END
  END=${END:-00:10:00}
  
  docker run -it --rm -v "$(pwd):/data" yourusername/project-siren timeline --url "$URL" --worldcup "$WORLDCUP" --start "$START" --end "$END"
else
  echo "잘못된 선택입니다."
fi