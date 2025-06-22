from fastapi import APIRouter, HTTPException
from app.database import execute_query
from app.models import Customer, Order
from app.config import Settings
import logging


router = APIRouter()

# Get all Orders
@router.get("/orders/", response_model=list[Order])
async def get_orders():
    query = Settings.GET_ALL_ORDERS
    return execute_query(query)

# Get Orders by CustomerID
@router.get("/orders/customer/{customer_id}/", response_model=list[Order])
async def get_customer_orders(customer_id: int):
    query = Settings.GET_ORDERS_BY_CUSTOMERID
    return execute_query(query, (customer_id,))


