param([int]$Port = 8765, [string]$Model = '', [ValidateSet('openai','gemini')][string]$Provider = 'openai', [string]$AppDirectory = '')
$ErrorActionPreference = 'Stop'
# Resolve the launcher before requesting credentials. Pasted script blocks have no PSScriptRoot.
$launcherRoot = $AppDirectory
if (-not $launcherRoot) { $launcherRoot = $PSScriptRoot }
if (-not $launcherRoot) { $launcherRoot = (Get-Location).Path }
$launcherPath = Join-Path $launcherRoot 'start.ps1'
if (-not (Test-Path -LiteralPath $launcherPath -PathType Leaf)) {
    throw 'Fan-Agent launcher not found. Run the saved start-ai.ps1 file using its full path, or supply -AppDirectory with the fan-agent folder. No API key has been requested.'
}
$keyName = if ($Provider -eq 'gemini') { 'GEMINI_API_KEY' } else { 'OPENAI_API_KEY' }
$previousKey = [Environment]::GetEnvironmentVariable($keyName, 'Process')
$previousProvider = $env:FAN_AGENT_AI_PROVIDER
$previousModel = $env:FAN_AGENT_AI_MODEL
try {
    $env:FAN_AGENT_AI_PROVIDER = $Provider
    if (-not [Environment]::GetEnvironmentVariable($keyName, 'Process')) {
        $secret = Read-Host "$Provider API key (hidden; used only for this server session)" -AsSecureString
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
        try { [Environment]::SetEnvironmentVariable($keyName, [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer), 'Process') }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secret.Dispose() }
    }
    if ($previousProvider -ne $Provider) { $env:FAN_AGENT_AI_MODEL = '' }
    if ($Model) { $env:FAN_AGENT_AI_MODEL = $Model }
    if (-not $env:FAN_AGENT_AI_MODEL) {
        $env:FAN_AGENT_AI_MODEL = Read-Host "$Provider model ID with structured-output support (no models/ prefix)"
    }
    if (-not [Environment]::GetEnvironmentVariable($keyName, 'Process') -or -not $env:FAN_AGENT_AI_MODEL) { throw 'API key and model are required.' }
    Write-Host "Open AI study planner at http://127.0.0.1:$Port . Only submitted request text is sent to $Provider."
    & $launcherPath -Port $Port
} finally {
    [Environment]::SetEnvironmentVariable($keyName, $previousKey, 'Process')
    $env:FAN_AGENT_AI_PROVIDER = $previousProvider
    $env:FAN_AGENT_AI_MODEL = $previousModel
}
