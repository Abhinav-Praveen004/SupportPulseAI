# SupportPulse AI - PowerShell Automation Tasks
param (
    [Parameter(Position=0)]
    [string]$Task = "test"
)

$Python = ".\.venv\Scripts\python.exe"
$Pip = ".\.venv\Scripts\pip.exe"
$Pytest = ".\.venv\Scripts\pytest.exe"

switch ($Task.ToLower()) {
    "setup" {
        Write-Host "Setting up Python virtual environment..." -ForegroundColor Cyan
        python -m venv .venv
        & $Pip install --upgrade pip
        & $Pip install -r backend\requirements.txt
        Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
        Set-Location frontend
        npm install
        Set-Location ..
        Write-Host "Setup completed." -ForegroundColor Green
    }
    "seed" {
        Write-Host "Seeding synthetic dataset (20,000 tickets)..." -ForegroundColor Cyan
        & $Python -m ml.seed_data --count 20000 --output data/tickets.csv
    }
    "train" {
        Write-Host "Training all ML models (M1 - M5)..." -ForegroundColor Cyan
        & $Python -m ml.train_all
    }
    "eval" {
        Write-Host "Evaluating all models and generating reports..." -ForegroundColor Cyan
        & $Python -m ml.evaluate_all
    }
    "test" {
        Write-Host "Running backend tests..." -ForegroundColor Cyan
        & $Pytest backend/tests -v
        Write-Host "Running frontend tests..." -ForegroundColor Cyan
        Set-Location frontend
        npm test
        Set-Location ..
    }
    "test-backend" {
        & $Pytest backend/tests -v
    }
    "test-frontend" {
        Set-Location frontend
        npm test
        Set-Location ..
    }
    "up" {
        docker compose up --build -d
    }
    "down" {
        docker compose down
    }
    default {
        Write-Host "Unknown task: $Task" -ForegroundColor Red
        Write-Host "Available tasks: setup, seed, train, eval, test, test-backend, test-frontend, up, down"
    }
}
