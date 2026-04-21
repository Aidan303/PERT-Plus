param(
    [string]$CondaEnvName = "path_gen_build",
    [string]$ExeName = "PERT+",
    [string]$ReleaseName = "PERT+_windows_x64",
    [switch]$KeepDist,
    [switch]$KeepBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$buildDir = Join-Path $projectDir "build"
$distDir = Join-Path $projectDir "dist"
$releaseRoot = Join-Path $projectDir "release"
$releaseDir = Join-Path $releaseRoot $ReleaseName

Write-Host "[1/6] Cleaning prior build artifacts..."
if (Test-Path $buildDir) {
    Remove-Item -Path $buildDir -Recurse -Force
}
if (Test-Path $distDir) {
    Remove-Item -Path $distDir -Recurse -Force
}

Write-Host "[2/6] Building one-file executable with PyInstaller..."
Push-Location $projectDir
try {
    $buildCmd = @(
        "run", "-n", $CondaEnvName,
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", $ExeName,
        "--paths", ".",
        "--collect-submodules", "engine",
        "--collect-submodules", "ui",
        "--collect-submodules", "worker",
        "--collect-submodules", "config",
        "app.py"
    )

    & conda @buildCmd
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

$builtExe = Join-Path $distDir "$ExeName.exe"
if (-not (Test-Path $builtExe)) {
    throw "Expected executable was not found at $builtExe"
}

Write-Host "[3/6] Preparing clean release folder..."
if (Test-Path $releaseDir) {
    Remove-Item -Path $releaseDir -Recurse -Force
}
New-Item -Path $releaseDir -ItemType Directory -Force | Out-Null

Write-Host "[4/6] Copying release artifacts..."
Copy-Item -Path $builtExe -Destination (Join-Path $releaseDir "$ExeName.exe") -Force

$releaseDocs = @(
    "README.md",
    "QUICK_START.md",
    "TROUBLESHOOTING.md",
    "SETTINGS_REFERENCE.md"
)

foreach ($doc in $releaseDocs) {
    $source = Join-Path $projectDir $doc
    if (Test-Path $source) {
        Copy-Item -Path $source -Destination (Join-Path $releaseDir $doc) -Force
    }
}

Write-Host "[5/6] Writing release metadata..."
$exeInRelease = Join-Path $releaseDir "$ExeName.exe"
$hash = Get-FileHash -Path $exeInRelease -Algorithm SHA256
@(
    "File: $($hash.Path)",
    "SHA256: $($hash.Hash)",
    "BuiltOn: $([DateTime]::UtcNow.ToString('u'))",
    "CondaEnv: $CondaEnvName"
) | Set-Content -Path (Join-Path $releaseDir "SHA256SUM.txt") -Encoding ASCII

Write-Host "[6/6] Cleaning post-build folders..."
if (-not $KeepDist -and (Test-Path $distDir)) {
    Remove-Item -Path $distDir -Recurse -Force
}
if (-not $KeepBuild -and (Test-Path $buildDir)) {
    Remove-Item -Path $buildDir -Recurse -Force
}

if ($KeepDist) {
    Write-Host "Dist retained: $distDir"
}
if ($KeepBuild) {
    Write-Host "Build retained: $buildDir"
}

Write-Host "Release complete: $releaseDir"