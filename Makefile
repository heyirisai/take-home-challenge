.PHONY: up down build setup migrate seed shell test logs format

# Start all services
up:
	docker compose up -d

# Stop all services
down:
	docker compose down

# Build/rebuild containers
build:
	docker compose build

# Full setup: build, start, migrate, seed
setup: build up
	@echo "Waiting for database to be ready..."
	@sleep 3
	$(MAKE) migrate
	$(MAKE) seed
	@echo ""
	@echo "Setup complete!"
	@echo "  Backend:  http://localhost:8000/api/"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Admin:    http://localhost:8000/admin/"

# Run Django migrations
migrate:
	docker compose exec backend python manage.py migrate

# Load sample data
seed:
	docker compose exec backend python manage.py load_sample_data

# Open Django shell
shell:
	docker compose exec backend python manage.py shell

# Run backend tests
test:
	docker compose exec backend python manage.py test

# View logs
logs:
	docker compose logs -f

# Create a Django superuser
superuser:
	docker compose exec backend python manage.py createsuperuser
