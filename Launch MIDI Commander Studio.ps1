[CmdletBinding()]
param(
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$StudioRoot = $PSScriptRoot
$StudioVenv = Join-Path $StudioRoot ".studio-venv-windows"
$StudioRuntime = Join-Path $StudioRoot ".studio-runtime"
$StudioUrl = "http://127.0.0.1:8765"
$InstallLog = Join-Path $StudioRuntime "install-windows.log"
$ServerLog = Join-Path $StudioRuntime "server-windows.log"
$ServerErrorLog = Join-Path $StudioRuntime "server-windows-error.log"
$PidFile = Join-Path $StudioRuntime "server-windows.pid"

function Test-StudioHealth {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "$StudioUrl/api/health" -TimeoutSec 2
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

function Show-StudioError([string]$Message) {
    try {
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show(
            $Message,
            "MIDI Commander Studio",
            [System.Windows.MessageBoxButton]::OK,
            [System.Windows.MessageBoxImage]::Error
        ) | Out-Null
    }
    catch {
        Write-Host $Message -ForegroundColor Red
    }
}

try {
    New-Item -ItemType Directory -Force -Path $StudioRuntime | Out-Null

    if (Test-StudioHealth) {
        if (-not $NoBrowser) { Start-Process $StudioUrl }
        exit 0
    }

    $VenvPython = Join-Path $StudioVenv "Scripts\python.exe"
    if (-not (Test-Path $VenvPython)) {
        Write-Host "Preparing MIDI Commander Studio for first use..."
        $PythonLauncher = Get-Command "py.exe" -ErrorAction SilentlyContinue
        if ($PythonLauncher) {
            & $PythonLauncher.Source -3 -m venv $StudioVenv
        }
        else {
            $PythonCommand = Get-Command "python.exe" -ErrorAction SilentlyContinue
            if (-not $PythonCommand) {
                throw "Python 3 was not found. Install it from python.org and enable 'Add Python to PATH', then launch Studio again."
            }
            & $PythonCommand.Source -m venv $StudioVenv
        }
        if ($LASTEXITCODE -ne 0) { throw "Python could not create the private Studio environment." }
    }

    & $VenvPython -c "import fastapi, mido, pandas, rtmidi, uvicorn" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing Studio components..."
        & $VenvPython -m pip install --disable-pip-version-check -r (Join-Path $StudioRoot "studio\requirements.txt") *>&1 | Tee-Object -FilePath $InstallLog
        if ($LASTEXITCODE -ne 0) {
            throw "Studio setup failed. See $InstallLog for details."
        }
    }

    $env:PYTHONUTF8 = "1"
    $process = Start-Process `
        -FilePath $VenvPython `
        -ArgumentList @("-m", "studio.backend.app") `
        -WorkingDirectory $StudioRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $ServerLog `
        -RedirectStandardError $ServerErrorLog `
        -PassThru
    Set-Content -Path $PidFile -Value $process.Id

    for ($attempt = 0; $attempt -lt 80; $attempt++) {
        if (Test-StudioHealth) {
            if (-not $NoBrowser) { Start-Process $StudioUrl }
            exit 0
        }
        Start-Sleep -Milliseconds 200
    }

    throw "Studio did not start. See $ServerErrorLog for details."
}
catch {
    Show-StudioError $_.Exception.Message
    Write-Error $_.Exception.Message
    exit 1
}
