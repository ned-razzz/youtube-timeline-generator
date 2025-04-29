@echo off
echo Project Siren - 창팝 월드컵 유튜브 타임라인 자동 생성기
echo =======================================================
echo.

:: Docker 설치 확인
docker --version > nul 2>&1
if %errorlevel% neq 0 (
  echo Docker가 설치되어 있지 않습니다.
  echo https://www.docker.com/products/docker-desktop 에서 Docker Desktop을 설치해주세요.
  pause
  exit
)

:: 메뉴 표시
echo 실행할 작업을 선택하세요:
echo 1. 오디오 지문 생성
echo 2. 타임라인 생성
echo.
set /p CHOICE="선택 (1 또는 2): "

if "%CHOICE%"=="1" (
  echo.
  echo 오디오 지문 생성 모드
  echo.
  set /p SONGLIST="노래 목록 파일 경로: "
  set /p WORLDCUP="월드컵 이름: "
  
  docker run -it --rm -v "%cd%:/data" yourusername/project-siren audioprint --urls /data/%SONGLIST% --name "%WORLDCUP%"
) else if "%CHOICE%"=="2" (
  echo.
  echo 타임라인 생성 모드
  echo.
  set /p URL="유튜브 URL: "
  set /p WORLDCUP="월드컵 이름: "
  set /p START="시작 시간 (HH:MM:SS) [기본값: 00:00:00]: "
  if "%START%"=="" set START=00:00:00
  set /p END="종료 시간 (HH:MM:SS) [기본값: 00:10:00]: "
  if "%END%"=="" set END=00:10:00
  
  docker run -it --rm -v "%cd%:/data" yourusername/project-siren timeline --url "%URL%" --worldcup "%WORLDCUP%" --start "%START%" --end "%END%"
) else (
  echo 잘못된 선택입니다.
)

pause