# pack-and-archive.ps1

#
Moves contents of Latest folder into a finalized projectpart folder
and updates lastUsed timestamp in project-session.json.
#

# Load project + part from config
$configPath = $PSScriptRoot..Assetsproject-session.json
$config = Get-Content $configPath  ConvertFrom-Json
$project = $config.project
$part = $config.part

# Compose target folder name
$sessionFolderName = ${project}_Part${part}
$projectDir = Join-Path $PSScriptRoot..AssetsProjects $sessionFolderName
$logsTarget = Join-Path $projectDir Logs
$videosTarget = Join-Path $projectDir Videos

# Source folders
$latestDir = Join-Path $PSScriptRoot..Assets Latest
$latestLogs = Join-Path $latestDir Logs
$latestVideos = Join-Path $latestDir Videos

# Create folders if missing
$folders = @($projectDir, $logsTarget, $videosTarget)
foreach ($folder in $folders) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder  Out-Null
        Write-Host 📁 Created $folder
    }
}

# Move logs
Get-ChildItem -Path $latestLogs -File  ForEach-Object {
    Move-Item $_.FullName -Destination $logsTarget
    Write-Host 📝 Moved log $($_.Name)
}

# Move videos
Get-ChildItem -Path $latestVideos -File  ForEach-Object {
    Move-Item $_.FullName -Destination $videosTarget
    Write-Host 🎥 Moved video $($_.Name)
}

# Update lastUsed timestamp
$config.lastUsed = (Get-Date).ToString('yyyy-MM-dd HHmmss')
$config  ConvertTo-Json -Depth 3  Set-Content $configPath
Write-Host ✅ Updated lastUsed timestamp in config.

# Optional auto-send to engine
# .send-to-engine.ps1
