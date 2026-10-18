# PowerShell script to start Flask Video Enhancement API in Docker
# Run this script as: .\start_docker.ps1

Write-Host "🐳 Starting Flask Video Enhancement API in Docker..." -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# Check if Docker is running
Write-Host "🔍 Checking Docker status..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.docker" ".env"
    Write-Host "📝 Please edit .env file and add your OpenAI API key" -ForegroundColor Yellow
    Read-Host "Press Enter after updating .env file"
}

# Stop any existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.flask.yml down

# Build and start the containers
Write-Host "🏗️  Building Docker image..." -ForegroundColor Yellow
docker-compose -f docker-compose.flask.yml build

Write-Host "🚀 Starting Flask API container..." -ForegroundColor Yellow
docker-compose -f docker-compose.flask.yml up -d

# Wait for the service to be ready
Write-Host "⏳ Waiting for Flask API to start..." -ForegroundColor Yellow
$timeout = 60
$elapsed = 0
$healthy = $false

while ($elapsed -lt $timeout -and -not $healthy) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:5003/health" -TimeoutSec 5
        if ($response.status -eq "healthy") {
            $healthy = $true
            Write-Host "✅ Flask API is healthy and ready!" -ForegroundColor Green
        }
    } catch {
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-Host "." -NoNewline -ForegroundColor Yellow
    }
}

if ($healthy) {
    Write-Host ""
    Write-Host "🎉 Flask Video Enhancement API is running!" -ForegroundColor Green
    Write-Host "=================================================" -ForegroundColor Cyan
    Write-Host "🌐 API Base URL: http://localhost:5003" -ForegroundColor White
    Write-Host "🔍 Health Check: http://localhost:5003/health" -ForegroundColor White
    Write-Host "📚 API Documentation: See DEPLOYMENT_GUIDE.md" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 Docker Management Commands:" -ForegroundColor Yellow
    Write-Host "  View logs:    docker-compose -f docker-compose.flask.yml logs -f" -ForegroundColor White
    Write-Host "  Stop:         docker-compose -f docker-compose.flask.yml down" -ForegroundColor White
    Write-Host "  Restart:      docker-compose -f docker-compose.flask.yml restart" -ForegroundColor White
    Write-Host ""
    Write-Host "🔗 Ready for N8N integration!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Flask API failed to start within $timeout seconds" -ForegroundColor Red
    Write-Host "🔍 Check logs with: docker-compose -f docker-compose.flask.yml logs" -ForegroundColor Yellow
}
