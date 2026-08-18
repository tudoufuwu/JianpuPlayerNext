$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

python -m pip install ".[build]"
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed with exit code $LASTEXITCODE" }
python -m unittest discover -s tests -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) { throw "Tests failed with exit code $LASTEXITCODE" }
python -m PyInstaller --noconfirm --clean JianpuPlayerNext.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }

$versionMatch = Select-String -LiteralPath (Join-Path $projectDir "app.py") -Pattern '^APP_VERSION = "([^"]+)"$'
if (-not $versionMatch) {
    throw "APP_VERSION was not found in app.py"
}
$version = $versionMatch.Matches[0].Groups[1].Value
$output = Join-Path $projectDir "dist\JianpuPlayerNext-v$version.exe"
if (-not (Test-Path -LiteralPath $output)) {
    throw "Build output was not created: $output"
}
Write-Host "Built: $output"

