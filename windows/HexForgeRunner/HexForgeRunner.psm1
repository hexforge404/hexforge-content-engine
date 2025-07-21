function Show-HexForgeMenu {
    Clear-Host
    Write-Host "=== HexForgeRunner Menu ===" -ForegroundColor Cyan
    Write-Host "[1] Start Shell Session"
    Write-Host "[2] Send Files to Engine"
    Write-Host "[3] Watch for OBS (auto-exit on OBS close)"
    Write-Host "[4] Build Blog JSON from Logs/Videos"
    Write-Host "[5] Launch OBS Studio (if not running)"
    Write-Host "[6] Full Capture & Upload (OBS + Shell)"
    Write-Host "[7] Configure OBS for Automation"
    Write-Host "============================="
    Write-Host "[0] Exit"
}

function Start-HexForgeRunner {
    while ($true) {
        Show-HexForgeMenu
        $choice = Read-Host "Select an option"

        switch ($choice) {
            "1" {
                & "$PSScriptRoot\hexforge-shell.ps1"
            }
            "2" {
                & "$PSScriptRoot\send-to-engine.ps1"
            }
            "3" {
                & "$PSScriptRoot\watch-for-obs.ps1"
            }
            "4" {
                & "$PSScriptRoot\build-blog-json.ps1"
            }
            "5" {
                & "$PSScriptRoot\launch-obs.ps1"
            }
            "6" {
                Write-Host "`n[+] Starting Full Capture & Upload Session..." -ForegroundColor Cyan
                . "$PSScriptRoot\set-project.ps1"
                if (-not $global:HexForgeSessionPath -or -not $global:HexForgeProjectName -or -not $global:HexForgePartNumber) {
                    Write-Host "[!] HexForge session info is missing. Did you run set-project.ps1?" -ForegroundColor Red
                    continue
                }
                Write-Host "`n[⚙] Pre-session processing started..." -ForegroundColor Yellow

                $launchScript = Join-Path $PSScriptRoot "launch-obs.ps1"
                Write-Host "[*] Running: $launchScript"
                & $launchScript

                $shellScript = Join-Path $PSScriptRoot "hexforge-shell.ps1"
                Write-Host "[*] Running logger inline: $shellScript"
                & $shellScript

                $postScript = Join-Path $PSScriptRoot "stop-hexforge-session.ps1"
                if (Test-Path $postScript) {
                    Write-Host "`n[⚙] Post-session processing started..." -ForegroundColor Yellow
                    & $postScript
                    Write-Host "`n✅ Post-session complete. Assets gathered, blog JSON built, and session sent to engine." -ForegroundColor Green
                } else {
                    Write-Host "`n[!] Post-session script not found: stop-hexforge-session.ps1" -ForegroundColor Red
                }

                Write-Host "`nPress Enter to return to menu..." -ForegroundColor DarkGray
                Read-Host
            }
            "7" {
                & "$PSScriptRoot\configure-obs.ps1"
            }
            "0" {
                Write-Host "Exiting..."
                break
            }
            default {
                Write-Host "Invalid option. Try again." -ForegroundColor Red
            }
        }

        Start-Sleep -Milliseconds 300
        Clear-Host
    }
}

Start-HexForgeRunner
