from fastapi import FastAPI

app = FastAPI(title="Lantern")


@app.get("/health")
def health():
    return {"status": "ok"}