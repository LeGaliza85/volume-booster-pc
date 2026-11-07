# Build the Windows installer with Inno Setup 6.
#
# This is separate from build.ps1 because Inno Setup is not a Python dependency:
# the portable build must keep working on a machine that has never heard of it.
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$exe = Join-Path $PSScriptRoot "dist\VolumeBooster.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    throw "Build the portable executable first: powershell -ExecutionPolicy Bypass -File build.ps1"
}

$candidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
)
$iscc = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $iscc) {
    throw "Inno Setup 6 not found. Install it from https://jrsoftware.org/isdl.php and run this again."
}

$version = (Select-String -Path (Join-Path $PSScriptRoot "version.py") -Pattern '^VERSION = "(.+)"').Matches[0].Groups[1].Value
Write-Host "Compiling installer for version $version"

& $iscc "/DAppVersion=$version" (Join-Path $PSScriptRoot "installer\volume-booster.iss")
if ($LASTEXITCODE -ne 0) {
    throw "ISCC failed with exit code $LASTEXITCODE"
}

$setup = Join-Path $PSScriptRoot "dist\VolumeBoosterSetup.exe"
if (-not (Test-Path -LiteralPath $setup)) {
    throw "ISCC reported success but $setup is missing."
}

$hash = (Get-FileHash -LiteralPath $setup -Algorithm SHA256).Hash
$sums = Join-Path $PSScriptRoot "dist\SHA256SUMS.txt"
Add-Content -LiteralPath $sums -Value "$hash  VolumeBoosterSetup.exe" -Encoding ASCII

Write-Host ""
Write-Host "Built:"
Write-Host "  $hash  VolumeBoosterSetup.exe"
