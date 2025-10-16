.PHONY: run-api run-web

run-api:
	@echo "Starting backend..."
	@cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-web:
	@echo "Starting frontend..."
	@cd frontend && npm run dev