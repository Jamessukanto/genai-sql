.PHONY: dev stop test setup-certs clean test-local setup-db load-data debug-paths

# Development setup
dev: setup-certs
	docker-compose up --build -d
	@echo "Waiting for services to be ready..."
	@sleep 1
	$(MAKE) setup-db
	$(MAKE) load-data

# Setup database schema
setup-db:
	@echo "Setting up database schema..."
	docker-compose run --rm api \
		python -m scripts.setup_data.setup_database \
		--drop-existing

# Load sample data
load-data:
	@echo "Loading sample data..."
	$(MAKE) debug-paths
	docker-compose run --rm api \
		python -m scripts.setup_data.import_data \
		--csv-dir /app/data

# Debug container paths
debug-paths:
	@echo "Debugging container paths..."
	docker-compose run --rm api /bin/sh -c "pwd && echo '\nContents of /app:' && ls -R /app"

# Clean stop (removes volumes)
clean:
	docker-compose down -v

# Run tests against production
test:
	docker-compose run --rm api pytest -s

# Run tests against local environment
test-local: setup-certs
	docker-compose up -d db
	docker-compose run --rm \
		-e API_URL=http://api:8000/api \
		-e PYTHONPATH=/app \
		api pytest -sv tests/

# Setup ssl certificates in the ssl directory
setup-certs:
	mkdir -p ssl
	chmod +x ssl/setup-certs.sh
	./ssl/setup-certs.sh 