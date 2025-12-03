# Hydra Auto Push Script (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Hydra Auto Push Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check status
Write-Host "[1/4] Checking status..." -ForegroundColor Yellow
git status --short
Write-Host ""

# Step 2: Add all changes
Write-Host "[2/4] Adding all changes..." -ForegroundColor Yellow
git add .
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to add files" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Files added" -ForegroundColor Green
Write-Host ""

# Step 3: Commit
Write-Host "[3/4] Creating commit..." -ForegroundColor Yellow
$commitMsg = Read-Host "Enter commit message (or press Enter for auto)"
if ([string]::IsNullOrWhiteSpace($commitMsg)) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $commitMsg = "Auto commit: $timestamp"
}
git commit -m $commitMsg
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to commit" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Committed" -ForegroundColor Green
Write-Host ""

# Step 4: Push
Write-Host "[4/4] Pushing to remote..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to push" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Pushed successfully" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All done!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan


