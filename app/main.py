from fastapi import FastAPI

app = FastAPI(
    title="Water ATM Backend",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Water ATM Backend Running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }