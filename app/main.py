from fastapi import FastAPI
from app.routes import customers, orders, tasks, reports, health

app = FastAPI(title="Smart CRM Hub API")

app.include_router(customers.router, prefix="/api", tags=["customers"])
app.include_router(orders.router, prefix="/api", tags=["orders"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(health.router, prefix="/api", tags=["health"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)