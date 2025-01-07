from fastapi import FastAPI

app = FastAPI()  # This 'app' variable matches what's referenced in render.yaml

@app.get("/")
async def root():
    return {"message": "Hello World"} 