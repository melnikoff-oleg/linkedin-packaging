$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$PythonCommand = Get-Command python -ErrorAction SilentlyContinue
$PythonArgs = @()
if (-not $PythonCommand) {
    $PythonCommand = Get-Command py -ErrorAction SilentlyContinue
    $PythonArgs = @("-3")
}
if (-not $PythonCommand) {
    throw "Python 3.10 or newer is required. Install it from https://www.python.org/downloads/ with Python on PATH, reopen PowerShell, then rerun setup."
}
& $PythonCommand.Source @PythonArgs -c 'import sys; sys.exit("Python 3.10 or newer is required.") if sys.version_info < (3, 10) else None'
if ($LASTEXITCODE -ne 0) { throw "Python version check failed. Install Python 3.10 or newer and ensure it is on PATH." }
& $PythonCommand.Source @PythonArgs -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed. Check the Python installation and folder permissions." }
& .\.venv\Scripts\python.exe -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed. Check your network connection and rerun setup." }
& .\.venv\Scripts\python.exe -m playwright install chromium
if ($LASTEXITCODE -ne 0) { throw "Chromium installation failed. Check your network connection and rerun setup." }
& .\.venv\Scripts\python.exe -c 'from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(); b.close(); p.stop()'
if ($LASTEXITCODE -ne 0) { throw "Chromium could not launch. Review the message above, then rerun setup." }
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Write-Host "Setup complete. Open .env and add your own KIE_AI_API_KEY."
Write-Host "Also add APIFY_API_KEY for --linkedin, or FIRECRAWL_API_KEY for --website."
Write-Host "Then run the Windows example command in README.md. Generation uses paid provider credits."
