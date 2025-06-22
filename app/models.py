from pydantic import BaseModel
from datetime import date
from typing import Optional
from pydantic import BaseModel
from typing import Union

class Customer(BaseModel):
    CustomerID: int
    FirstName: str
    LastName: str
    EmailAddress: Optional[str] = None
    LeadStatus: Optional[str] = None

    class Config:
        orm_mode = True

class Order(BaseModel):
    SalesOrderID: int
    CustomerID: int
    OrderDate: date
    TotalDue: float

    class Config:
        orm_mode = True

class TaskCreate(BaseModel):
    CustomerID: int
    TaskDescription: str
    AssignedTo: str
    DueDate: date

class Task(TaskCreate):
    TaskID: int

    class Config:
        orm_mode = True

class Report(BaseModel):
    leads: int
    tasks: int

class ErrorResponse(BaseModel):
    error: str