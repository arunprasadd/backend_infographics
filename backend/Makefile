# YouTube Infographic Generator - Backend Makefile

.PHONY: help install dev test lint format clean docker-build docker-run docker-stop

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Run development server"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  clean       - Clean up generated files"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run  - Run with Docker Compose"
	@echo "  docker-stop - Stop Docker containers"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -e .

# Install development dependencies
install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"

# Run development server
dev:
	python run.py

# Run tests
test:
	pytest tests/ -v --cov=. --cov-report=html

# Run tests with specific pattern
test-pattern:
	pytest tests/ -v -k "$(PATTERN)"

# Run linting
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	mypy . --ignore-missing-imports

# Format code
format:
	black .
	isort .

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/

# Docker commands
docker-build:
	docker build -t youtube-infographic-api .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Database commands
db-init:
	python -c "from services.template_service import TemplateService; TemplateService()"

db-reset:
	docker-compose down -v
	docker-compose up -d postgres
	sleep 5
	make db-init

# Load sample data
load-icons:
	python scripts/load_images_to_qdrant.py

# Health check
health:
	curl -f http://localhost:8000/api/health || exit 1

# Production deployment
deploy-prod:
	docker-compose -f docker-compose.prod.yml up -d

# Backup database
backup-db:
	docker-compose exec postgres pg_dump -U postgres infographic_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Restore database
restore-db:
	docker-compose exec -T postgres psql -U postgres infographic_db < $(BACKUP_FILE)