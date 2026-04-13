$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

& ".\venv\Scripts\Activate.ps1"
Set-Location ".\backend"

python setup_db.py
if ($LASTEXITCODE -ne 0) {
  throw "setup_db.py failed"
}

python run.py
