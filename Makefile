.PHONY: setup seed train eval dev test test-backend test-frontend up down lint format clean

PYTHON := ./.venv/Scripts/python
PIP := ./.venv/Scripts/pip
PYTEST := ./.venv/Scripts/pytest

# On Unix-like systems, use bin instead of Scripts
ifeq ($(OS),Windows_NT)
    PYTHON := ./.venv/Scripts/python.exe
    PIP := ./.venv/Scripts/pip.exe
    PYTEST := ./.venv/Scripts/pytest.exe
else
    PYTHON := ./.venv/bin/python
    PIP := ./.venv/bin/pip
    PYTEST := ./.venv/bin/pytest
endif

setup:
	@echo "Setting up Python virtual environment..."
	python -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Setup completed successfully."

seed:
	@echo "Seeding synthetic dataset (20,000 tickets)..."
	$(PYTHON) -m ml.seed_data --count 20000 --output data/tickets.csv

train:
	@echo "Training all ML models (M1 - M5)..."
	$(PYTHON) -m ml.train_all

eval:
	@echo "Running complete evaluation suite and generating reports..."
	$(PYTHON) -m ml.evaluate_all

dev:
	@echo "Starting development servers..."
	powershell -Command "Start-Process cmd -ArgumentList '/k .\.venv\Scripts\uvicorn.exe backend.app.main:app --reload --port 8000'; Start-Process cmd -ArgumentList '/k cd frontend && npm run dev'"

test: test-backend test-frontend

test-backend:
	@echo "Running backend unit and integration tests..."
	$(PYTEST) backend/tests -v

test-frontend:
	@echo "Running frontend unit and component tests..."
	cd frontend && npm test

up:
	@echo "Starting Docker Compose services..."
	docker compose up --build -d

down:
	@echo "Stopping Docker Compose services..."
	docker compose down

lint:
	@echo "Running linters..."
	./.venv/Scripts/ruff check backend ml
	cd frontend && npm run build

format:
	@echo "Formatting code..."
	./.venv/Scripts/ruff format backend ml

clean:
	@echo "Cleaning caches and generated files..."
	rm -rf .pytest_cache frontend/dist frontend/.vite
