# Save Chat Transcript with Timestamp and Screenshot Linking

# Prompt user to copy chat transcript
Write-Host "💬 Before exiting, please copy your ChatGPT transcript to the clipboard. Press Enter when ready."
Read-Host | Out-Null

# Generate timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

# Resolve script and log paths
$scriptRoot = Split-Path $MyInvocation.MyCommand.Path
$logDir = Join-Path $scriptRoot "..\Logs"

# Generate full chat transcript file path
$chatFile = Join-Path $logDir "chat_$timestamp.txt"

# Ensure Logs directory exists
if (-not (Test-Path $logDir)) {
    New-Item -Path $logDir -ItemType Directory | Out-Null
    Write-Host "[*] Created log directory: $logDir"
}

# Save clipboard contents to chat file if valid
try {
    $clipboard = Get-Clipboard -Raw
    if (-not [string]::IsNullOrWhiteSpace($clipboard)) {
        $clipboard | Out-File -FilePath $chatFile -Encoding UTF8 -Force
        Write-Host "[✓] Chat transcript saved to: $chatFile" -ForegroundColor Cyan
    } else {
        Write-Host "[!] Clipboard is empty or not plain text. Chat transcript not saved." -ForegroundColor Yellow
    }
} catch {
    Write-Host "[!] Failed to access or save chat transcript: $($_.Exception.Message)" -ForegroundColor Red
}

# Attempt to capture any screenshots taken by user
$screenshotDir = "$env:USERPROFILE\Pictures\Screenshots"
if (Test-Path $screenshotDir) {
    $destination = Join-Path $logDir "screenshots_$timestamp"
    try {
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
        Copy-Item "$screenshotDir\*.*" -Destination $destination -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "[✓] Screenshots copied to: $destination" -ForegroundColor Green
    } catch {
        Write-Host "[!] Failed to copy screenshots: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "[!] Screenshot directory not found at: $screenshotDir" -ForegroundColor Yellow
}

# Attempt to save image from clipboard (Win + Shift + S workflow)
try {
    $image = Get-Clipboard -Format Image
    if ($image -ne $null -and $image.GetType().Name -eq "Bitmap") {
        $imagePath = Join-Path $logDir "clipboard_image_$timestamp.png"
        $image.Save($imagePath, [System.Drawing.Imaging.ImageFormat]::Png)
        Write-Host "[✓] Clipboard image (Win+Shift+S) saved to: $imagePath" -ForegroundColor Green
    } else {
        Write-Host "[!] Clipboard does not contain a valid image format." -ForegroundColor Yellow
    }
} catch {
    Write-Host "[!] Error checking clipboard image: $($_.Exception.Message)" -ForegroundColor Red
}

# Optional: Write a session metadata JSON file
$metadata = [PSCustomObject]@{
    Timestamp = $timestamp
    TranscriptFile = $chatFile
    ScreenshotsDir = if (Test-Path $destination) { $destination } else { $null }
    ClipboardImage = if (Test-Path $imagePath) { $imagePath } else { $null }
}

$metadataFile = Join-Path $logDir "session-assets_$timestamp.json"
$metadata | ConvertTo-Json -Depth 3 | Out-File -FilePath $metadataFile -Encoding UTF8 -Force
Write-Host "[✓] Session asset metadata written to: $metadataFile" -ForegroundColor Cyan
