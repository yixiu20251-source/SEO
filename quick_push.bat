@echo off
REM Quick push without prompts
git add . && git commit -m "Auto commit: %date% %time%" && git push origin main
if errorlevel 1 (
    echo Push failed!
    pause
) else (
    echo Push successful!
)


