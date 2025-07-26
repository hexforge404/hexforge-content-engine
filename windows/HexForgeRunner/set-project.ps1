# === HexForgeRunner: set-project.ps1 ===

# Define base paths
$modulePath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectsPath = Join-Path $modulePath "projects"
$sessionStateFile = Join-Path $modulePath "last-session.json"

# Load last session (if exists)
if (Test-Path $sessionStateFile) {
    $lastSession = Get-Content $sessionStateFile | ConvertFrom-Json
    $lastProject = $lastSession.project
    $lastPart = $lastSession.part
} else {
    $lastProject = ""
    $lastPart = ""
}

# Prompt for project name with smart reuse text
$lastDisplayProject = if ($lastProject) { " [$lastProject to reuse]" } else { "" }
$projectPrompt = "Enter project name$lastDisplayProject"
$projectName = Read-Host $projectPrompt
if (-not $projectName) { $projectName = $lastProject }

# Prompt for part number with smart reuse text
$lastDisplayPart = if ($lastPart) { " [$lastPart to reuse]" } else { "" }
$partPrompt = "Enter part number$lastDisplayPart"
$partNumber = Read-Host $partPrompt
if (-not $partNumber) { $partNumber = $lastPart }

# Handle full reuse: ask if reuse or bump
if ($projectName -eq $lastProject -and $partNumber -eq $lastPart) {
    Write-Host "⚠️  You are about to reuse the same session: $projectName / $partNumber" -ForegroundColor Yellow
    $reuseChoice = Read-Host "(y)es to reuse  (b)ump part number  (n)o to cancel"

    switch ($reuseChoice.ToLower()) {
        "y" {
            Write-Host "✅ Reusing same session."
        }
        "b" {
            if ($partNumber -match "^part(\d+)$") {
                $nextNum = [int]$Matches[1] + 1
                $partNumber = "part$nextNum"
                Write-Host "🔁 Bumping part number → $partNumber"
            } else {
                $partNumber = $partNumber + "_next"
                Write-Host "🔁 Renaming part to: $partNumber"
            }
        }
        default {
            Write-Host "❌ Cancelled by user." -ForegroundColor Red
            exit
        }
    }
}

# Define final paths
$projectRoot = Join-Path $projectsPath $projectName
$partPath = Join-Path $projectRoot $partNumber

# Confirm if already exists
if (Test-Path $partPath) {
    Write-Host "⚠️  Project '$projectName' / Part '$partNumber' already exists." -ForegroundColor Yellow
    $response = Read-Host "Do you want to continue with this project and part? (Y to confirm / N to cancel)"
    if ($response -ne "Y" -and $response -ne "y") {
        Write-Host "❌ Operation cancelled." -ForegroundColor Red
        exit
    }
} else {
    # Create project/part folders
    New-Item -Path $partPath -ItemType Directory -Force | Out-Null
    @("Logs", "Videos", "Screenshots", "Zips", "Latest") | ForEach-Object {
        New-Item -Path (Join-Path $partPath $_) -ItemType Directory -Force | Out-Null
    }
    Write-Host "`n✅ Created project folder: $projectRoot" -ForegroundColor Green
    Write-Host "✅ Created part folder:    $partPath" -ForegroundColor Green
}

# Save this session
@{
    project = $projectName
    part    = $partNumber
} | ConvertTo-Json | Out-File -Encoding UTF8 $sessionStateFile

# Export globally
$global:HexForgeProjectName = $projectName
$global:HexForgePartNumber = $partNumber
$global:HexForgeSessionPath = $partPath

# Confirm to user
Write-Host "`n✅ Project loaded and folders ready."
Write-Host "   Project: $projectName"
Write-Host "   Part:    $partNumber"
Write-Host "   Path:    $partPath`n"
