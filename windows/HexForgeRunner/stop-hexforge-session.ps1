# ✅ Load active session info
if (-not $global:HexForgeSessionPath -or -not $global:HexForgeProjectName -or -not $global:HexForgePartNumber) {
    Write-Host "❌ HexForge session not set. Run set-project.ps1 first." -ForegroundColor Red
    exit 1
}

$project = $global:HexForgeProjectName
$part = $global:HexForgePartNumber
$projectPath = $global:HexForgeSessionPath

# 📁 Define key paths
$videosPath   = Join-Path $projectPath "Videos"
$logsPath     = Join-Path $projectPath "Logs"
$latestDir    = Join-Path $projectPath "Latest"
$latestVideos = Join-Path $latestDir "Videos"
$zipsPath     = Join-Path $projectPath "Zips"

# 🧱 Ensure required folders exist
$requiredFolders = @($videosPath, $logsPath, $latestVideos, $zipsPath)
foreach ($folder in $requiredFolders) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
    }
}

# ⏹️ Stop OBS
Write-Host "[⏹] Stopping OBS..."
Start-Process "taskkill" -ArgumentList "/IM obs64.exe /F" -WindowStyle Hidden -Wait
Start-Sleep -Seconds 8

# 📍 Find default Videos folder (where OBS saves by default)
$globalVideosPath = [Environment]::GetFolderPath("MyVideos")
if (-not (Test-Path $globalVideosPath)) {
    Write-Host "[!] Video source folder not found: $globalVideosPath"
    Read-Host "Press Enter to return to menu..."
    return
}

# 🎥 Copy latest MKV video from last 10 mins
Write-Host "[📁] Transferring recording to project folder..."
$cutoffTime = (Get-Date).AddMinutes(-10)

$recentVideo = Get-ChildItem "$globalVideosPath\*.mkv" |
    Where-Object { $_.LastWriteTime -gt $cutoffTime } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($recentVideo) {
    Copy-Item $recentVideo.FullName -Destination $videosPath -Force
    Copy-Item $recentVideo.FullName -Destination $latestVideos -Force
    Write-Host "✅ Copied: $($recentVideo.Name)"
} else {
    Write-Host "⚠️ No recent video found in the last 10 minutes."
}

# ⏱️ Find latest log to detect session start time
$logFile = Get-ChildItem "$logsPath\session_*.log" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

$sessionStartTime = $null
if ($logFile.Name -match 'session_(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})') {
    $datePart = $Matches[1]
    $hour = $Matches[2]; $minute = $Matches[3]; $second = $Matches[4]
    $timestamp = "$datePart $hour`:$minute`:$second"
    $sessionStartTime = Get-Date $timestamp
    Write-Host "🕒 Parsed session start time: $sessionStartTime"
}

# 🖼️ Move screenshots based on session timestamp
if ($sessionStartTime) {
    $screenshotSource = "$env:USERPROFILE\Pictures\Screenshots"
    $screenshotDest   = Join-Path $projectPath "Screenshots"
    if (Test-Path $screenshotSource) {
        $screenshots = Get-ChildItem $screenshotSource -Include *.png, *.jpg -Recurse |
            Where-Object { $_.LastWriteTime -ge $sessionStartTime }

        if ($screenshots.Count -gt 0) {
            New-Item -ItemType Directory -Path $screenshotDest -Force | Out-Null
            foreach ($shot in $screenshots) {
                Move-Item $shot.FullName -Destination $screenshotDest -Force
            }
            Write-Host "🖼️ Moved $($screenshots.Count) screenshot(s) to $screenshotDest"
        } else {
            Write-Host "⚠️ No session screenshots found to move."
        }
    }
}

# 💬 Clipboard prompt for ChatGPT transcript
Write-Host "`n📋 Paste your ChatGPT transcript into the clipboard now."
Write-Host "Press ENTER when ready to save clipboard contents to file." -ForegroundColor Cyan
Read-Host
try {
    $clipText = Get-Clipboard
    if (-not [string]::IsNullOrWhiteSpace($clipText)) {
        $chatPath = Join-Path $projectPath "chatgpt-transcript.txt"
        $clipText | Out-File -Encoding UTF8 $chatPath
        Write-Host "✅ Saved transcript to: $chatPath"
    } else {
        Write-Host "⚠️ Clipboard empty — no transcript saved."
    }
} catch {
    Write-Host "❌ Failed to read clipboard: $_"
}

# 🔧 Run blog builder and pack sender
& "$PSScriptRoot\build-blog-json.ps1"
& "$PSScriptRoot\pack-and-send.ps1"

Write-Host "`n✅ Post-session complete. Assets gathered, blog JSON built, and session sent to engine."
Read-Host "Press Enter to return to menu..."
