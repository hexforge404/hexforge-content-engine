# Load project-session.json
$configPath = Join-Path $PSScriptRoot "..\assets\project-session.json"
$config = Get-Content $configPath | ConvertFrom-Json
$project = $config.project
$part = $config.part

do {
    Start-Sleep -Seconds 5
    $obsRunning = Get-Process -Name "obs64" -ErrorAction SilentlyContinue
} while ($obsRunning)

& (Join-Path $PSScriptRoot "stop-hexforge-session.ps1")

