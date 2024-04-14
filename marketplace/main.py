import uvicorn
from app.fastapi import create_app
from fastapi import FastAPI

app: FastAPI = create_app()

if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True)
