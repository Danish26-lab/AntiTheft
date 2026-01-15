# Smart Anti-Theft System - Start All Services
# This script starts backend, frontend, and optionally device agents

Write-Host "🚀 Starting Smart Anti-Theft System..." -ForegroundColor Green
Write-Host "=" -repeat 50
Write-Host ""

# Get the project root directory
$projectRoot = $PSScriptRoot
if (!$projectRoot) {
    $projectRoot = Get-Location
}

# Function to check if port is in use
function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue 2>$null
    return $connection
}

# Check ports
Write-Host "Checking ports..." -ForegroundColor Cyan
if (Test-Port -Port 5000) {
    Write-Host "⚠️  Port 5000 (Backend) is already in use" -ForegroundColor Yellow
}
if (Test-Port -Port 3000) {
    Write-Host "⚠️  Port 3000 (Frontend) is already in use" -ForegroundColor Yellow
}
Write-Host ""

# Start Backend
Write-Host "📦 Starting Backend Server..." -ForegroundColor Cyan
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot
    Set-Location backend
    python app.py
} -Name "BackendServer"

Start-Sleep -Seconds 2
if (Test-Port -Port 5000) {
    Write-Host "✅ Backend running on http://localhost:5000" -ForegroundColor Green
} else {
    Write-Host "⏳ Backend starting..." -ForegroundColor Yellow
}

# Start Frontend
Write-Host "🌐 Starting Frontend Server..." -ForegroundColor Cyan
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot
    Set-Location frontend
    npm run dev
} -Name "FrontendServer"

Start-Sleep -Seconds 3
if (Test-Port -Port 3000) {
    Write-Host "✅ Frontend running on http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "⏳ Frontend starting..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" -repeat 50
Write-Host "🎉 All Services Started!" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Access Points:" -ForegroundColor Cyan
Write-Host "  • Dashboard:  http://localhost:3000" -ForegroundColor White
Write-Host "  • QR Scanner:  http://192.168.0.19:3000/qr-scanner" -ForegroundColor White
Write-Host "  • Backend API: http://localhost:5000/api/health" -ForegroundColor White
Write-Host ""
Write-Host "🔐 Default Login:" -ForegroundColor Cyan
Write-Host "  • Email: admin@antitheft.com" -ForegroundColor White
Write-Host "  • Password: admin123" -ForegroundColor White
Write-Host ""
Write-Host "📊 Service Status:" -ForegroundColor Cyan
Write-Host "  • Backend:  Job ID $($backendJob.Id)" -ForegroundColor White
Write-Host "  • Frontend: Job ID $($frontendJob.Id)" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  To stop all services:" -ForegroundColor Yellow
Write-Host "  • Press Ctrl+C or close this window" -ForegroundColor White
Write-Host "  • Or run: .\stop_all.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Monitoring services... (Press Ctrl+C to stop)" -ForegroundColor Gray
Write-Host ""

# Monitor and show output
try {
    while ($true) {
        Start-Sleep -Seconds 5
        
        # Check if jobs are still running
        $backendStatus = Get-Job -Name "BackendServer" -ErrorAction SilentlyContinue
        $frontendStatus = Get-Job -Name "FrontendServer" -ErrorAction SilentlyContinue
        
        if ($backendStatus -and $backendStatus.State -eq "Failed") {
            Write-Host "❌ Backend failed! Check logs above." -ForegroundColor Red
        }
        if ($frontendStatus -and $frontendStatus.State -eq "Failed") {
            Write-Host "❌ Frontend failed! Check logs above." -ForegroundColor Red
        }
    }
} catch {
    Write-Host "`n🛑 Stopping all services..." -ForegroundColor Yellow
} finally {
    # Cleanup
    Get-Job | Stop-Job -ErrorAction SilentlyContinue
    Get-Job | Remove-Job -ErrorAction SilentlyContinue
    Write-Host "✅ All services stopped." -ForegroundColor Green
}

