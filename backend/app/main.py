from fastapi import FastAPI

app = FastAPI(
    title="AgenticAI"
)

@app.get("/")
def root():
    return {"status":"chal rha hai bhai!"}

@app.get("/api/health")
def health_check():
    return {"status":"OK"}