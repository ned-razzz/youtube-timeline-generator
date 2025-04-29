@echo off
chcp 949 > nul
echo Project Siren - Kpop World Cup YouTube Timeline Generator
echo =========================================================
echo.

:MENU
echo Select an option:
echo 1. Generate audio fingerprints
echo 2. Generate timeline
echo.
set /p CHOICE="Choose (1 or 2): "

if "%CHOICE%"=="1" goto FINGERPRINT
if "%CHOICE%"=="2" goto TIMELINE
echo Invalid selection.
goto END

:FINGERPRINT
echo.
echo Audio Fingerprint Mode
echo.
set /p SONGLIST="Song list file path: "
set /p WORLDCUP="World Cup name: "
echo.
echo Debug:
echo [%SONGLIST%]
echo [%WORLDCUP%]
echo.
docker run -it --rm -v "%cd%:/data" song5173/project-siren audioprint --urls /data/%SONGLIST% --name "%WORLDCUP%"
goto END

:TIMELINE
echo.
echo Timeline Generation Mode
echo.
set /p URL="YouTube URL: "
set /p WORLDCUP="World Cup name: "
set /p START="Start time (HH:MM:SS) [Default: 00:00:00]: "
if "%START%"=="" set START=00:00:00
set /p END="End time (HH:MM:SS) [Default: 00:10:00]: "
if "%END%"=="" set END=00:10:00
docker run -it --rm -v "%cd%:/data" song5173/project-siren timeline --url "%URL%" --worldcup "%WORLDCUP%" --start "%START%" --end "%END%"
goto END

:END
pause