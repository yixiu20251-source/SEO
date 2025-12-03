@echo off
chcp 65001 >nul
echo ========================================
echo Hydra Auto Push Script
echo ========================================
echo.

echo [1/4] Checking status...
git status --short
echo.

echo [2/4] Adding all changes...
git add .
if errorlevel 1 (
    echo ERROR: Failed to add files
    pause
    exit /b 1
)
echo ✓ Files added
echo.

echo [3/4] Creating commit...
set /p commit_msg="Enter commit message (or press Enter for auto): "
if "%commit_msg%"=="" (
    for /f "tokens=*" %%i in ('git log -1 --pretty=format:"%%s"') do set last_msg=%%i
    set commit_msg=Auto commit: %date% %time%
)
git commit -m "%commit_msg%"
if errorlevel 1 (
    echo ERROR: Failed to commit
    pause
    exit /b 1
)
echo ✓ Committed
echo.

echo [4/4] Pushing to remote...
git push origin main
if errorlevel 1 (
    echo ERROR: Failed to push
    pause
    exit /b 1
)
echo ✓ Pushed successfully
echo.

echo ========================================
echo All done!
echo ========================================
timeout /t 2 >nul


