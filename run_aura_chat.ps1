$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$py = Join-Path $root ".venv/Scripts/python.exe"
if (-not (Test-Path $py)) {
  $py = "python"
}

Write-Host "Installing dependencies..."
& $py -m pip install -r requirements.txt

Write-Host "Running migrations..."
& $py -m alembic upgrade head

Write-Host "Starting API..."
$api = Start-Process -FilePath $py -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" -PassThru -WindowStyle Hidden

try {
  $ready = $false
  for ($i = 0; $i -lt 30; $i++) {
    try {
      $h = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
      if ($h.status -eq "ok") {
        $ready = $true
        break
      }
    } catch {
    }
    Start-Sleep -Milliseconds 500
  }

  if (-not $ready) {
    throw "API did not become healthy in time."
  }

  Write-Host "Getting token..."
  $authBody = @{
    username = "admin"
    password = "admin123"
  } | ConvertTo-Json

  $auth = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/v1/auth/token" -ContentType "application/json" -Body $authBody
  $token = $auth.access_token
  $headers = @{ Authorization = "Bearer $token" }

  $sessionId = "chat-" + [guid]::NewGuid().ToString("N").Substring(0, 8)
  $userId = "local-user-" + [guid]::NewGuid().ToString("N").Substring(0, 8)

  $nimKey = $env:NVIDIA_NIM_API_KEY
  if ([string]::IsNullOrWhiteSpace($nimKey)) {
    $nimKey = $env:NIM_API_KEY
  }

  if ([string]::IsNullOrWhiteSpace($nimKey)) {
    Write-Host "Model mode: STUB (set NVIDIA_NIM_API_KEY for real NIM inference)"
  }
  else {
    Write-Host "Model mode: NVIDIA NIM"
  }

  Write-Host ""
  Write-Host "Aura chat is ready. Type /exit to quit."

  while ($true) {
    $text = Read-Host "You"
    if ([string]::IsNullOrWhiteSpace($text)) {
      continue
    }

    if ($text -eq "/exit") {
      break
    }

    $payload = @{
      user_id = $userId
      session_id = $sessionId
      message = @{
        role = "user"
        content = $text
        modality = "text"
        metadata = @{}
      }
    } | ConvertTo-Json -Depth 6

    try {
      $resp = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/v1/conversation/turn" -Headers $headers -ContentType "application/json" -Body $payload
      Write-Host ""
      Write-Host ("Aura [" + $resp.strategy + " | " + $resp.safety.risk_level + "]:")
      Write-Host $resp.response_text
      Write-Host ""
    } catch {
      Write-Host "Request failed: $($_.Exception.Message)"
    }
  }
}
finally {
  Write-Host "Stopping API..."
  if ($api -and -not $api.HasExited) {
    Stop-Process -Id $api.Id -Force
  }
}
