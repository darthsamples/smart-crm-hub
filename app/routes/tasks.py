from fastapi import APIRouter, HTTPException
from app.database import execute_query, execute_command, execute_insert_get_id
from app.models import Task, TaskCreate
from app.config import Settings
import logging

router = APIRouter()

@router.get("/tasks/", response_model=list[Task])
async def get_tasks():
    query = Settings.GET_ALL_TASKS
    return execute_query(query)

@router.get("/tasks/{task_id}/", response_model=Task)
async def get_task(task_id: int):
    query = Settings.GET_TASK_BY_ID
    result = execute_query(query, (task_id,))
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result[0]

@router.post("/tasks/", response_model=Task)
async def create_task(task: TaskCreate):
    query = Settings.CREATE_TASK
    task_id = execute_insert_get_id(query, (task.CustomerID, task.TaskDescription, task.AssignedTo, task.DueDate))

    if not task_id:
        raise HTTPException(status_code=500, detail="Failed to create task")
    
    return Task(
        TaskID=task_id,
        CustomerID=task.CustomerID,
        TaskDescription=task.TaskDescription,
        AssignedTo=task.AssignedTo,
        DueDate=task.DueDate
    )

@router.put("/tasks/{task_id}/", response_model=Task)
async def update_task(task_id: int, task: TaskCreate):
    update_query = Settings.UPDATE_TASK
    affected_rows = execute_command(update_query, (task.CustomerID, task.TaskDescription, task.AssignedTo, task.DueDate, task_id))

    if affected_rows == 0:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Get the updated task
    select_query = Settings.GET_TASK_BY_ID
    result = execute_query(select_query, (task_id,))
    return Task(**result[0])


@router.delete("/tasks/{task_id}/")
async def delete_task(task_id: int):
    query = Settings.DELETE_TASK
    result = execute_command(query, (task_id,))
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}