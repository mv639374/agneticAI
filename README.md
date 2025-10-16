# AgenticAI

---

## **TECH-STACK**

**Languages:** Python (3.12), TypeScript, JavaScript, SQL, Bash

**AI/ML:** LangChain, LangGraph, LangSmith, MCP, GPT-4, Claude, Prompt Engineering, FAISS, RAG

**Backend:** FastAPI, Django, GraphQL, REST APIs, WebSockets, SSE, Celery, RabbitMQ

**Frontend:** React, Next.js, TypeScript, Tailwind CSS, ShadCN

**Databases:** PostgreSQL, Redis, Elasticsearch, Vector DBs

**DevOps:** Docker, Kubernetes, Terraform, Ansible, GitHub Actions (CI/CD)

**Cloud:** GCP (Cloud Run, Cloud Storage, Container Registry)

**Monitoring:** Prometheus, Grafana, ELK Stack (Elasticsearch, Logstash, Kibana)

**Security:** OWASP, JWT, Kong API Gateway, HTTPS, CORS

**Testing:** Pytest, Jest, Load Testing

---

## Application Setup

### Backend Setup:
```bash
# From agenticAI root directory
cd backend

# Verify Python version
python --version  # Should show 3.12.3

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Initialize uv lock file and install dependencies
uv sync

# This will:
# 1. Read pyproject.toml
# 2. Create uv.lock
# 3. Create .venv directory
# 4. Install all dependencies

# Verify installation
python -c "import fastapi, langchain, langgraph; print('✓ Core packages installed')"
```

### Frontend Setup
```bash
# Check Node environment
cd frontend
node --version
npm --version

# Install Dependencies
npm install
```

### Environment Variables Setup
```bash
# Copy .env file (root folder)
cp .env.example .env
```
* 1. LLM: Get Groq or Google API key
* 2. Cloud PostgreSQL: Create database on Neon and get the PostgreSQL Connection String (else use localhost postgres)
* 3. Clound Redis: Create database on Upstash Redis (upstash.com) and get the Redis URL
* 4. Vector Database: Use Pinecone or Chromadb (Either one)
* 5. Set Backend API KEY and SECRET_KEY (as per instructions in .env.example)

---

## Run the Application

### 1. Either use Docker

* You will need Docker for this (install docker and run `docker run hello-world`)

```bash
# From root folder
docker compose up -d --build

# This starts the backend and frontend containers
```
* To stop the container, run: `docker compose down`
* To check logs, run: `docker logs -f <container_name>`

### 2. Or start services individually

```bash
# Start backend (In one terminal)
make run-api
# runs at http://localhost:8000

# Start frontend (In another terminal)
make run-web
# runs at http://localhost:3000
```

---

* For any support: mviitb25@gmail.com