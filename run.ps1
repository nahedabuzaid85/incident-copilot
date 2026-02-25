# Run the Incident Co-Pilot API from project root (no need to set PYTHONPATH manually)
Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot
uvicorn app.main:app --reload --port 8000
