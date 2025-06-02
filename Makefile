.PHONY: dev clean test setup-ssl-certs setup-db seed-db

setup-ssl-certs:
	@echo "Setting up ssl certs..."
	chmod +x ./backend/core/setup-ssl-certs.sh
	./backend/core/setup-ssl-certs.sh 

setup-db:
	@echo "Setting up database schema..."
	env $(cat .env | xargs) docker-compose run --rm backend \
		python -m core.setup_data.setup_database \
		--drop-existing

seed-db:
	@echo "Loading sample data..."
	env $(cat .env | xargs) docker-compose run --rm backend \
		python -m core.setup_data.import_data \
		--csv-dir ./data

dev: setup-ssl-certs
	docker-compose up --build -d
	@echo "Waiting for services to be ready..."
	@echo "Frontend should now be running on http://localhost:8501"
	@sleep 4
	$(MAKE) setup-db
	$(MAKE) seed-db

test:
	docker-compose run --rm backend pytest tests/test_mandatory_queries.py -s

clean:
	docker-compose down -v

