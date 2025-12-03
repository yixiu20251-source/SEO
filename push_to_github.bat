@echo off
chcp 65001 >nul
echo === Hydra GitHub 推送脚本 ===
echo.

REM 检查 Git 是否安装
git --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Git 未安装或不在 PATH 中
    echo 请访问 https://git-scm.com/download/win 下载安装 Git
    pause
    exit /b 1
)

echo ✓ Git 已安装
echo.

REM 检查是否已初始化 Git 仓库
if exist .git (
    echo ✓ Git 仓库已初始化
) else (
    echo 初始化 Git 仓库...
    git init
    echo ✓ Git 仓库初始化完成
)

echo.
echo 添加文件到暂存区...
git add .
echo ✓ 文件已添加
echo.

set /p commit_msg="请输入提交信息（直接回车使用默认）: "
if "%commit_msg%"=="" set commit_msg=Initial commit: Hydra SEO Ecosystem

git commit -m "%commit_msg%"
if errorlevel 1 (
    echo 注意: 提交可能失败（可能没有更改）
) else (
    echo ✓ 提交完成
)

echo.
set /p repo_url="请输入 GitHub 仓库 URL（留空跳过）: "
if not "%repo_url%"=="" (
    git remote remove origin 2>nul
    git remote add origin "%repo_url%"
    echo ✓ 远程仓库已配置
    echo.
    set /p push_confirm="是否现在推送? (Y/N): "
    if /i "%push_confirm%"=="Y" (
        git branch -M main 2>nul
        git push -u origin main
        if errorlevel 1 (
            echo ✗ 推送失败，请检查网络连接和权限
        ) else (
            echo ✓ 推送成功！
        )
    )
)

echo.
echo 完成！
pause

