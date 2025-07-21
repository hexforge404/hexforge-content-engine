Clear-Host
Write-Host "`n[+] Configuring OBS for Automation..." -ForegroundColor Cyan

# Define paths
$obsProfile = "HexForge"
$obsBasePath = "$env:APPDATA\obs-studio\basic\profiles"
$destPath = Join-Path $obsBasePath $obsProfile
$sourceFile = "$PSScriptRoot\assets\OBS-Profiles\devblog\basic.ini"
$backupPath = "${obsBasePath}\${obsProfile}-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# Check for profile folder
if (-not (Test-Path $destPath)) {
    Write-Host "`n❌ OBS profile '$obsProfile' was not found." -ForegroundColor Red
    Write-Host "💡 Open OBS and create a new profile named '$obsProfile' first."
    Read-Host "`nPress Enter to continue..."
    exit
}

# Backup existing profile
Write-Host "📦 Creating backup at: $backupPath"
Copy-Item $destPath $backupPath -Recurse -Force

# Apply custom basic.ini if it exists
if (Test-Path $sourceFile) {
    Copy-Item $sourceFile -Destination (Join-Path $destPath "basic.ini") -Force
    Write-Host "✅ Applied custom basic.ini from: $sourceFile"
} else {
    Write-Host "⚠️ No custom basic.ini found at: $sourceFile"
}

# Ensure output folder exists
$latestVideosPath = "$PSScriptRoot\assets\Latest\Videos"
if (-not (Test-Path $latestVideosPath)) {
    New-Item -ItemType Directory -Path $latestVideosPath | Out-Null
}

Write-Host "`n✅ OBS profile '$obsProfile' is configured at: $destPath"
Write-Host "📼 OBS will auto-record to: $latestVideosPath"

Read-Host "`nPress Enter to continue..."
