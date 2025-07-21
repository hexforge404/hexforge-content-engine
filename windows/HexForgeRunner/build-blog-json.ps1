# ✅ Validate session path
if (-not $global:HexForgeSessionPath -or -not $global:HexForgeProjectName -or -not $global:HexForgePartNumber) {
    Write-Host "❌ HexForge session info is missing. Run set-project.ps1 first." -ForegroundColor Red
    exit 1
}

# Inject environment variables and run Node script
$env:HEXFORGE_PROJECT = $global:HexForgeProjectName
$env:HEXFORGE_PART = $global:HexForgePartNumber
$env:HEXFORGE_SESSION_PATH = $global:HexForgeSessionPath

node "$PSScriptRoot\buildBlogJsonFromAssets.js"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to build blog.json. Check the Node.js script for errors." -ForegroundColor Red
    exit $LASTEXITCODE
}