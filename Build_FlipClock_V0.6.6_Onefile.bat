@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo  FlipClock V0.6.6 - Nuitka Onefile 建置
echo  Windows 原生系統匣，不需要 pystray / Pillow
echo ============================================================
echo.

py -3.13 -m pip install --upgrade Nuitka ordered-set zstandard
if errorlevel 1 goto :failed

if exist "%~dp0build" rmdir /s /q "%~dp0build"

py -3.13 -m nuitka ^
  --mode=onefile ^
  --enable-plugin=tk-inter ^
  --windows-console-mode=disable ^
  --output-dir="%~dp0build" ^
  --output-filename=FlipClock_V0.6.6.exe ^
  --remove-output ^
  --assume-yes-for-downloads ^
  --windows-icon-from-ico="%~dp0FlipClock_V0.6.6.ico" ^
  --file-version=0.6.6.0 ^
  --product-version=0.6.6.0 ^
  --product-name=FlipClock ^
  --file-description="Railway Flip Clock Native System Tray" ^
  --force-stderr-spec="{PROGRAM_BASE}.error.log" ^
  "%~dp0FlipClock_V0.6.6.py"

if errorlevel 1 goto :failed

echo.
echo 建置完成：
echo %~dp0build\FlipClock_V0.6.6.exe
start "" "%~dp0build"
pause
exit /b 0

:failed
echo.
echo 建置失敗。
pause
exit /b 1
