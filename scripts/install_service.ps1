# Git Workflow Guardian - Service Installation Script
param(
    [Parameter(Mandatory=$false)]
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$ServiceName = "GitWorkflowGuardian"
$ServiceDisplayName = "Git Workflow Guardian Monitor"
$ServiceDescription = "Monitors git repositories for workflow compliance"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$ServiceScript = Join-Path $ProjectRoot "service\monitor.py"
$PythonExe = "python"  # Assumes python in PATH

if ($Uninstall) {
    Write-Host "Uninstalling $ServiceDisplayName..." -ForegroundColor Yellow

    # Remove scheduled task
    $task = Get-ScheduledTask -TaskName $ServiceName -ErrorAction SilentlyContinue
    if ($task) {
        Unregister-ScheduledTask -TaskName $ServiceName -Confirm:$false
        Write-Host "  ✓ Scheduled task removed" -ForegroundColor Green
    } else {
        Write-Host "  ℹ No scheduled task found" -ForegroundColor Gray
    }

    Write-Host "Uninstallation complete!" -ForegroundColor Green
    exit 0
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Git Workflow Guardian - Service Installer" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

Write-Host "`n[1/3] Validating environment..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = & $PythonExe --version 2>&1
    Write-Host "  ✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Error "Python not found in PATH. Please install Python 3.8+ and try again."
    exit 1
}

# Check service script
if (-not (Test-Path $ServiceScript)) {
    Write-Error "Service script not found: $ServiceScript"
    exit 1
}
Write-Host "  ✓ Service script found" -ForegroundColor Green

Write-Host "`n[2/3] Installing service..." -ForegroundColor Yellow

# Create scheduled task (runs at login)
$action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ServiceScript`""
$trigger = New-ScheduledTaskTrigger -AtLogon
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Limited

try {
    Register-ScheduledTask `
        -TaskName $ServiceName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description $ServiceDescription `
        -Force | Out-Null

    Write-Host "  ✓ Scheduled task created" -ForegroundColor Green
} catch {
    Write-Error "Failed to create scheduled task: $_"
    exit 1
}

Write-Host "`n[3/3] Starting service..." -ForegroundColor Yellow

# Start task
Start-ScheduledTask -TaskName $ServiceName
Start-Sleep -Seconds 2

# Verify running
$task = Get-ScheduledTask -TaskName $ServiceName
if ($task.State -eq "Running") {
    Write-Host "  ✓ Service started successfully" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Service may not be running (check Task Scheduler)" -ForegroundColor Yellow
}

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host " Installation Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan

Write-Host "`nService details:"
Write-Host "  Name: $ServiceName" -ForegroundColor Gray
Write-Host "  Status: Running at login" -ForegroundColor Gray
Write-Host "  Script: $ServiceScript" -ForegroundColor Gray

Write-Host "`nTo uninstall: .\install_service.ps1 -Uninstall" -ForegroundColor Gray
Write-Host "To view logs: Check Windows Event Viewer or console output" -ForegroundColor Gray
