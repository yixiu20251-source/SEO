# Hydra 项目 GitHub 推送脚本
# 使用方法: .\push_to_github.ps1

Write-Host "=== Hydra GitHub 推送脚本 ===" -ForegroundColor Cyan
Write-Host ""

# 检查 Git 是否安装
try {
    $gitVersion = git --version
    Write-Host "✓ Git 已安装: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Git 未安装或不在 PATH 中" -ForegroundColor Red
    Write-Host "请访问 https://git-scm.com/download/win 下载安装 Git" -ForegroundColor Yellow
    exit 1
}

# 检查是否已初始化 Git 仓库
if (Test-Path .git) {
    Write-Host "✓ Git 仓库已初始化" -ForegroundColor Green
} else {
    Write-Host "初始化 Git 仓库..." -ForegroundColor Yellow
    git init
    Write-Host "✓ Git 仓库初始化完成" -ForegroundColor Green
}

# 检查是否有未提交的更改
$status = git status --porcelain
if ($status) {
    Write-Host "发现未提交的文件，准备添加..." -ForegroundColor Yellow
    git add .
    Write-Host "✓ 文件已添加到暂存区" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "请输入提交信息（或按 Enter 使用默认信息）:" -ForegroundColor Cyan
    $commitMessage = Read-Host
    if ([string]::IsNullOrWhiteSpace($commitMessage)) {
        $commitMessage = "Initial commit: Hydra SEO Ecosystem"
    }
    
    git commit -m $commitMessage
    Write-Host "✓ 提交完成" -ForegroundColor Green
} else {
    Write-Host "✓ 没有未提交的更改" -ForegroundColor Green
}

# 检查远程仓库
$remote = git remote get-url origin 2>$null
if ($remote) {
    Write-Host "✓ 远程仓库已配置: $remote" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "请提供 GitHub 仓库 URL:" -ForegroundColor Cyan
    Write-Host "格式: https://github.com/USERNAME/REPO.git 或 git@github.com:USERNAME/REPO.git" -ForegroundColor Gray
    $repoUrl = Read-Host
    
    if ([string]::IsNullOrWhiteSpace($repoUrl)) {
        Write-Host "✗ 未提供仓库 URL，跳过远程配置" -ForegroundColor Red
        Write-Host "你可以稍后使用以下命令添加远程仓库:" -ForegroundColor Yellow
        Write-Host "  git remote add origin YOUR_REPO_URL" -ForegroundColor Gray
        exit 0
    }
    
    git remote add origin $repoUrl
    Write-Host "✓ 远程仓库已添加" -ForegroundColor Green
}

# 设置主分支名称
git branch -M main 2>$null

# 询问是否推送
Write-Host ""
Write-Host "是否现在推送到 GitHub? (Y/N)" -ForegroundColor Cyan
$push = Read-Host

if ($push -eq "Y" -or $push -eq "y") {
    Write-Host "正在推送到 GitHub..." -ForegroundColor Yellow
    git push -u origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 推送成功！" -ForegroundColor Green
    } else {
        Write-Host "✗ 推送失败，请检查网络连接和权限" -ForegroundColor Red
    }
} else {
    Write-Host "跳过推送。你可以稍后使用以下命令推送:" -ForegroundColor Yellow
    Write-Host "  git push -u origin main" -ForegroundColor Gray
}

Write-Host ""
Write-Host "完成！" -ForegroundColor Green

