# Launch OBS Studio from correct directory with recording flag if not already running

# Get session path from global scope
if (-not $global:HexForgeSessionPath) {
    Write-Host "[!] HexForgeSessionPath is not set. Did you run set-project.ps1?" -ForegroundColor Red
    exit 1
}

# Set the full path to the OBS executable
$obsPath = "C:\Program Files\obs-studio\bin\64bit\obs64.exe"
$obsDir = Split-Path $obsPath
$arguments = @("--startrecording")

Write-Host "[*] Launching OBS from $obsDir with arguments: $($arguments -join ' ')..."


try {
    # Check if OBS is already running by process name
    $existing = Get-Process -Name "obs64" -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "[!] OBS Studio is already running. Skipping launch." -ForegroundColor Yellow
        return
    }

    # Optional enhancement
if ($existing) {
    Write-Host "[!] OBS appears to be running. Attempting to clear stale processes..." -ForegroundColor Yellow
    $existing | Stop-Process -Force
    Start-Sleep -Seconds 1
}


    # Show intended launch details
    Write-Host "[*] Starting OBS from path: $obsPath"
    Write-Host "[*] Using working directory: $obsDir"
    Write-Host "[*] Arguments being passed: $($arguments -join ' ')"

    $obsConfigPath = "$env:APPDATA\obs-studio\global.ini"
if (Test-Path $obsConfigPath) {
    (Get-Content $obsConfigPath) -replace 'SafeModePrompt=true', 'SafeModePrompt=false' |
        Set-Content $obsConfigPath
}
    Write-Host "[*] Updated OBS global.ini to disable Safe Mode prompt."

    # Launch OBS from the specified directory with recording flag
    Start-Process -FilePath $obsPath -ArgumentList $arguments -WorkingDirectory $obsDir -WindowStyle Normal
    Write-Host "[+] OBS Studio launch command executed with --startrecording."

    # Wait a couple seconds to allow the process to start
    Start-Sleep -Seconds 2

    # Verify OBS is running after launch attempt
    $checkProcess = Get-Process -Name "obs64" -ErrorAction SilentlyContinue
    if ($checkProcess) {
        Write-Host "[✓] OBS Studio successfully launched and is running." -ForegroundColor Green
    } else {
        Write-Host "[✗] OBS launch command ran, but OBS process not detected." -ForegroundColor Red
    }
} catch {
    # Catch and report any errors from the try block
    Write-Host "[!] Failed to launch OBS: $($_.Exception.Message)" -ForegroundColor Red
}
