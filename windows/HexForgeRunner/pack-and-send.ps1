# ✅ Validate session state
if (-not $global:HexForgeSessionPath -or -not $global:HexForgeProjectName -or -not $global:HexForgePartNumber) {
    Write-Host "❌ HexForge session info is missing. Did you run set-project.ps1?" -ForegroundColor Red
    exit 1
}

$project = $global:HexForgeProjectName
$part = $global:HexForgePartNumber
$projectPath = $global:HexForgeSessionPath

# 📁 Paths
$logsPath     = Join-Path $projectPath "Logs"
$videosPath   = Join-Path $projectPath "Videos"
$latestPath   = Join-Path $projectPath "Latest"
$zipsPath     = Join-Path $projectPath "Zips"
$screenshotsPath = Join-Path $projectPath "Screenshots"
$transcriptPath  = Join-Path $projectPath "chatgpt-transcript.txt"

# 📦 Define zip name and output path
$timestamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$zipName = "HexForge_Pack_${project}_Part${part}_$timestamp.zip"
$zipPath = Join-Path $latestPath $zipName

# 🧱 Ensure folders exist
@($latestPath, $zipsPath) | ForEach-Object {
    if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
}

# 📦 Collect files to include
$filesToPack = @()

# Log
$latestLog = Get-ChildItem "$logsPath\session_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latestLog) { $filesToPack += $latestLog.FullName }

# Video
$videoFiles = Get-ChildItem "$videosPath\*.mkv"
if ($videoFiles.Count -eq 1) {
    $filesToPack += $videoFiles[0].FullName
} elseif ($videoFiles.Count -gt 1) {
    $latestVideo = $videoFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $filesToPack += $latestVideo.FullName
}

# blog.json (should exist in part folder)
$blogJsonPath = Join-Path $projectPath "blog.json"
if (Test-Path $blogJsonPath) {
    $filesToPack += $blogJsonPath
}

# Transcript
if (Test-Path $transcriptPath) {
    $filesToPack += $transcriptPath
}

# Screenshots
if (Test-Path $screenshotsPath) {
    $screenshots = Get-ChildItem "$screenshotsPath\*.png", "$screenshotsPath\*.jpg"
    if ($screenshots.Count -gt 0) {
        $filesToPack += $screenshots.FullName
    }
}

# Any misc files in Latest/
$additionalFiles = Get-ChildItem "$latestPath\*" -File
if ($additionalFiles.Count -gt 0) {
    $filesToPack += $additionalFiles.FullName
}

# Final filter
$filesToPack = $filesToPack | Where-Object { $_ -and (Test-Path $_) }

# 🧾 Show contents
Write-Host "`n[🔍] Contents of pack folder ($zipPath):"
foreach ($file in $filesToPack) {
    Write-Host " -  " (Split-Path $file -Leaf)
}

# ❌ Abort if empty
if ($filesToPack.Count -eq 0) {
    Write-Host "`n⚠️ No valid files found to package. Aborting."
    Read-Host "Press Enter to return to menu..."
    return
}

# 📦 Compress
Compress-Archive -Path $filesToPack -DestinationPath $zipPath -Force
Copy-Item $zipPath -Destination $zipsPath -Force

# 📏 Metadata
$zipSizeMB = [Math]::Round((Get-Item $zipPath).Length / 1MB, 2)
$zipHash = Get-FileHash $zipPath -Algorithm SHA256

Write-Host "`n📦 Created zip: $zipPath"
Write-Host "📁 Backup copy created in: $zipsPath"
Write-Host "📏 Size: $zipSizeMB MB"
Write-Host "🔐 SHA256: $($zipHash.Hash)"

# 🚀 Send to engine
Write-Host "`n[🚀] Sending to engine via SCP..."
$scpDest = "/mnt/hdd-storage/hexforge-content-engine/uploads/windows/"
$scpTarget = "root@10.0.0.200:`"$scpDest`""

scp $zipPath $scpTarget

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ SCP transfer successful."
    Write-Host "📦 Final confirmation: Blog session fully transferred."
} else {
    Write-Host "`n❌ SCP failed. Please retry manually."
}

Read-Host "`nPress Enter to return to menu..."
