$ports = 8000, 5000, 5500

foreach ($port in $ports) {
  $processIds = netstat -ano |
    Select-String (":" + $port + " ") |
    ForEach-Object { ($_ -split '\s+')[-1] } |
    Where-Object { $_ -match '^\d+$' -and [int]$_ -gt 4 } |
    Sort-Object -Unique

  foreach ($processId in $processIds) {
    taskkill /PID $processId /T /F | Out-Null
  }
}

Write-Host "Ports 8000/5000/5500 cleaned."
