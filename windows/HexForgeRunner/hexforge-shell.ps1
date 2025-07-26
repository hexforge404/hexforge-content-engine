param()

# 🔒 Validate session path is available
if (-not $global:HexForgeSessionPath -or -not $global:HexForgeProjectName -or -not $global:HexForgePartNumber) {
    Write-Host "[!] HexForge session info is missing. Did you run set-project.ps1?" -ForegroundColor Red
    exit 1
}

$project = $global:HexForgeProjectName
$part = $global:HexForgePartNumber
$sessionPath = $global:HexForgeSessionPath
$LogDir = Join-Path $sessionPath "Logs"

# 🕒 Generate log file path
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = Join-Path $LogDir "session_$timestamp.log"

# 🖼️ Display ASCII banner if available
$bannerPath = Join-Path $PSScriptRoot "assets\hexforge-banner.txt"
if (Test-Path $bannerPath) {
    Get-Content $bannerPath | ForEach-Object { Write-Host $_ -ForegroundColor Green }
}

Write-Host "`n🪓 HexForge Logger started for $project / $part"
Write-Host "📁 Logging to: $logFile`n"

Start-Transcript -Path $logFile -Append

Write-Host "`n✅ Logger is active. Type 'exit' to end this session and continue..." -ForegroundColor Green

# 🖥️ Inline REPL
while ($true) {
    $cwd = Get-Location
    $user = $env:USERNAME
    $prompt = "$user $cwd>"

    $cmd = Read-Host -Prompt $prompt
    if ($cmd -eq 'exit') { break }

    try {
        Invoke-Expression $cmd 2>&1 | ForEach-Object {
            Write-Host $_
        }
    } catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
    }
}

Stop-Transcript
Write-Host "`n📁 Session log saved to: $logFile" -ForegroundColor DarkGray
# 🛑 End of session 
Write-Host "🪓 HexForge Logger session ended. Goodbye!" -ForegroundColor Green
