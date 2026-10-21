from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from order import Order

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

test_orders = [
    Order(item="Burger"),
    Order(item="Pizza", time_made=datetime(2025, 11, 25, 10, 15, 0)),
]

@app.get("/orders")
async def get_products():
    return test_orders