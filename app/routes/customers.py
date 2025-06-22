from fastapi import APIRouter, HTTPException, Query
from app.database import execute_query, execute_command
from app.models import Customer
from app.config import Settings
import logging

router = APIRouter()

# Get all Customers
@router.get("/customers/", response_model=list[Customer])
async def get_customers():
    try:
        query = Settings.GET_ALL_CUSTOMERS
        raw_data = execute_query(query)  # Now returns list of dictionaries
        customers = [Customer(**customer_dict) for customer_dict in raw_data]
        return customers
    except Exception as e:
        logging.error(f"Error retrieving customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get Customer by CustomerID
@router.get("/customers/{customer_id}/", response_model=Customer)
async def get_customer(customer_id: int):
    query = Settings.GET_CUSTOMER_BY_ID
    result = execute_query(query, (customer_id,))
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    return Customer(**result[0])

# Update LeadStatus column in the Sales.Customer table
@router.put("/customers/{customer_id}/", response_model=Customer)
async def update_customer(customer_id: int, lead_status: str):
    update_query = Settings.UPDATE_LeadStatus
    affected_rows = execute_command(update_query, (lead_status, customer_id))
    
    if affected_rows == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get the updated customer
    select_query = Settings.GET_CUSTOMER_BY_ID
    result = execute_query(select_query, (customer_id,))
    return Customer(**result[0])
