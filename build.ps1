# Build the standalone Windows executable plus the portable zip and checksums.
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

python tools\make_icon.py

python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name BoostAudio `
    --icon "assets\volume-amplifier.ico" `
    --version-file "version_info.txt" `
    --add-data "assets\volume-amplifier.ico;assets" `
    app.py

$exe = "dist\BoostAudio.exe"
$zip = "dist\BoostAudio-portable.zip"

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
