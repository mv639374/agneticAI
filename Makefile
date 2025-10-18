.PHONY: run-api run-web

run-api:
	@echo "Starting backend..."
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-web:
	@echo "Starting frontend..."
	@cd frontend && npm run dev