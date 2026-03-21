from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
from app.core.database import db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Hello from backend"}

@app.get("/demo")
def get_data():
    return {"hi": "demo"}