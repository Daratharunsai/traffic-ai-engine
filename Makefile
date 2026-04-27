.PHONY: help install test run-api run-frontend clean docker-build docker-up docker-down

help:
	@echo "Traffic AI Engine - Available Commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make run-api      - Run FastAPI backend"
	@echo "  make run-frontend - Run Streamlit frontend"
	@echo "  make clean        - Clean generated files"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

run-api:
	uvicorn api.main:app --reload --port 8000

run-frontend:
	streamlit run frontend/app.py --server.port 8501

clean:
	rm -rf data/input/* data/output/* static/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f
