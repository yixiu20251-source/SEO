@echo off
chcp 65001 >nul
echo === Hydra GitHub 快速设置 ===
echo.

echo 步骤 1: 配置 Git 用户信息
set /p git_name="请输入你的 GitHub 用户名或姓名: "
set /p git_email="请输入你的邮箱: "

git config --global user.name "%git_name%"
git config --global user.email "%git_email%"
echo ✓ Git 用户信息已配置
echo.

echo 步骤 2: 创建提交
git add .
git commit -m "Initial commit: Hydra SEO Ecosystem"
echo ✓ 提交完成
echo.

echo 步骤 3: 创建 GitHub 仓库
echo 请访问: https://github.com/new
echo 1. 输入仓库名称（如: hydra-seo）
echo 2. 选择 Public 或 Private
echo 3. 不要勾选任何初始化选项
echo 4. 点击 Create repository
echo.
set /p repo_url="创建完成后，请输入仓库 URL（如: https://github.com/username/repo.git）: "

if not "%repo_url%"=="" (
    echo.
    echo 步骤 4: 推送到 GitHub
    git remote remove origin 2>nul
    git remote add origin "%repo_url%"
    git branch -M main
    git push -u origin main
    if errorlevel 1 (
        echo.
        echo ✗ 推送失败，请检查:
        echo   - 网络连接
        echo   - 仓库 URL 是否正确
        echo   - 是否有推送权限
    ) else (
        echo.
        echo ✓ 推送成功！
        echo 仓库地址: %repo_url%
    )
)

echo.
echo 完成！
pause

