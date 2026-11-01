# Build the Windows artefacts.
#
# Two shapes on purpose:
#   * dist\VolumeBooster.exe       one-file portable, what people download directly
#   * dist\VolumeBooster\          folder build, what the installer ships
#
# The installed copy must NOT be one-file: it would unpack itself into %TEMP% on
# every start, and doing that while an update is replacing files is what produced
# "Failed to load Python DLL" after an automatic update.
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

python tools\make_icon.py

python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name VolumeBooster `
    --icon "assets\volume-amplifier.ico" `
    --version-file "version_info.txt" `
    --add-data "assets\volume-amplifier.ico;assets" `
    app.py

python -m PyInstaller --noconfirm --clean --onedir --windowed `
    --name VolumeBooster `
    --icon "assets\volume-amplifier.ico" `
    --version-file "version_info.txt" `
    --add-data "assets\volume-amplifier.ico;assets" `
    app.py

$exe = "dist\VolumeBooster.exe"
$folder = "dist\VolumeBooster\VolumeBooster.exe"
$zip = "dist\VolumeBooster-portable.zip"

if (-not (Test-Path -LiteralPath $folder)) { throw "the folder build is missing: $folder" }

if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
Compress-Archive -LiteralPath $exe, "README.md", "LICENSE" -DestinationPath $zip -CompressionLevel Optimal

$lines = @()
foreach ($file in @($exe, $zip)) {
    $hash = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash
    $lines += "$hash  $(Split-Path -Leaf $file)"
}
$lines | Set-Content -LiteralPath "dist\SHA256SUMS.txt" -Encoding ascii

Write-Host ""
Write-Host "Built:"
$lines | ForEach-Object { Write-Host "  $_" }
Write-Host "  installer payload: $folder"
