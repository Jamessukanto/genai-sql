.PHONY: dev stop test setup-certs clean test-local setup-db load-data 

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
	docker-compose run --rm api \
		python -m scripts.setup_data.import_data \
		--csv-dir /app/data

# Clean stop (removes volumes)
clean:
	docker-compose down -v

test:
	docker-compose run --rm api pytest tests/test_mandatory_queries.py -s

# Setup ssl certificates in the ssl directory
setup-certs:
	mkdir -p ssl
	chmod +x ssl/setup-certs.sh
	./ssl/setup-certs.sh 