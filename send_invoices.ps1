# PowerShell script to run the Python email script
$scriptPath = "C:\inetpub\flaskapps\justlawns_mail"
$pythonScript = "send_invoices_google_oauth.py"
$venvActivate = ".\DispatchMail\Scripts\Activate.ps1"
$logFile = "C:\inetpub\flaskapps\justlawns_mail\email_script_log.txt"

try {
    # Change to the script directory
    Set-Location -Path $scriptPath

    # Activate the virtual environment
    if (Test-Path $venvActivate) {
        & $venvActivate
    } else {
        Write-Error "Virtual environment activation script not found at $venvActivate"
        exit 1
    }

    # Run the Python script and capture output
    Write-Host "Running Python script: $pythonScript"
    $pythonOutput = python $pythonScript 2>&1 | Tee-Object -FilePath $logFile
    Write-Host $pythonOutput

    # Deactivate the virtual environment
    deactivate
}
catch {
    Write-Error "An error occurred: $_"
    Add-Content -Path $logFile -Value "Error: $_"
    exit 1
}
finally {
    # Return to original directory
    Set-Location -Path $PSScriptRoot
}