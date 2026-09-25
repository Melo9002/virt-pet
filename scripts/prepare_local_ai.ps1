$ErrorActionPreference = "Stop"
$preparer = Join-Path $PSScriptRoot "prepare_local_ai.py"

python $preparer
if ($LASTEXITCODE -ne 0) {
    throw "Local AI preparation failed with exit code $LASTEXITCODE."
}
