# Load project-session.json into all relevant scripts in one go

$runnerPath = "$PSScriptRoot"
$injectCode = @'
# Load project-session.json
$configPath = Join-Path $PSScriptRoot "..\assets\project-session.json"
$config = Get-Content $configPath | ConvertFrom-Json
$project = $config.project
$part = $config.part
'@

# List of target scripts
$scriptsToUpdate = @(
  "start-hexforge-session.ps1",
  "send-to-engine.ps1",
  "hexforge-shell.ps1",
  "watch-for-obs.ps1",
  "set-project.ps1"
)

foreach ($scriptName in $scriptsToUpdate) {
    $fullPath = Join-Path $runnerPath $scriptName
    if (Test-Path $fullPath) {
        $original = Get-Content $fullPath
        if ($original -notmatch 'project-session\.json') {
            $newContent = $injectCode + "`n`n" + ($original -join "`n")
            Set-Content -Path $fullPath -Value $newContent
            Write-Host "✅ Injected into: $scriptName"
        } else {
            Write-Host "⚠️ Already contains config: $scriptName"
        }
    } else {
        Write-Host "X Not found: $scriptName"
    }
}
