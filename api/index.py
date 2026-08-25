from fastapi import FastAPI

from backend.main import app as citypulse_app


app = FastAPI(
    title="CityPulse Lahore API",
    version="1.0.0",
)


@app.get("/api")
def api_root():
    return {
        "service": "CityPulse Lahore API",
        "status": "online",
    }


app.mount(
    "/api",
    citypulse_app,
)