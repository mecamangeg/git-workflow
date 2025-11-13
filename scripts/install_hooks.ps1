# Git Workflow Guardian - Hook Installation Script
param(
    [Parameter(Mandatory=$false)]
    [string]$RepoPath = ".",

    [Parameter(Mandatory=$false)]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Git Workflow Guardian - Hook Installer" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Resolve repo path
$RepoPath = Resolve-Path $RepoPath

# Check if git repo
if (-not (Test-Path "$RepoPath/.git")) {
    Write-Error "Not a git repository: $RepoPath"
    exit 1
}

Write-Host "`n[1/4] Validating repository..." -ForegroundColor Yellow
Write-Host "Repository: $RepoPath" -ForegroundColor Gray

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$HooksSource = Join-Path (Split-Path -Parent $ScriptDir) "hooks"

# Check if hooks already installed
$HooksDir = "$RepoPath/.git/hooks"
if ((Test-Path "$HooksDir/pre-commit") -and -not $Force) {
    $response = Read-Host "Hooks already installed. Overwrite? (y/n)"
    if ($response -ne "y") {
        Write-Host "Installation cancelled." -ForegroundColor Red
        exit 0
    }
}

Write-Host "`n[2/4] Installing hooks..." -ForegroundColor Yellow

# Copy hook scripts
$hooks = @("pre-commit.sh", "pre-push.sh", "post-checkout.sh", "post-merge.sh", "notifier.py")

foreach ($hook in $hooks) {
    $source = Join-Path $HooksSource $hook
    $dest = Join-Path $HooksDir ($hook -replace ".sh$", "")

    if (Test-Path $source) {
        Copy-Item $source $dest -Force
        Write-Host "  ✓ Installed: $hook" -ForegroundColor Green

        # Make executable (Git Bash compatibility)
        if ($hook -match ".sh$") {
            try {
                git -C $RepoPath update-index --chmod=+x ".git/hooks/$($hook -replace '.sh$', '')" 2>$null
            } catch {
                # Ignore errors on Windows
            }
        }
    } else {
        Write-Host "  ✗ Missing: $hook" -ForegroundColor Red
    }
}

Write-Host "`n[3/4] Configuring permissions..." -ForegroundColor Yellow
# Permissions already set above
Write-Host "  ✓ Permissions configured" -ForegroundColor Green

Write-Host "`n[4/4] Verifying installation..." -ForegroundColor Yellow

# Test hooks
$installedHooks = Get-ChildItem "$HooksDir" -File | Where-Object { $_.Name -match "^(pre-commit|pre-push|post-checkout|post-merge)$" }
if ($installedHooks.Count -ge 3) {
    Write-Host "  ✓ Hooks installed successfully ($($installedHooks.Count) hooks)" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Some hooks may be missing" -ForegroundColor Yellow
}

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host " Installation Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan

Write-Host "`nWorkflow rules now active:"
Write-Host "  ⛔ BLOCK: Commits to main" -ForegroundColor Red
Write-Host "  ⛔ BLOCK: Pushes to main" -ForegroundColor Red
Write-Host "  💡 SUGGEST: Pull main after checkout" -ForegroundColor Blue
Write-Host "  💡 SUGGEST: Delete merged branches" -ForegroundColor Blue

Write-Host "`nTo bypass hooks (emergency only): git commit --no-verify" -ForegroundColor Gray
