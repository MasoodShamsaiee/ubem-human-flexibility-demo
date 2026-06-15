param(
    [int]$Port = 8501,
    [string]$CondaEnv = "urban-energy-core",
    [string]$Address = "127.0.0.1",
    [int]$TimeoutSeconds = 45,
    [switch]$Foreground
)

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$OutLog = Join-Path $ProjectRoot "streamlit_server.out.log"
$ErrLog = Join-Path $ProjectRoot "streamlit_server.err.log"
$RestartLog = Join-Path $ProjectRoot "streamlit_restart.log"
$HealthUrl = "http://$Address`:$Port/?v=$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"

$ErrorActionPreference = "Stop"
Remove-Item -LiteralPath $RestartLog -Force -ErrorAction SilentlyContinue

function Write-Step {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Message
    Write-Host $line
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            Add-Content -LiteralPath $RestartLog -Value $line -ErrorAction Stop
            return
        }
        catch {
            Start-Sleep -Milliseconds 150
        }
    }
    Write-Host "[warn] Could not write to $RestartLog; continuing."
}

Write-Step "Project: $ProjectRoot"
Write-Step "Stopping existing listeners on port $Port"
$connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
$owners = $connections | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -ne 0 }
if (-not $owners) {
    Write-Step "No existing Streamlit process found on port $Port"
}
foreach ($owner in $owners) {
    $process = Get-Process -Id $owner -ErrorAction SilentlyContinue
    if ($process) {
        Write-Step "Stopping PID $owner ($($process.ProcessName))"
        Stop-Process -Id $owner -Force -ErrorAction SilentlyContinue
    }
}

Write-Step "Clearing local Python caches"
Get-ChildItem -Force -Directory `
    (Join-Path $ProjectRoot "app\__pycache__"), `
    (Join-Path $ProjectRoot "src\__pycache__"), `
    (Join-Path $ProjectRoot "tests\__pycache__") `
    -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Step "Resetting logs"
Remove-Item -LiteralPath $OutLog, $ErrLog -Force -ErrorAction SilentlyContinue

Write-Step "Starting Streamlit on $Address`:$Port with conda env '$CondaEnv'"
$arguments = @(
    "run", "-n", $CondaEnv,
    "python", "-m", "streamlit", "run", "app/streamlit_app.py",
    "--server.address", $Address,
    "--server.port", $Port,
    "--server.headless", "true",
    "--browser.gatherUsageStats", "false"
)
if ($Foreground) {
    Write-Step "Foreground mode: Streamlit output will stay attached to this terminal"
    Write-Step "Open after startup: $HealthUrl"
    & conda @arguments
    exit $LASTEXITCODE
}

$process = Start-Process `
    -FilePath "conda" `
    -ArgumentList $arguments `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $OutLog `
    -RedirectStandardError $ErrLog `
    -PassThru
Write-Step "Started PID $($process.Id)"

Write-Step "Waiting for health check: $HealthUrl"
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$ready = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 2
    if ($process.HasExited) {
        Write-Step "ERROR: Streamlit process exited with code $($process.ExitCode)"
        break
    }
    try {
        $response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $ready = $true
            Write-Step "READY: HTTP 200"
            Write-Step "Open: $HealthUrl"
            break
        }
        Write-Step "Waiting: HTTP $($response.StatusCode)"
    }
    catch {
        Write-Step "Waiting: $($_.Exception.Message)"
    }
}

if (-not $ready) {
    Write-Step "NOT READY after $TimeoutSeconds seconds"
    if (Test-Path $ErrLog) {
        Write-Step "Last stderr lines:"
        Get-Content $ErrLog -Tail 40
    }
    if (Test-Path $OutLog) {
        Write-Step "Last stdout lines:"
        Get-Content $OutLog -Tail 40
    }
    exit 1
}

Write-Step "Recent stderr:"
if (Test-Path $ErrLog) {
    $stderr = Get-Content $ErrLog -Tail 12
    if ($stderr) { $stderr } else { Write-Output "(empty)" }
}
else {
    Write-Output "(missing)"
}

Write-Step "Done"
