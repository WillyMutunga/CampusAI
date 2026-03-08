$appProcess = Start-Process python -ArgumentList "-u", "app.py" -RedirectStandardOutput "debug_run.log" -RedirectStandardError "debug_run_err.log" -PassThru -NoNewWindow
Write-Host "App started with PID: $($appProcess.Id)"

# Wait for port 5000 to be open
$portArg = "127.0.0.1:5000"
$maxRetries = 60
$retryCount = 0
$portOpen = $false

Write-Host "Waiting for app to initialize..."
while ($retryCount -lt $maxRetries) {
    $con = Test-NetConnection -ComputerName 127.0.0.1 -Port 5000 -InformationLevel Quiet
    if ($con) {
        $portOpen = $true
        Write-Host "Port 5000 is open!"
        break
    }
    Start-Sleep -Seconds 1
    $retryCount++
}

if (-not $portOpen) {
    Write-Host "Timeout waiting for app to start."
    Stop-Process -Id $appProcess.Id -Force
    Get-Content "debug_run.log" -Tail 50
    Get-Content "debug_run_err.log" -Tail 50
    exit 1
}

Start-Sleep -Seconds 2 # Give it a moment to be fully ready

try {
    Write-Host "Sending login request..."
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/login" -Method Post -Body @{
        student_id = "test_user"
        password   = "test_password"
    }
    Write-Host "Login request sent."
}
catch {
    Write-Host "Request failed: $_"
}

Start-Sleep -Seconds 5
Stop-Process -Id $appProcess.Id -Force
Write-Host "App stopped."

Write-Host "--- stdout ---"
Get-Content "debug_run.log" -Tail 100
Write-Host "--- stderr ---"
Get-Content "debug_run_err.log" -Tail 50
