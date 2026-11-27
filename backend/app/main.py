from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dependencies import system, get_system
from routers import orders, users
from schemas.order import ReserveRequest, ActivateRequest, DeleteRequest

app = FastAPI(
    title="FoodReSCU API",
    description="API for FoodReSCU leftover food ordering and reservation management.",
    version="1.0.0",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(orders.router)
app.include_router(users.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "FoodReSCU API is running"}