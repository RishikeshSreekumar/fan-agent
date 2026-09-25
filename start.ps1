param([int]$Port = 8765)

$ErrorActionPreference = 'Stop'
$pythonCandidate = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonCandidate)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $pythonCandidate = $pythonCommand.Source
    } else {
        $pythonCandidate = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    }
}
if (-not (Test-Path -LiteralPath $pythonCandidate)) {
    throw 'Python 3.10 or newer is required. Install Python, then run python -m fan_agent serve from this directory.'
}
Push-Location $PSScriptRoot
try {
    & $pythonCandidate -m fan_agent serve --port $Port
} finally {
    Pop-Location
}
