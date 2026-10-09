$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Project Python not found: $python" }
& $python -m pip install -r requirements.txt pyinstaller
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
& $python tools/release_preflight.py
if ($LASTEXITCODE -ne 0) { throw "Release preflight failed; see release_preflight.json" }
& $python -m PyInstaller --noconfirm --clean "Simple Solitaire.spec"
if ($LASTEXITCODE -ne 0) { throw "Build failed" }
Copy-Item "PLAYER_README.txt" "dist\Simple Solitaire\READ_ME.txt" -Force
$archive = Join-Path $PSScriptRoot "Simple_Solitaire_Test_Build.zip"
Compress-Archive -Path "dist\Simple Solitaire" -DestinationPath $archive -Force
Write-Host "Share this entire archive: $archive"
