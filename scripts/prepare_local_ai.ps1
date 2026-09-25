$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $projectRoot "runtime"
$modelsDir = Join-Path $projectRoot "models"
$licensesDir = Join-Path $projectRoot "THIRD_PARTY_LICENSES"
$temporaryDir = Join-Path ([IO.Path]::GetTempPath()) ("virt-pet-" + [guid]::NewGuid())

New-Item -ItemType Directory -Force -Path $runtimeDir, $modelsDir, $licensesDir, $temporaryDir | Out-Null

try {
    Write-Host "Finding the latest llama.cpp Windows CPU build..."
    $release = Invoke-RestMethod "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
    $asset = $release.assets |
        Where-Object { $_.name -match "bin-win-cpu-x64\.zip$" } |
        Select-Object -First 1
    if (-not $asset) { throw "No Windows x64 CPU llama.cpp release was found." }

    $archive = Join-Path $temporaryDir "llama.zip"
    $expanded = Join-Path $temporaryDir "llama"
    Invoke-WebRequest $asset.browser_download_url -OutFile $archive
    Expand-Archive -LiteralPath $archive -DestinationPath $expanded
    $server = Get-ChildItem -Path $expanded -Recurse -Filter "llama-server.exe" |
        Select-Object -First 1
    if (-not $server) { throw "llama-server.exe was not present in the release." }
    Copy-Item -Path (Join-Path $server.Directory.FullName "*") -Destination $runtimeDir -Recurse -Force

    $modelName = "smollm2-360m-instruct-q8_0.gguf"
    $modelPath = Join-Path $modelsDir $modelName
    if (-not (Test-Path -LiteralPath $modelPath)) {
        Write-Host "Downloading SmolLM2-360M-Instruct (386 MB)..."
        $modelUrl = "https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct-GGUF/resolve/main/$modelName?download=true"
        Invoke-WebRequest $modelUrl -OutFile $modelPath
    }
    Invoke-WebRequest "https://raw.githubusercontent.com/ggml-org/llama.cpp/master/LICENSE" `
        -OutFile (Join-Path $licensesDir "llama.cpp-MIT.txt")
    Invoke-WebRequest "https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct/raw/main/LICENSE" `
        -OutFile (Join-Path $licensesDir "SmolLM2-Apache-2.0.txt")
    Write-Host "Local AI is ready. Run: python -m virtpet.main --setup"
}
finally {
    if (Test-Path -LiteralPath $temporaryDir) {
        Remove-Item -LiteralPath $temporaryDir -Recurse -Force
    }
}
