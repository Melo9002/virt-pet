$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

python -m pip install -e ".[build]"
python -m PyInstaller --noconfirm --clean --onedir --name "virt-pet" virtpet/main.py

$releaseDir = Join-Path $projectRoot "dist\virt-pet"
foreach ($assetDir in @("runtime", "models", "THIRD_PARTY_LICENSES")) {
    $source = Join-Path $projectRoot $assetDir
    if (Test-Path -LiteralPath $source) {
        Copy-Item -LiteralPath $source -Destination $releaseDir -Recurse -Force
    }
}
Copy-Item -LiteralPath (Join-Path $projectRoot "README.md") -Destination $releaseDir -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "LICENSE") -Destination $releaseDir -Force

$archive = Join-Path $projectRoot "dist\virt-pet-windows-x64.zip"
if (Test-Path -LiteralPath $archive) { Remove-Item -LiteralPath $archive -Force }
Compress-Archive -Path (Join-Path $releaseDir "*") -DestinationPath $archive
Write-Host "Built $archive"
