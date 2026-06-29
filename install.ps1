$ErrorActionPreference = "Stop"

Write-Host "🐸 Installing CronFrog..." -ForegroundColor Green

$installDir = "$env:LOCALAPPDATA\CronFrog\bin"
if (-Not (Test-Path -Path $installDir)) {
    New-Item -ItemType Directory -Force -Path $installDir | Out-Null
}

$repo = "shayansaha85/cronfrog"
$releaseApiUrl = "https://api.github.com/repos/$repo/releases/latest"

Write-Host "Fetching latest release information..."
try {
    $releaseData = Invoke-RestMethod -Uri $releaseApiUrl
} catch {
    Write-Error "Failed to fetch release info. Make sure you have published a GitHub Release."
    exit 1
}

$asset = $releaseData.assets | Where-Object { $_.name -match "cronfrog-windows.exe" }

if (-Not $asset) {
    Write-Error "Could not find a Windows release (cronfrog-windows.exe) on GitHub."
    exit 1
}

$downloadUrl = $asset.browser_download_url
$targetFile = "$installDir\cronfrog.exe"

Write-Host "Downloading from $downloadUrl..."
Invoke-WebRequest -Uri $downloadUrl -OutFile $targetFile

Write-Host "✅ CronFrog installed to $targetFile" -ForegroundColor Green

# Add to User PATH if not exists
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notmatch [regex]::Escape($installDir)) {
    Write-Host "Adding $installDir to your User PATH..."
    $newPath = "$userPath;$installDir"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    
    # Also update current session
    $env:PATH = "$env:PATH;$installDir"
    
    Write-Host "PATH updated successfully. You can now use the 'cronfrog' command." -ForegroundColor Cyan
} else {
    Write-Host "Directory is already in PATH. You can use the 'cronfrog' command." -ForegroundColor Cyan
}