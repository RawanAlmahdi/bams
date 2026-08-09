from fastapi import FastAPI

app = FastAPI(
    title="BAMS API",
    description="Biomedical Asset Management System Backend",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Welcome to the BAMS API"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }