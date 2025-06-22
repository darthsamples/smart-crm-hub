from fastapi import APIRouter, HTTPException
from app.database import execute_query
from app.models import Report
from app.config import Settings
import logging

router = APIRouter()

@router.get("/report/leads/", response_model=Report)
async def get_leads_report():
    lead_query = Settings.LEAD_QUERY
    task_query = Settings.TASK_QUERY

    leads_result = execute_query(lead_query)
    tasks_result = execute_query(task_query)

    leads  = list(leads_result[0].values())[0] if leads_result else 0
    tasks =list(tasks_result[0].values())[0] if tasks_result else 0
    
    return {"leads": leads, "tasks": tasks}