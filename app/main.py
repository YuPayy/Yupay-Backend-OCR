from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="OCR Service")

# register router
app.include_router(router)

@app.get("/")
def root():
    return {"message": "OCR Service is running"}
