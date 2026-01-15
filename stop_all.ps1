# Stop All Services Script
Write-Host "🛑 Stopping all services..." -ForegroundColor Yellow

# Stop all jobs
Get-Job | Stop-Job -ErrorAction SilentlyContinue
Get-Job | Remove-Job -ErrorAction SilentlyContinue

# Kill Python processes (backend)
Get-Process python -ErrorAction SilentlyContinue | 
    Where-Object { $_.MainWindowTitle -like "*backend*" -or $_.CommandLine -like "*app.py*" } | 
    Stop-Process -Force -ErrorAction SilentlyContinue

# Kill Node processes (frontend)
Get-Process node -ErrorAction SilentlyContinue | 
    Where-Object { $_.MainWindowTitle -like "*frontend*" -or $_.CommandLine -like "*vite*" } | 
    Stop-Process -Force -ErrorAction SilentlyContinue

# Kill processes on specific ports
Write-Host "Checking ports 3000 and 5000..." -ForegroundColor Cyan
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -First 1
$port5000 = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -First 1

if ($port3000) {
    Stop-Process -Id $port3000.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Stopped process on port 3000" -ForegroundColor Green
}
if ($port5000) {
    Stop-Process -Id $port5000.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Stopped process on port 5000" -ForegroundColor Green
}

Write-Host "✅ All services stopped." -ForegroundColor Green

