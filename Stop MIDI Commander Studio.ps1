$ErrorActionPreference = "Stop"
$StudioUrl = "http://127.0.0.1:8765"

function Show-StudioMessage([string]$Message, [bool]$IsError = $false) {
    try {
        Add-Type -AssemblyName PresentationFramework
        $icon = if ($IsError) {
            [System.Windows.MessageBoxImage]::Warning
        }
        else {
            [System.Windows.MessageBoxImage]::Information
        }
        [System.Windows.MessageBox]::Show(
            $Message,
            "MIDI Commander Studio",
            [System.Windows.MessageBoxButton]::OK,
            $icon
        ) | Out-Null
    }
    catch {
        Write-Host $Message
    }
}

try {
    Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$StudioUrl/api/shutdown" -TimeoutSec 4 | Out-Null
    Show-StudioMessage "The local MIDI Commander Studio service has stopped."
    exit 0
}
catch {
    Show-StudioMessage "MIDI Commander Studio was not running." $true
    exit 1
}
