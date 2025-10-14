from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers import user_controller  # <- controller renombrado
from schemas.user_schema import UserBase  # <- schema en inglés

app = FastAPI(
    title="Granjas del Carmen API",
    description="MVC API connected to Supabase",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "🚀 Granjas del Carmen API is running correctly"}

@app.get("/users")
def list_users():
    return user_controller.list_users()

@app.get("/users/{id}")
def get_user(id: int):
    return user_controller.get_user(id)

@app.post("/users")
def create_user(user: UserBase):
    return user_controller.create_user(user)

@app.delete("/users/{id}")
def delete_user(id: int):
    return user_controller.delete_user(id)
