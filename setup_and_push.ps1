# Hydra 项目 GitHub 设置和推送脚本
Write-Host "=== Hydra GitHub 设置向导 ===" -ForegroundColor Cyan
Write-Host ""

# 检查 Git 配置
$currentName = git config --global user.name 2>$null
$currentEmail = git config --global user.email 2>$null

if ($currentName -and $currentEmail) {
    Write-Host "当前 Git 配置:" -ForegroundColor Green
    Write-Host "  用户名: $currentName" -ForegroundColor Gray
    Write-Host "  邮箱: $currentEmail" -ForegroundColor Gray
    Write-Host ""
    $useCurrent = Read-Host "使用当前配置? (Y/N)"
    if ($useCurrent -ne "Y" -and $useCurrent -ne "y") {
        $currentName = $null
        $currentEmail = $null
    }
}

if (-not $currentName -or -not $currentEmail) {
    Write-Host "请配置 Git 用户信息:" -ForegroundColor Yellow
    $name = Read-Host "请输入你的姓名（或 GitHub 用户名）"
    $email = Read-Host "请输入你的邮箱（建议使用 GitHub 邮箱）"
    
    if ($name -and $email) {
        git config --global user.name $name
        git config --global user.email $email
        Write-Host "✓ Git 用户信息已配置" -ForegroundColor Green
    } else {
        Write-Host "✗ 配置信息不完整，退出" -ForegroundColor Red
        exit 1
    }
}

# 检查是否有未提交的更改
$status = git status --porcelain
if ($status) {
    Write-Host ""
    Write-Host "发现未提交的文件，正在提交..." -ForegroundColor Yellow
    git add .
    
    $commitMsg = Read-Host "请输入提交信息（直接回车使用默认）"
    if ([string]::IsNullOrWhiteSpace($commitMsg)) {
        $commitMsg = "Initial commit: Hydra SEO Ecosystem"
    }
    
    git commit -m $commitMsg
    Write-Host "✓ 提交完成" -ForegroundColor Green
} else {
    Write-Host "✓ 所有文件已提交" -ForegroundColor Green
}

# 检查远程仓库
$remote = git remote get-url origin 2>$null
if ($remote) {
    Write-Host ""
    Write-Host "已配置的远程仓库: $remote" -ForegroundColor Green
    $push = Read-Host "是否推送到此仓库? (Y/N)"
    if ($push -eq "Y" -or $push -eq "y") {
        git branch -M main 2>$null
        git push -u origin main
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 推送成功！" -ForegroundColor Green
            exit 0
        }
    }
}

# 创建 GitHub 仓库
Write-Host ""
Write-Host "=== 创建 GitHub 仓库 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "请选择创建仓库的方式:" -ForegroundColor Yellow
Write-Host "1. 手动在 GitHub 网站创建（推荐）" -ForegroundColor White
Write-Host "2. 使用 GitHub CLI (gh) 创建（需要安装 gh 并登录）" -ForegroundColor White
Write-Host "3. 稍后手动推送" -ForegroundColor White
Write-Host ""
$choice = Read-Host "请选择 (1/2/3)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "请按照以下步骤操作:" -ForegroundColor Yellow
    Write-Host "1. 访问: https://github.com/new" -ForegroundColor Cyan
    Write-Host "2. 输入仓库名称（如: hydra-seo）" -ForegroundColor Cyan
    Write-Host "3. 选择 Public 或 Private" -ForegroundColor Cyan
    Write-Host "4. 不要勾选 'Initialize this repository with a README'" -ForegroundColor Cyan
    Write-Host "5. 点击 'Create repository'" -ForegroundColor Cyan
    Write-Host ""
    $repoUrl = Read-Host "创建完成后，请输入仓库 URL（如: https://github.com/username/repo.git）"
    
    if ($repoUrl) {
        git remote remove origin 2>$null
        git remote add origin $repoUrl
        git branch -M main 2>$null
        Write-Host ""
        Write-Host "正在推送到 GitHub..." -ForegroundColor Yellow
        git push -u origin main
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 推送成功！" -ForegroundColor Green
            Write-Host "仓库地址: $repoUrl" -ForegroundColor Cyan
        } else {
            Write-Host "✗ 推送失败，请检查:" -ForegroundColor Red
            Write-Host "  - 网络连接" -ForegroundColor Yellow
            Write-Host "  - 仓库 URL 是否正确" -ForegroundColor Yellow
            Write-Host "  - 是否有推送权限" -ForegroundColor Yellow
        }
    }
} elseif ($choice -eq "2") {
    # 检查 GitHub CLI
    $ghInstalled = Get-Command gh -ErrorAction SilentlyContinue
    if (-not $ghInstalled) {
        Write-Host "✗ GitHub CLI 未安装" -ForegroundColor Red
        Write-Host "请访问 https://cli.github.com/ 下载安装" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host ""
    Write-Host "检查 GitHub CLI 登录状态..." -ForegroundColor Yellow
    gh auth status 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "需要登录 GitHub CLI" -ForegroundColor Yellow
        gh auth login
    }
    
    $repoName = Read-Host "请输入仓库名称（如: hydra-seo）"
    $isPrivate = Read-Host "是否创建私有仓库? (Y/N)"
    $privateFlag = if ($isPrivate -eq "Y" -or $isPrivate -eq "y") { "--private" } else { "--public" }
    
    Write-Host ""
    Write-Host "正在创建 GitHub 仓库..." -ForegroundColor Yellow
    gh repo create $repoName $privateFlag --source=. --remote=origin --push
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 仓库创建并推送成功！" -ForegroundColor Green
        $repoUrl = gh repo view --web 2>$null
        Write-Host "仓库地址: $repoUrl" -ForegroundColor Cyan
    } else {
        Write-Host "✗ 创建失败，请检查错误信息" -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "稍后可以使用以下命令推送:" -ForegroundColor Yellow
    Write-Host "  git remote add origin https://github.com/USERNAME/REPO.git" -ForegroundColor Gray
    Write-Host "  git branch -M main" -ForegroundColor Gray
    Write-Host "  git push -u origin main" -ForegroundColor Gray
}

Write-Host ""
Write-Host "完成！" -ForegroundColor Green

